"""The CRM backend."""

import json
import sqlite3
import uuid
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, closing
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query

from backend.database import connect, database_path, seed
from backend.documents import contents, search, sections, titles
from backend.models import (
    Case,
    CaseSummary,
    Contract,
    Decision,
    DecisionRequest,
    DocumentName,
    FailureRequest,
    FinishRequest,
    Instructions,
    Payment,
    PaymentRequest,
    PreviousCase,
    Run,
    RunRequest,
    Section,
    SectionMatch,
    SignOffRequest,
    StartRequest,
    Step,
    StepRequest,
    Todo,
    TodosRequest,
    Worker,
)
from domains import loader

ATTEMPTS = 2


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
            "attempts": row["attempts"],
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


def add_step(
    db: sqlite3.Connection, case_id: str, thread_id: str, kind: str, content: str
) -> Step:
    """Add one step of the agent's work to a case."""
    row = db.execute(
        "INSERT INTO steps (case_id, thread_id, kind, content, created_at)"
        " VALUES (?, ?, ?, ?, ?) RETURNING *",
        (case_id, thread_id, kind, content, now()),
    ).fetchone()
    return Step(**dict(row))


def find_run(db: sqlite3.Connection, run_id: str) -> Run:
    """Return one run with its to-do list, or raise a 404."""
    row = db.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
    if row is None:
        raise HTTPException(404, f"Run {run_id} not found")
    todos = db.execute(
        "SELECT content, status FROM todos WHERE run_id = ? ORDER BY position",
        (run_id,),
    ).fetchall()
    return Run(**dict(row), todos=[Todo(**dict(todo)) for todo in todos])


def running_run(db: sqlite3.Connection, run_id: str) -> Run:
    """Return a run that is still running, or raise a 404 or a 409."""
    run = find_run(db, run_id)
    if run.status != "running":
        raise HTTPException(409, f"Run {run_id} has finished")
    return run


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
    """Get the agent's instructions for running the queue and for working a case."""
    queue = loader.pack().instruction("queue")
    case = loader.pack().instruction("case")
    return Instructions(queue=queue, case=f"{case}\n{contents(db)}")


@app.get("/api/documents/search", operation_id="search_documents")
def search_documents(
    query: Annotated[str, Query(min_length=1)], db: Database
) -> list[SectionMatch]:
    """Find the sections of the wording and the manual that mention a word or phrase."""
    return search(db, query)


@app.get("/api/documents/{document}/sections/{number}", operation_id="read_section")
def read_section(document: DocumentName, number: int, db: Database) -> Section:
    """Read one section of the contract wording or the cases manual in full."""
    for section in sections(db, document):
        if section.number == number:
            return section
    title = titles(db)[document].lower()
    raise HTTPException(404, f"Section {number} of the {title} not found")


@app.get("/api/workers", operation_id="list_workers")
def list_workers(db: Database) -> list[Worker]:
    """List the cases workers."""
    rows = db.execute("SELECT * FROM workers ORDER BY worker_id").fetchall()
    return [Worker(**dict(row)) for row in rows]


@app.post("/api/cases/{case_id}/start", operation_id="start_case")
def start_case(case_id: str, request: StartRequest, db: Database) -> Case:
    """Start work on a waiting case, which moves it to in progress."""
    if find_case(db, case_id)["status"] != "waiting":
        raise HTTPException(409, f"Case {case_id} is not waiting")
    db.execute(
        "UPDATE cases SET status = 'in_progress', thread_id = ?,"
        " attempts = attempts + 1 WHERE case_id = ?",
        (request.thread_id, case_id),
    )
    return to_case(find_case(db, case_id))


@app.post("/api/cases/{case_id}/steps", operation_id="record_step")
def record_step(case_id: str, request: StepRequest, db: Database) -> Step:
    """Record one step of the agent's work on a case."""
    thread_id = find_case(db, case_id)["thread_id"]
    if thread_id is None:
        raise HTTPException(409, f"Case {case_id} has not been started")
    return add_step(db, case_id, thread_id, request.kind, request.content)


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


@app.post("/api/cases/{case_id}/failure", operation_id="fail_case")
def fail_case(case_id: str, request: FailureRequest, db: Database) -> Case:
    """Put a failed case back in the queue, or leave it for a worker after two."""
    case = find_case(db, case_id)
    if case["status"] != "in_progress":
        raise HTTPException(409, f"Case {case_id} is not in progress")
    add_step(db, case_id, case["thread_id"], "error", request.reason)
    status = "left_for_worker" if case["attempts"] >= ATTEMPTS else "waiting"
    db.execute("UPDATE cases SET status = ? WHERE case_id = ?", (status, case_id))
    return to_case(find_case(db, case_id))


@app.post("/api/runs", operation_id="start_run")
def start_run(request: RunRequest, db: Database) -> Run:
    """Start a run of the agent on the queue, with an empty to-do list."""
    run_id = str(uuid.uuid4())
    db.execute(
        "INSERT INTO runs VALUES (?, ?, 'running', ?, NULL, NULL)",
        (run_id, request.cap, now()),
    )
    return find_run(db, run_id)


@app.get("/api/runs/latest", operation_id="get_latest_run")
def get_latest_run(db: Database) -> Run | None:
    """Get the newest run with its to-do list, or nothing before the first run."""
    row = db.execute("SELECT run_id FROM runs ORDER BY rowid DESC").fetchone()
    return None if row is None else find_run(db, row["run_id"])


@app.put("/api/runs/{run_id}/todos", operation_id="write_todos")
def write_todos(run_id: str, request: TodosRequest, db: Database) -> Run:
    """Replace the to-do list of a running run."""
    running_run(db, run_id)
    db.execute("DELETE FROM todos WHERE run_id = ?", (run_id,))
    db.executemany(
        "INSERT INTO todos VALUES (?, ?, ?, ?)",
        [
            (run_id, position, todo.content, todo.status)
            for position, todo in enumerate(request.todos)
        ],
    )
    return find_run(db, run_id)


@app.post("/api/runs/{run_id}/finish", operation_id="finish_run")
def finish_run(run_id: str, request: FinishRequest, db: Database) -> Run:
    """Finish a run with the agent's summary for the workers."""
    running_run(db, run_id)
    db.execute(
        "UPDATE runs SET status = 'finished', finished_at = ?, summary = ?"
        " WHERE run_id = ?",
        (now(), request.summary, run_id),
    )
    return find_run(db, run_id)
