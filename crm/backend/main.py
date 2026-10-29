"""The CRM backend."""

import uuid
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Annotated

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query
from sqlalchemy import Connection, RowMapping, delete, insert, select, update

from backend import agent_service
from backend.database import (
    case_view,
    cases,
    contracts,
    customers,
    decisions,
    engine,
    is_seeded,
    payments,
    runs,
    seed,
    settings,
    steps,
    todos,
    workers,
)
from backend.documents import contents, search, sections, titles
from backend.models import (
    Award,
    AwardRequest,
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
    Plans,
    PreviousCase,
    Run,
    RunRequest,
    Section,
    SectionMatch,
    SignOffRequest,
    StartRequest,
    Status,
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
    """Seed the database on startup if it has no tables yet."""
    if not is_seeded(engine()):
        seed(engine())
    yield


app = FastAPI(title="CRM", lifespan=lifespan)


def database() -> Iterator[Connection]:
    """Open the database for one request, in a transaction committed at its end."""
    with engine().begin() as connection:
        yield connection


# Committed before the response is sent and before any background task runs.
Database = Annotated[Connection, Depends(database, scope="function")]


def now() -> str:
    """Return the current time in UTC, to the second."""
    return datetime.now(UTC).isoformat(timespec="seconds")


def dollars(amount: float) -> str:
    """Format an amount like $1,250.00."""
    return f"${amount:,.2f}"


def rules():
    """Return the active pack's deterministic rules module."""
    return loader.pack().rules_module()


def approval_limit(db: Connection) -> float:
    """Return the largest award that can be paid without a worker's sign-off."""
    return db.execute(select(settings.c.award_approval_limit)).scalar_one()


def plans(db: Connection) -> Plans:
    """Return the plans and add-ons, and the benefits the deductible applies to."""
    return Plans(**db.execute(select(settings.c.plans)).scalar_one())


def find_case(db: Connection, case_id: str) -> RowMapping:
    """Return one case's row, or raise a 404."""
    query = case_view.where(cases.c.case_id == case_id)
    row = db.execute(query).mappings().first()
    if row is None:
        raise HTTPException(404, f"Case {case_id} not found")
    return row


def find_contract(db: Connection, contract_id: str) -> Contract:
    """Return one contract, or raise a 404."""
    query = select(contracts.c.record).where(contracts.c.contract_id == contract_id)
    record = db.execute(query).scalar_one_or_none()
    if record is None:
        raise HTTPException(404, f"Contract {contract_id} not found")
    return Contract(**record)


def set_status(db: Connection, case_id: str, status: Status) -> None:
    """Move a case to a new status."""
    db.execute(update(cases).where(cases.c.case_id == case_id).values(status=status))


def to_summary(row: RowMapping) -> CaseSummary:
    """Build a case's line in the queue from its row."""
    return CaseSummary(
        **row["record"]
        | {
            "status": row["status"],
            "customer_name": row["customer_name"],
            "decision": row["decision"],
            "award": row["award"],
        }
    )


def to_case(row: RowMapping) -> Case:
    """Build a case in full, with its decision and payment, from its row."""
    decision = None
    if row["decision"] is not None:
        decision = Decision(**{field: row[field] for field in Decision.model_fields})
    payment = None
    if row["paid_at"] is not None:
        payment = Payment(**{field: row[field] for field in Payment.model_fields})
    return Case(
        **row["record"]
        | {
            "status": row["status"],
            "customer_name": row["customer_name"],
            "thread_id": row["thread_id"],
            "attempts": row["attempts"],
            "decision": decision,
            "payment": payment,
        }
    )


def add_step(
    db: Connection, case_id: str, thread_id: str, kind: str, content: str
) -> Step:
    """Add one step of the agent's work to a case."""
    query = (
        insert(steps)
        .values(
            case_id=case_id,
            thread_id=thread_id,
            kind=kind,
            content=content,
            created_at=now(),
        )
        .returning(steps)
    )
    return Step(**db.execute(query).mappings().one())


def find_run(db: Connection, run_id: str) -> Run:
    """Return one run with its to-do list, or raise a 404."""
    row = db.execute(select(runs).where(runs.c.run_id == run_id)).mappings().first()
    if row is None:
        raise HTTPException(404, f"Run {run_id} not found")
    query = (
        select(todos.c.content, todos.c.status)
        .where(todos.c.run_id == run_id)
        .order_by(todos.c.position)
    )
    items = [Todo(**todo) for todo in db.execute(query).mappings()]
    return Run(**row, todos=items)


def running_run(db: Connection, run_id: str) -> Run:
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
    rows = db.execute(case_view.order_by(cases.c.case_id)).mappings()
    return [to_summary(row) for row in rows]


@app.get("/api/cases/{case_id}", operation_id="get_case")
def get_case(case_id: str, db: Database) -> Case:
    """Get one case in full: the story, the items claimed and the documents."""
    return to_case(find_case(db, case_id))


@app.get("/api/contracts/{contract_id}", operation_id="get_contract")
def get_contract(contract_id: str, db: Database) -> Contract:
    """Get a contract: the plan, add-ons, purchase date, trip and travelers."""
    return find_contract(db, contract_id)


@app.get("/api/customers/{customer_id}/cases", operation_id="get_case_history")
def get_case_history(customer_id: str, db: Database) -> list[PreviousCase]:
    """Get a customer's earlier cases, with the outcome and the amount paid."""
    query = select(customers.c.record).where(customers.c.customer_id == customer_id)
    record = db.execute(query).scalar_one_or_none()
    if record is None:
        raise HTTPException(404, f"Customer {customer_id} not found")
    return [PreviousCase(**case) for case in record["previous_cases"]]


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
    rows = db.execute(select(workers).order_by(workers.c.worker_id)).mappings()
    return [Worker(**row) for row in rows]


@app.post("/api/cases/{case_id}/start", operation_id="start_case")
def start_case(case_id: str, request: StartRequest, db: Database) -> Case:
    """Start work on a waiting case, which moves it to in progress."""
    if find_case(db, case_id)["status"] != "waiting":
        raise HTTPException(409, f"Case {case_id} is not waiting")
    db.execute(
        update(cases)
        .where(cases.c.case_id == case_id)
        .values(
            status="in_progress",
            thread_id=request.thread_id,
            attempts=cases.c.attempts + 1,
        )
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
    query = select(steps).where(steps.c.case_id == case_id).order_by(steps.c.step_id)
    return [Step(**row) for row in db.execute(query).mappings()]


@app.post("/api/cases/{case_id}/decision", operation_id="record_decision")
def record_decision(case_id: str, request: DecisionRequest, db: Database) -> Case:
    """Record a case's decision once; an approval waits to be paid or signed off."""
    case = find_case(db, case_id)
    award = round(request.award, 2)
    if case["decision"] is not None:
        if (case["decision"], case["award"]) == (request.decision, award):
            return to_case(case)
        raise HTTPException(409, f"Case {case_id} has already been decided")
    if case["status"] != "in_progress":
        raise HTTPException(409, f"Case {case_id} is not in progress")
    db.execute(
        insert(decisions).values(
            case_id=case_id,
            decision=request.decision,
            award=award,
            section=request.section,
            reason=request.reason,
            decided_at=now(),
        )
    )
    if request.decision != "approve":
        set_status(db, case_id, "decided")
    elif rules().needs_sign_off(award, approval_limit(db)):
        set_status(db, case_id, "waiting_for_sign_off")
    return to_case(find_case(db, case_id))


@app.post("/api/cases/{case_id}/award", operation_id="calculate_award")
def calculate_award(case_id: str, request: AwardRequest, db: Database) -> Award:
    """Work out an approval's award with CRM's award rules; records nothing."""
    contract = find_contract(db, to_case(find_case(db, case_id)).contract_id)
    return rules().work_out_award(contract, plans(db), request, approval_limit(db))


@app.post("/api/cases/{case_id}/payment", operation_id="pay_case")
def pay_case(case_id: str, request: PaymentRequest, db: Database) -> Case:
    """Pay an approved case its award once, unless it needs a worker's sign-off."""
    case = find_case(db, case_id)
    if case["decision"] != "approve":
        raise HTTPException(409, f"Case {case_id} has not been approved")
    amount = round(request.amount, 2)
    if case["paid_at"] is not None:
        if amount == case["amount"]:
            return to_case(case)
        raise HTTPException(409, f"Case {case_id} has already been paid")
    if case["status"] == "waiting_for_sign_off":
        raise HTTPException(
            403,
            f"A award over {dollars(approval_limit(db))} needs a worker's sign-off",
        )
    if amount != case["award"]:
        raise HTTPException(
            422, f"The amount must be the approved award of {dollars(case['award'])}"
        )
    db.execute(
        insert(payments).values(case_id=case_id, amount=case["award"], paid_at=now())
    )
    set_status(db, case_id, "decided")
    return to_case(find_case(db, case_id))


@app.post("/api/cases/{case_id}/sign-off", operation_id="sign_off_case")
def sign_off_case(
    case_id: str, request: SignOffRequest, db: Database, background: BackgroundTasks
) -> Case:
    """Sign off a held award as a worker, so the agent picks the case up and pays."""
    case = find_case(db, case_id)
    if case["status"] != "waiting_for_sign_off":
        raise HTTPException(409, f"Case {case_id} is not waiting for sign-off")
    query = select(workers).where(workers.c.worker_id == request.worker_id)
    row = db.execute(query).mappings().first()
    if row is None:
        raise HTTPException(404, f"Worker {request.worker_id} not found")
    worker = Worker(**row)
    if not worker.can_approve_over_limit:
        raise HTTPException(
            403,
            f"{worker.name} can't sign off awards over {dollars(approval_limit(db))}",
        )
    db.execute(
        update(decisions)
        .where(decisions.c.case_id == case_id)
        .values(signed_off_by=worker.name, signed_off_at=now())
    )
    set_status(db, case_id, "in_progress")
    background.add_task(agent_service.resume_case, case_id)
    return to_case(find_case(db, case_id))


@app.post("/api/cases/{case_id}/failure", operation_id="fail_case")
def fail_case(case_id: str, request: FailureRequest, db: Database) -> Case:
    """Put a failed case back in the queue, or leave it for a worker after two."""
    case = find_case(db, case_id)
    if case["status"] != "in_progress":
        raise HTTPException(409, f"Case {case_id} is not in progress")
    if case["decision"] is not None:
        raise HTTPException(409, f"Case {case_id} has already been decided")
    add_step(db, case_id, case["thread_id"], "error", request.reason)
    status = "left_for_worker" if case["attempts"] >= ATTEMPTS else "waiting"
    set_status(db, case_id, status)
    return to_case(find_case(db, case_id))


@app.post("/api/runs", operation_id="start_run")
def start_run(request: RunRequest, db: Database) -> Run:
    """Start a run of the agent on the queue, with an empty to-do list."""
    run_id = str(uuid.uuid4())
    db.execute(
        insert(runs).values(
            run_id=run_id, cap=request.cap, status="running", started_at=now()
        )
    )
    return find_run(db, run_id)


@app.get("/api/runs/latest", operation_id="get_latest_run")
def get_latest_run(db: Database) -> Run | None:
    """Get the newest run with its to-do list, or nothing before the first run."""
    query = select(runs.c.run_id).order_by(runs.c.number.desc()).limit(1)
    run_id = db.execute(query).scalar_one_or_none()
    return None if run_id is None else find_run(db, run_id)


@app.put("/api/runs/{run_id}/todos", operation_id="write_todos")
def write_todos(run_id: str, request: TodosRequest, db: Database) -> Run:
    """Replace the to-do list of a running run."""
    running_run(db, run_id)
    db.execute(delete(todos).where(todos.c.run_id == run_id))
    if request.todos:
        db.execute(
            insert(todos),
            [
                {"run_id": run_id, "position": position, **todo.model_dump()}
                for position, todo in enumerate(request.todos)
            ],
        )
    return find_run(db, run_id)


@app.post("/api/runs/{run_id}/finish", operation_id="finish_run")
def finish_run(run_id: str, request: FinishRequest, db: Database) -> Run:
    """Finish a run with the agent's summary for the workers."""
    running_run(db, run_id)
    db.execute(
        update(runs)
        .where(runs.c.run_id == run_id)
        .values(status="finished", finished_at=now(), summary=request.summary)
    )
    return find_run(db, run_id)
