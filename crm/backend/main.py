"""The CRM backend."""

import json
import sqlite3
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, closing
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException

from backend.database import connect, database_path, seed
from backend.models import (
    Case,
    CaseSummary,
    Contract,
    Decision,
    DecisionRequest,
    Instructions,
    Payment,
    PaymentRequest,
    PreviousCase,
    SignOffRequest,
    StartRequest,
    Step,
    StepRequest,
    Worker,
)
from domains import loader


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Seed the database on startup if it doesn't exist yet."""
    if not database_path().exists():
        seed(database_path())
    yield


app = FastAPI(title="CRM", lifespan=lifespan)


def database() -> Iterator[sqlite3.Connection]:
    """Open the database for one request and commit if the request succeeds."""
    with closing(connect()) as connection, connection:
        yield connection


Database = Annotated[sqlite3.Connection, Depends(database)]


def now() -> str:
    """Return the current time in UTC, to the second."""
    return datetime.now(UTC).isoformat(timespec="seconds")


def dollars(amount: float) -> str:
    """Format an amount like $1,250.00."""
    return f"${amount:,.2f}"


def approval_limit(db: sqlite3.Connection) -> float:
    """Return the largest award that can be paid without a worker's sign-off."""
    return db.execute("SELECT award_approval_limit FROM settings").fetchone()[0]


def find_case(db: sqlite3.Connection, case_id: str) -> sqlite3.Row:
    """Return one case's row, or raise a 404."""
    row = db.execute("SELECT * FROM case_view WHERE case_id = ?", (case_id,)).fetchone()
    if row is None:
        raise HTTPException(404, f"Case {case_id} not found")
    return row


def to_summary(row: sqlite3.Row) -> CaseSummary:
    """Build a case's line in the queue from its row."""
    return CaseSummary(
        **json.loads(row["record"])
        | {
            "status": row["status"],
            "customer_name": row["customer_name"],
            "decision": row["decision"],
            "award": row["award"],
        }
    )


def to_case(row: sqlite3.Row) -> Case:
    """Build a case in full, with its decision and payment, from its row."""
    decision = None
    if row["decision"] is not None:
        decision = Decision(**{field: row[field] for field in Decision.model_fields})
    payment = None
    if row["paid_at"] is not None:
        payment = Payment(**{field: row[field] for field in Payment.model_fields})
    return Case(
        **json.loads(row["record"])
        | {
            "status": row["status"],
            "customer_name": row["customer_name"],
            "thread_id": row["thread_id"],
            "decision": decision,
            "payment": payment,
        }
    )


def pay(
    db: sqlite3.Connection, case_id: str, amount: float, signed_off_by: str | None
) -> Payment:
    """Record a payment on a case."""
    payment = Payment(amount=amount, paid_at=now(), signed_off_by=signed_off_by)
    db.execute(
        "INSERT INTO payments VALUES (?, ?, ?, ?)",
        (case_id, payment.amount, payment.paid_at, payment.signed_off_by),
    )
    return payment


@app.get("/api/health", operation_id="health")
def health() -> dict[str, str]:
    """Check that the backend is running."""
    return {"status": "ok"}


@app.get("/api/cases", operation_id="list_cases")
def list_cases(db: Database) -> list[CaseSummary]:
    """List every case in the queue, in id order."""
    rows = db.execute("SELECT * FROM case_view ORDER BY case_id").fetchall()
    return [to_summary(row) for row in rows]


@app.get("/api/cases/{case_id}", operation_id="get_case")
def get_case(case_id: str, db: Database) -> Case:
    """Get one case in full: the story, the items claimed and the documents."""
    return to_case(find_case(db, case_id))


@app.get("/api/contracts/{contract_id}", operation_id="get_contract")
def get_contract(contract_id: str, db: Database) -> Contract:
    """Get a contract: the plan, add-ons, purchase date, trip and travelers."""
    row = db.execute(
        "SELECT record FROM contracts WHERE contract_id = ?", (contract_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(404, f"Contract {contract_id} not found")
    return Contract(**json.loads(row["record"]))


@app.get("/api/customers/{customer_id}/cases", operation_id="get_case_history")
def get_case_history(customer_id: str, db: Database) -> list[PreviousCase]:
    """Get a customer's earlier cases, with the outcome and the amount paid."""
    row = db.execute(
        "SELECT record FROM customers WHERE customer_id = ?", (customer_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(404, f"Customer {customer_id} not found")
    return [
        PreviousCase(**case) for case in json.loads(row["record"])["previous_cases"]
    ]


@app.get("/api/instructions", operation_id="get_instructions")
def get_instructions(db: Database) -> Instructions:
    """Get the agent's instructions, followed by the contract wording."""
    wording = db.execute("SELECT wording FROM settings").fetchone()[0]
    text = loader.pack().instruction("case")
    return Instructions(text=f"{text}\n{wording}")


@app.get("/api/workers", operation_id="list_workers")
def list_workers(db: Database) -> list[Worker]:
    """List the case workers."""
    rows = db.execute("SELECT * FROM workers ORDER BY worker_id").fetchall()
    return [Worker(**dict(row)) for row in rows]


@app.post("/api/cases/{case_id}/start", operation_id="start_case")
def start_case(case_id: str, request: StartRequest, db: Database) -> Case:
    """Start work on a waiting case, which moves it to in progress."""
    if find_case(db, case_id)["status"] != "waiting":
        raise HTTPException(409, f"Case {case_id} is not waiting")
    db.execute(
        "UPDATE cases SET status = 'in_progress', thread_id = ? WHERE case_id = ?",
        (request.thread_id, case_id),
    )
    return to_case(find_case(db, case_id))


@app.post("/api/cases/{case_id}/steps", operation_id="record_step")
def record_step(case_id: str, request: StepRequest, db: Database) -> Step:
    """Record one step of the agent's work on a case."""
    thread_id = find_case(db, case_id)["thread_id"]
    if thread_id is None:
        raise HTTPException(409, f"Case {case_id} has not been started")
    row = db.execute(
        "INSERT INTO steps (case_id, thread_id, kind, content, created_at)"
        " VALUES (?, ?, ?, ?, ?) RETURNING *",
        (case_id, thread_id, request.kind, request.content, now()),
    ).fetchone()
    return Step(**dict(row))


@app.get("/api/cases/{case_id}/steps", operation_id="list_steps")
def list_steps(case_id: str, db: Database) -> list[Step]:
    """List the steps of the agent's work on a case, in order."""
    find_case(db, case_id)
    rows = db.execute(
        "SELECT * FROM steps WHERE case_id = ? ORDER BY step_id", (case_id,)
    ).fetchall()
    return [Step(**dict(row)) for row in rows]


@app.post("/api/cases/{case_id}/decision", operation_id="record_decision")
def record_decision(case_id: str, request: DecisionRequest, db: Database) -> Case:
    """Record the decision on a case; an approval over the limit waits for sign-off."""
    if find_case(db, case_id)["status"] != "in_progress":
        raise HTTPException(409, f"Case {case_id} is not in progress")
    award = round(request.award, 2)
    held = request.decision == "approve" and award > approval_limit(db)
    db.execute(
        "INSERT INTO decisions VALUES (?, ?, ?, ?, ?, ?)",
        (case_id, request.decision, award, request.section, request.reason, now()),
    )
    db.execute(
        "UPDATE cases SET status = ? WHERE case_id = ?",
        ("waiting_for_sign_off" if held else "decided", case_id),
    )
    return to_case(find_case(db, case_id))


@app.post("/api/cases/{case_id}/payment", operation_id="pay_case")
def pay_case(case_id: str, request: PaymentRequest, db: Database) -> Payment:
    """Pay an approved case its award, unless it needs a worker's sign-off."""
    case = find_case(db, case_id)
    if case["decision"] != "approve":
        raise HTTPException(409, f"Case {case_id} has not been approved")
    if case["paid_at"] is not None:
        raise HTTPException(409, f"Case {case_id} has already been paid")
    if case["status"] == "waiting_for_sign_off":
        raise HTTPException(
            403,
            f"An award over {dollars(approval_limit(db))} needs a worker's sign-off",
        )
    if round(request.amount, 2) != case["award"]:
        raise HTTPException(
            422, f"The amount must be the approved award of {dollars(case['award'])}"
        )
    return pay(db, case_id, case["award"], None)


@app.post("/api/cases/{case_id}/sign-off", operation_id="sign_off_case")
def sign_off_case(case_id: str, request: SignOffRequest, db: Database) -> Case:
    """Sign off a held award as a worker, which pays it and decides the case."""
    case = find_case(db, case_id)
    if case["status"] != "waiting_for_sign_off":
        raise HTTPException(409, f"Case {case_id} is not waiting for sign-off")
    row = db.execute(
        "SELECT * FROM workers WHERE worker_id = ?", (request.worker_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(404, f"Worker {request.worker_id} not found")
    worker = Worker(**dict(row))
    if not worker.can_approve_over_limit:
        raise HTTPException(
            403,
            f"{worker.name} can't sign off awards over {dollars(approval_limit(db))}",
        )
    pay(db, case_id, case["award"], worker.name)
    db.execute("UPDATE cases SET status = 'decided' WHERE case_id = ?", (case_id,))
    return to_case(find_case(db, case_id))
