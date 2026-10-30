"""The CRM backend."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException
from mangum import Mangum
from sqlalchemy import Connection, RowMapping, insert, select, update

from backend import agent_api, dashboard
from backend.calculation import attempts_calculation, keep_calculation
from backend.configuration import router as configuration
from domains import loader
from backend.database import (
    case_view,
    cases,
    customers,
    decisions,
    engine,
    is_seeded,
    model_calls,
    now,
    payments,
    award_rules,
    contracts,
    seed,
    stamp,
    steps,
    work_times,
)
from backend.dependencies import (
    AgentKey,
    Database,
    WorkerOrAgent,
    SignedIn,
    SignedInWorker,
    senior,
)
from backend.documents import manual_version
from backend.improvement import router as improvement
from backend.lookups import CASE_NOT_FOUND, current_settings, run_row
from backend.models import (
    Case,
    CaseSummary,
    DecisionKind,
    DecisionRequest,
    FailureRequest,
    Worker,
    HoldRequest,
    ModelCall,
    ModelCallRequest,
    PaymentRequest,
    Award,
    AwardRequest,
    Plans,
    Contract,
    PreviousCase,
    StartRequest,
    Status,
    Step,
    StepRequest,
    WorkTime,
    WorkTimeRequest,
)
from backend.money import dollars
from backend.records import check_calculation, check_request
from backend.round_state import round_row, why_no_case_starts
from backend.runs import router as runs
from backend.views import to_case, to_summary

ATTEMPTS = 2
NOT_APPROVED = "Case {case_id} has not been approved"
ALREADY_PAID = "Case {case_id} has already been paid"
NOT_STARTED = "Case {case_id} has not been started"
NOT_IN_PROGRESS = "Case {case_id} is not in progress"
ALREADY_DECIDED = "Case {case_id} has already been decided"


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


def over_the_limit(limit: float) -> str:
    """Say that a award over a limit needs a worker's sign-off."""
    return f"An award over {dollars(limit)} needs a worker's sign-off"


def record_payment(db: Connection, case: RowMapping) -> None:
    """Pay an approved case its award, which decides it."""
    case_id = case["case_id"]
    db.execute(
        insert(payments).values(
            case_id=case_id, amount=case["award"], paid_at=now()
        )
    )
    set_status(db, case_id, Status.DECIDED)


def set_status(db: Connection, case_id: str, status: Status) -> None:
    """Move a case to a new status."""
    db.execute(
        update(cases).where(cases.c.case_id == case_id).values(status=status)
    )


def started_thread(db: Connection, case_id: str) -> str:
    """Return the thread of a case that has been started, or raise a 404 or a 409."""
    thread_id = find_case(db, case_id)["thread_id"]
    if thread_id is None:
        raise HTTPException(409, NOT_STARTED.format(case_id=case_id))
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


def add_step(db: Connection, case_id: str, thread_id: str, step: StepRequest) -> Step:
    """Add one step of the agent's work to a case."""
    query = (
        insert(steps)
        .values(
            case_id=case_id,
            thread_id=thread_id,
            **step.model_dump(),
            created_at=now(),
        )
        .returning(steps)
    )
    return Step(**db.execute(query).mappings().one())


@app.get("/api/health", operation_id="health")
def health() -> dict[str, str]:
    """Check that the backend is running."""
    return {"status": "ok"}


@app.get("/api/cases", operation_id="list_cases", dependencies=[WorkerOrAgent])
def list_cases(db: Database) -> list[CaseSummary]:
    """List every case in the queue, in id order, leaving out evaluations' copies."""
    query = case_view.where(cases.c.evaluation_id.is_(None))
    rows = db.execute(query.order_by(cases.c.case_id)).mappings()
    return [to_summary(row) for row in rows]


@app.get(
    "/api/cases/{case_id}", operation_id="get_case", dependencies=[WorkerOrAgent]
)
def get_case(case_id: str, db: Database) -> Case:
    """Get one case in full: the story, the items claimed and the documents."""
    return to_case(find_case(db, case_id))


@app.get(
    "/api/contracts/{contract_id}",
    operation_id="get_contract",
    dependencies=[WorkerOrAgent],
)
def get_contract(contract_id: str, db: Database) -> Contract:
    """Get a contract: the plan, add-ons, purchase date, trip and travelers."""
    return find_contract(db, contract_id)


@app.get(
    "/api/customers/{customer_id}/cases",
    operation_id="get_case_history",
    dependencies=[WorkerOrAgent],
)
def get_case_history(customer_id: str, db: Database) -> list[PreviousCase]:
    """Get a customer's earlier cases, with the outcome and the amount paid."""
    query = select(customers.c.record).where(customers.c.customer_id == customer_id)
    record = db.execute(query).scalar_one_or_none()
    if record is None:
        raise HTTPException(404, f"Customer {customer_id} not found")
    return [PreviousCase(**case) for case in record["previous_cases"]]


@app.get(
    "/api/agent/openapi.json",
    operation_id="get_agent_api",
    dependencies=[WorkerOrAgent],
)
def get_agent_api() -> dict[str, Any]:
    """Get the OpenAPI document of the case agent's own operations, for the Gateway."""
    return agent_api.document(app)


@app.get("/api/me", operation_id="get_signed_in_worker")
def get_signed_in_worker(worker: SignedIn) -> Worker:
    """Get the worker signed in, with what they may sign off."""
    return worker


@app.post(
    "/api/cases/{case_id}/start", operation_id="start_case", dependencies=[AgentKey]
)
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


@app.post(
    "/api/cases/{case_id}/steps", operation_id="record_step", dependencies=[AgentKey]
)
def record_step(case_id: str, request: StepRequest, db: Database) -> Step:
    """Record one step of the agent's work on a case."""
    thread_id = started_thread(db, case_id)
    return add_step(db, case_id, thread_id, request)


@app.post(
    "/api/cases/{case_id}/model-calls",
    operation_id="record_model_call",
    dependencies=[AgentKey],
)
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


@app.post(
    "/api/cases/{case_id}/work-times",
    operation_id="record_work_time",
    dependencies=[AgentKey],
)
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


@app.get(
    "/api/cases/{case_id}/steps",
    operation_id="list_steps",
    dependencies=[SignedInWorker],
)
def list_steps(case_id: str, db: Database) -> list[Step]:
    """List the steps of the agent's work on a case, in order."""
    find_case(db, case_id)
    query = select(steps).where(steps.c.case_id == case_id).order_by(steps.c.step_id)
    return [Step(**row) for row in db.execute(query).mappings()]


@app.post(
    "/api/cases/{case_id}/decision",
    operation_id="record_decision",
    dependencies=[AgentKey],
)
def record_decision(case_id: str, request: DecisionRequest, db: Database) -> Case:
    """Record a case's decision once, as section 14 asks; approvals await payment."""
    check_request(request)
    case = find_case(db, case_id)
    award = request.award
    if case["decision"] is not None:
        if (case["decision"], case["award"]) == (request.decision, award):
            return to_case(case)
        raise HTTPException(409, ALREADY_DECIDED.format(case_id=case_id))
    if case["status"] != Status.IN_PROGRESS:
        raise HTTPException(409, NOT_IN_PROGRESS.format(case_id=case_id))
    calculation = None
    if request.decision == DecisionKind.APPROVE:
        calculation = check_calculation(award, attempts_calculation(db, case))
    limit = approval_limit(db)
    db.execute(
        insert(decisions).values(
            case_id=case_id,
            decision=request.decision,
            award=award,
            section=request.section,
            reason=request.reason,
            decided_by=request.decided_by,
            decided_at=now(),
            manual_version=manual_version(db),
            calculation=calculation and calculation.model_dump(),
            approval_limit=limit,
        )
    )
    if request.decision != DecisionKind.APPROVE:
        set_status(db, case_id, Status.DECIDED)
    elif rules().needs_sign_off(award, limit):
        set_status(db, case_id, Status.WAITING_FOR_SIGN_OFF)
    return to_case(find_case(db, case_id))


@app.post(
    "/api/cases/{case_id}/award",
    operation_id="calculate_award",
    dependencies=[AgentKey],
)
def calculate_award(case_id: str, request: AwardRequest, db: Database) -> Award:
    """Work out and keep an approval's award with CRM's award rules."""
    case = to_case(find_case(db, case_id))
    if case.thread_id is None:
        raise HTTPException(409, NOT_STARTED.format(case_id=case_id))
    if case.status != Status.IN_PROGRESS:
        raise HTTPException(409, NOT_IN_PROGRESS.format(case_id=case_id))
    contract = find_contract(db, case.contract_id)
    award = rules().work_out_award(
        contract, plans(db), request, approval_limit(db)
    )
    keep_calculation(db, case_id, case.thread_id, award)
    return award


@app.post(
    "/api/cases/{case_id}/payment", operation_id="pay_case", dependencies=[AgentKey]
)
def pay_case(case_id: str, request: PaymentRequest, db: Database) -> Case:
    """Pay an approved case its award once, unless it is over the limit."""
    amount = round(request.amount, 2)
    limit = approval_limit(db)
    if rules().needs_sign_off(amount, limit):
        raise HTTPException(403, over_the_limit(limit))
    case = find_case(db, case_id)
    if case["decision"] != DecisionKind.APPROVE:
        raise HTTPException(409, NOT_APPROVED.format(case_id=case_id))
    if case["paid_at"] is not None:
        if amount == case["amount"]:
            return to_case(case)
        raise HTTPException(409, ALREADY_PAID.format(case_id=case_id))
    if case["status"] == Status.WAITING_FOR_SIGN_OFF:
        raise HTTPException(403, over_the_limit(case["approval_limit"]))
    if amount != case["award"]:
        raise HTTPException(
            422, f"The amount must be the approved award of {dollars(case['award'])}"
        )
    record_payment(db, case)
    return to_case(find_case(db, case_id))


@app.post(
    "/api/cases/{case_id}/hold", operation_id="hold_payment", dependencies=[AgentKey]
)
def hold_payment(case_id: str, request: HoldRequest, db: Database) -> Case:
    """Hold an approval the Gateway refused to pay for a worker's sign-off."""
    case = find_case(db, case_id)
    if case["decision"] != DecisionKind.APPROVE:
        raise HTTPException(409, NOT_APPROVED.format(case_id=case_id))
    if case["paid_at"] is not None:
        raise HTTPException(409, ALREADY_PAID.format(case_id=case_id))
    if case["status"] == Status.WAITING_FOR_SIGN_OFF:
        return to_case(case)
    db.execute(
        update(decisions)
        .where(decisions.c.case_id == case_id)
        .values(gateway_refusal=request.reason)
    )
    set_status(db, case_id, Status.WAITING_FOR_SIGN_OFF)
    return to_case(find_case(db, case_id))


@app.post("/api/cases/{case_id}/sign-off", operation_id="sign_off_case")
def sign_off_case(case_id: str, worker: SignsOffOverTheLimit, db: Database) -> Case:
    """Sign off a held award as the worker signed in, which pays it."""
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
    record_payment(db, case)
    return to_case(find_case(db, case_id))


@app.post(
    "/api/cases/{case_id}/failure", operation_id="fail_case", dependencies=[AgentKey]
)
def fail_case(case_id: str, request: FailureRequest, db: Database) -> Case:
    """Put a failed case back in the queue, or leave it for a worker after two."""
    case = find_case(db, case_id)
    if case["status"] != Status.IN_PROGRESS:
        raise HTTPException(409, NOT_IN_PROGRESS.format(case_id=case_id))
    if case["decision"] is not None:
        raise HTTPException(409, ALREADY_DECIDED.format(case_id=case_id))
    error = StepRequest(kind="error", content=request.reason, sources=[])
    add_step(db, case_id, case["thread_id"], error)
    status = (
        Status.LEFT_FOR_WORKER if case["attempts"] >= ATTEMPTS else Status.WAITING
    )
    set_status(db, case_id, status)
    return to_case(find_case(db, case_id))


# After every route, so the dashboard's build only answers what no route does.
app.router.routes.append(dashboard.mount)

# AWS Lambda's entry point. Nothing seeds the database there.
worker = Mangum(app, lifespan="off")
