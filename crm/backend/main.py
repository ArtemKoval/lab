"""The CRM backend."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query
from sqlalchemy import Connection, RowMapping, insert, select, update

from backend import agent_service
from backend.configuration import router as configuration
from backend.database import (
    award_rules,
    case_view,
    cases,
    contracts,
    customers,
    decisions,
    engine,
    is_seeded,
    model_calls,
    now,
    payments,
    seed,
    stamp,
    steps,
    work_times,
)
from backend.dependencies import Database, SignedIn, senior
from backend.documents import search, sections, titles
from backend.improvement import router as improvement
from backend.lookups import CASE_NOT_FOUND, current_settings, run_row
from backend.models import (
    Award,
    AwardRequest,
    Case,
    CaseSummary,
    Contract,
    DecisionKind,
    DecisionRequest,
    DocumentName,
    FailureRequest,
    ModelCall,
    ModelCallRequest,
    PaymentRequest,
    Plans,
    PreviousCase,
    Section,
    SectionMatch,
    StartRequest,
    Status,
    Step,
    StepRequest,
    Worker,
    WorkTime,
    WorkTimeRequest,
)
from backend.money import dollars
from backend.round_state import round_row, why_no_case_starts
from backend.runs import router as runs
from backend.views import to_case, to_summary
from domains import loader

ATTEMPTS = 2


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Seed the database on startup if it has no tables yet."""
    if not is_seeded(engine()):
        seed(engine())
    yield


app = FastAPI(title="CRM", lifespan=lifespan)
app.include_router(runs)
app.include_router(configuration)
app.include_router(improvement)

SignsOffOverTheLimit = Annotated[Worker, Depends(senior("sign this off"))]


def rules():
    """Return the active pack's deterministic rules module."""
    return loader.pack().rules_module()


def approval_limit(db: Connection) -> float:
    """Return the largest award that can be paid without a worker's sign-off, as
    the settings in force have it."""
    return current_settings(db).approval_limit


def plans(db: Connection) -> Plans:
    """Return the plans and add-ons, and the benefits the deductible applies to."""
    return Plans(**db.execute(select(award_rules.c.plans)).scalar_one())


def find_case(db: Connection, case_id: str) -> RowMapping:
    """Return one case's row, or raise a 404."""
    query = case_view.where(cases.c.case_id == case_id)
    row = db.execute(query).mappings().first()
    if row is None:
        raise HTTPException(404, CASE_NOT_FOUND.format(case_id=case_id))
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


def started_thread(db: Connection, case_id: str) -> str:
    """Return the thread of a case that has been started, or raise a 404 or a 409."""
    thread_id = find_case(db, case_id)["thread_id"]
    if thread_id is None:
        raise HTTPException(409, f"Case {case_id} has not been started")
    return thread_id


def refuse_a_round_that_cant_go_on(db: Connection, run_id: str) -> None:
    """Raise a 409 when an evaluation belongs to a round that was stopped or has
    spent its limit, so no new case starts in it."""
    round_id = run_row(db, run_id)["round_id"]
    if round_id is None:
        return
    reason = why_no_case_starts(db, round_row(db, round_id))
    if reason:
        raise HTTPException(409, reason)


def check_run(db: Connection, run_id: str | None) -> None:
    """Check that the run named, if any, exists, or raise a 404."""
    if run_id is not None:
        run_row(db, run_id)


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


@app.get("/api/health", operation_id="health")
def health() -> dict[str, str]:
    """Check that the backend is running."""
    return {"status": "ok"}


@app.get("/api/cases", operation_id="list_cases")
def list_cases(db: Database) -> list[CaseSummary]:
    """List every case in the queue, in id order, leaving out evaluations' copies."""
    query = case_view.where(cases.c.evaluation_id.is_(None))
    rows = db.execute(query.order_by(cases.c.case_id)).mappings()
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


@app.get("/api/me", operation_id="get_signed_in_worker")
def get_signed_in_worker(worker: SignedIn) -> Worker:
    """Get the worker signed in, with what they may sign off."""
    return worker


@app.post("/api/cases/{case_id}/start", operation_id="start_case")
def start_case(case_id: str, request: StartRequest, db: Database) -> Case:
    """Start work on a waiting case, which moves it to in progress."""
    case = find_case(db, case_id)
    if case["status"] != Status.WAITING:
        raise HTTPException(409, f"Case {case_id} is not waiting")
    if case["evaluation_id"]:
        refuse_a_round_that_cant_go_on(db, case["evaluation_id"])
    db.execute(
        update(cases)
        .where(cases.c.case_id == case_id)
        .values(
            status=Status.IN_PROGRESS,
            thread_id=request.thread_id,
            attempts=cases.c.attempts + 1,
        )
    )
    return to_case(find_case(db, case_id))


@app.post("/api/cases/{case_id}/steps", operation_id="record_step")
def record_step(case_id: str, request: StepRequest, db: Database) -> Step:
    """Record one step of the agent's work on a case."""
    thread_id = started_thread(db, case_id)
    return add_step(db, case_id, thread_id, request.kind, request.content)


@app.post("/api/cases/{case_id}/model-calls", operation_id="record_model_call")
def record_model_call(
    case_id: str, request: ModelCallRequest, db: Database
) -> ModelCall:
    """Record the tokens and the cost of one model call on a started case."""
    thread_id = started_thread(db, case_id)
    check_run(db, request.run_id)
    query = (
        insert(model_calls)
        .values(
            case_id=case_id,
            thread_id=thread_id,
            **request.model_dump(),
            created_at=now(),
        )
        .returning(model_calls)
    )
    return ModelCall(**db.execute(query).mappings().one())


@app.post("/api/cases/{case_id}/work-times", operation_id="record_work_time")
def record_work_time(case_id: str, request: WorkTimeRequest, db: Database) -> WorkTime:
    """Record one spell of the agent's work on a started case, ending now."""
    thread_id = started_thread(db, case_id)
    check_run(db, request.run_id)
    started = datetime.now(UTC) - timedelta(seconds=request.seconds)
    query = (
        insert(work_times)
        .values(
            case_id=case_id,
            thread_id=thread_id,
            run_id=request.run_id,
            started_at=stamp(started),
            seconds=request.seconds,
        )
        .returning(work_times)
    )
    return WorkTime(**db.execute(query).mappings().one())


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
    if case["status"] != Status.IN_PROGRESS:
        raise HTTPException(409, f"Case {case_id} is not in progress")
    limit = approval_limit(db)
    db.execute(
        insert(decisions).values(
            case_id=case_id,
            decision=request.decision,
            award=award,
            section=request.section,
            reason=request.reason,
            decided_at=now(),
            approval_limit=limit,
        )
    )
    if request.decision != DecisionKind.APPROVE:
        set_status(db, case_id, Status.DECIDED)
    elif rules().needs_sign_off(award, limit):
        set_status(db, case_id, Status.WAITING_FOR_SIGN_OFF)
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
    if case["decision"] != DecisionKind.APPROVE:
        raise HTTPException(409, f"Case {case_id} has not been approved")
    amount = round(request.amount, 2)
    if case["paid_at"] is not None:
        if amount == case["amount"]:
            return to_case(case)
        raise HTTPException(409, f"Case {case_id} has already been paid")
    if case["status"] == Status.WAITING_FOR_SIGN_OFF:
        raise HTTPException(
            403,
            f"An award over {dollars(case['approval_limit'])} needs a worker's "
            "sign-off",
        )
    if amount != case["award"]:
        raise HTTPException(
            422, f"The amount must be the approved award of {dollars(case['award'])}"
        )
    db.execute(
        insert(payments).values(case_id=case_id, amount=case["award"], paid_at=now())
    )
    set_status(db, case_id, Status.DECIDED)
    return to_case(find_case(db, case_id))


@app.post("/api/cases/{case_id}/sign-off", operation_id="sign_off_case")
def sign_off_case(
    case_id: str,
    worker: SignsOffOverTheLimit,
    db: Database,
    background: BackgroundTasks,
) -> Case:
    """Sign off a held award as the worker signed in, so the agent pays it."""
    case = find_case(db, case_id)
    if case["evaluation_id"] is not None:
        raise HTTPException(
            409, f"Case {case_id} is a copy in an evaluation and can't be signed off"
        )
    if case["status"] != Status.WAITING_FOR_SIGN_OFF:
        raise HTTPException(409, f"Case {case_id} is not waiting for sign-off")
    db.execute(
        update(decisions)
        .where(decisions.c.case_id == case_id)
        .values(signed_off_by=worker.name, signed_off_at=now())
    )
    set_status(db, case_id, Status.IN_PROGRESS)
    background.add_task(agent_service.resume_case, case_id)
    return to_case(find_case(db, case_id))


@app.post("/api/cases/{case_id}/failure", operation_id="fail_case")
def fail_case(case_id: str, request: FailureRequest, db: Database) -> Case:
    """Put a failed case back in the queue, or leave it for a worker after two."""
    case = find_case(db, case_id)
    if case["status"] != Status.IN_PROGRESS:
        raise HTTPException(409, f"Case {case_id} is not in progress")
    if case["decision"] is not None:
        raise HTTPException(409, f"Case {case_id} has already been decided")
    add_step(db, case_id, case["thread_id"], "error", request.reason)
    status = Status.LEFT_FOR_WORKER if case["attempts"] >= ATTEMPTS else Status.WAITING
    set_status(db, case_id, status)
    return to_case(find_case(db, case_id))
