"""The CRM backend."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException
from mangum import Mangum
from sqlalchemy import (
    Connection,
    RowMapping,
    delete,
    func,
    insert,
    or_,
    select,
    update,
)

from backend import agent_api, agent_service, context_files, dashboard
from backend.configuration import router as configuration
from backend.copilot import router as copilot
from backend.customers import router as customers_router
from backend.database import (
    case_view,
    cases,
    contracts,
    decisions,
    effect_runs,
    engine,
    is_seeded,
    model_calls,
    now,
    outcomes,
    seed,
    stamp,
    steps,
    work_times,
)
from backend.dependencies import (
    AgentKey,
    Database,
    SignedIn,
    SignedInWorker,
    WorkerOrAgent,
    senior,
)
from backend.documents import manual_version
from backend.improvement import router as improvement
from backend.lookups import (
    A_COPY,
    CASE_NOT_FOUND,
    NOT_WAITING_FOR_SIGN_OFF,
    current_settings,
    customer_record,
    find_case,
    run_row,
)
from backend.models import (
    Award,
    AwardRequest,
    Case,
    CaseSummary,
    Contract,
    DecisionKind,
    DecisionRequest,
    EffectRun,
    FailureRequest,
    HoldRequest,
    ModelCall,
    ModelCallRequest,
    NewStep,
    PackView,
    Plans,
    PreviousCase,
    SendBackRequest,
    SignOffs,
    StartRequest,
    Status,
    Step,
    StepRequest,
    TakeRequest,
    Worker,
    WorkTime,
    WorkTimeRequest,
)
from backend.money import dollars
from backend.records import NOTHING_RESOLVED, check_request, falls_short
from backend.round_state import round_row, why_no_case_starts
from backend.runs import router as runs
from backend.sent_back import keep, sent_back_of
from backend.views import to_case, to_summary
from domains import loader

ATTEMPTS = 2
NOT_APPROVED = "Case {case_id} has not been approved"
ALREADY_PAID = "Case {case_id} has already been paid"
NOT_STARTED = "Case {case_id} has not been started"
NOT_IN_PROGRESS = "Case {case_id} is not in progress"
ALREADY_RAN = "Case {case_id} already ran the effect {effect!r}"
ALREADY_DECIDED = "Case {case_id} has already been decided"
NOT_WAITING = "Case {case_id} is not waiting"
NOT_SENT_BACK = "Case {case_id} isn't sent back"

log = logging.getLogger(__name__)


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
app.include_router(copilot)
app.include_router(customers_router)

SignsOffOverTheLimit = Annotated[Worker, Depends(senior("sign this off"))]
SendsBack = Annotated[Worker, Depends(senior("send this back"))]


def rules():
    """Return the active pack's deterministic rules module."""
    return loader.pack().rules_module()


def protocol():
    """Return the active pack's protocol module, with its four verbs."""
    return loader.pack().protocol_module()


def outcome_kind() -> str:
    """Return the outcome kind the pack declares, which the engine's routes
    carry under its own name."""
    return next(iter(loader.pack().outcomes), "award")


def approval_limit(db: Connection) -> float:
    """Return the largest award that can be paid without a worker's sign-off, as
    the settings in force have it."""
    return current_settings(db).approval_limit


def plans() -> Plans:
    """Return the plans and add-ons, and the benefits the deductible applies
    to, from the pack's context layer."""
    return Plans(**context_files.plans())


def case_in_full(db: Connection, case_id: str) -> Case:
    """Return one case in full, as the API shows it, or raise a 404."""
    run = db.execute(
        select(effect_runs)
        .where(effect_runs.c.case_id == case_id)
        .order_by(effect_runs.c.effect_run_id.desc())
        .limit(1)
    ).mappings().first()
    effect = EffectRun(**run) if run is not None else None
    return to_case(find_case(db, case_id), sent_back_of(db, case_id), effect)


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


def keep_outcome(
    db: Connection, case: RowMapping, outcome: str, payload: dict
) -> None:
    """Store one resolved outcome's payload for the attempt in flight, over
    any earlier one."""
    db.execute(
        delete(outcomes).where(
            outcomes.c.case_id == case["case_id"], outcomes.c.outcome == outcome
        )
    )
    db.execute(
        insert(outcomes).values(
            case_id=case["case_id"],
            outcome=outcome,
            thread_id=case["thread_id"],
            payload=payload,
            resolved_at=now(),
        )
    )


def stored_payload(
    db: Connection, case: RowMapping, outcome: str
) -> dict | None:
    """Return the outcome payload resolved on the case's current attempt, or
    nothing. The engine moves it opaque, and never reads inside it."""
    return db.execute(
        select(outcomes.c.payload).where(
            outcomes.c.case_id == case["case_id"],
            outcomes.c.outcome == outcome,
            outcomes.c.thread_id == case["thread_id"],
        )
    ).scalar_one_or_none()


def gated(db: Connection, payload: dict, limit: float) -> bool:
    """Ask the pack's gate whether an outcome is held for a worker's
    sign-off, under the limit in force."""
    try:
        return protocol().gate(payload, {"approval_limit": limit})
    except (KeyError, TypeError, ValueError) as error:
        raise HTTPException(
            422, f"The outcome payload does not fit the pack's gate: {error}"
        ) from error


def run_the_effect(db: Connection, case: RowMapping, effect: str) -> dict:
    """Execute one of a case's declared effects once, and record the run with
    the pack's summary of its outcome. The record comes from the pack's
    execute verb on the outcome the case decided on."""
    payload = stored_payload(db, case, effect)
    record = protocol().execute(dict(case), payload)
    db.execute(
        insert(effect_runs).values(
            case_id=case["case_id"],
            effect=effect,
            result=record,
            summary=protocol().summarize(payload),
            ran_at=now(),
        )
    )
    set_status(db, case["case_id"], Status.DECIDED)
    return record


def set_status(db: Connection, case_id: str, status: Status) -> None:
    """Move a case to a new status."""
    db.execute(update(cases).where(cases.c.case_id == case_id).values(status=status))


def move_case(
    db: Connection, case_id: str, old: Status, new: Status, **columns: Any
) -> bool:
    """Move a case from one status to another, setting any other columns given, and
    say whether it moved: only the first of two requests at the same moment finds
    it in the old status."""
    moved = db.execute(
        update(cases)
        .where(cases.c.case_id == case_id, cases.c.status == old)
        .values(status=new, **columns)
    )
    return moved.rowcount == 1


def answer_held(
    db: Connection, case_id: str, answer: Status, answered: str
) -> RowMapping:
    """Move a case held for sign-off on with a worker's answer, and return its row
    as the move found it, with the decision that was held, or raise a 404, or a 409
    for an evaluation's copy, which nobody answers, or for a case no longer
    waiting, as when another answer came first."""
    if find_case(db, case_id)["evaluation_id"] is not None:
        raise HTTPException(409, A_COPY.format(case_id=case_id, answered=answered))
    if not move_case(db, case_id, Status.WAITING_FOR_SIGN_OFF, answer):
        raise HTTPException(409, NOT_WAITING_FOR_SIGN_OFF.format(case_id=case_id))
    return find_case(db, case_id)


def record_send_back(db: Connection, case: RowMapping, note: str, by: str) -> None:
    """Keep a held decision sent back with its note, clear it from the case with
    its resolved outcome, so nothing runs for it, and record the note as a step."""
    keep(db, case, note, by)
    db.execute(delete(decisions).where(decisions.c.case_id == case["case_id"]))
    db.execute(delete(outcomes).where(outcomes.c.case_id == case["case_id"]))
    step = NewStep(kind="sent_back", content=f"Sent back by {by}: {note}", sources=[])
    add_step(db, case["case_id"], case["thread_id"], step)


def ask_to_resume(case_id: str) -> None:
    """Ask the agent to resume a case after a worker's answer, which stands
    whatever happens to the call: a failure is logged as a warning."""
    try:
        agent_service.resume_case(case_id)
    except Exception as error:  # the worker's answer stands whatever happens
        log.warning("%s wasn't resumed: %s", case_id, error)


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


def add_step(db: Connection, case_id: str, thread_id: str, step: NewStep) -> Step:
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


@app.get("/api/pack", operation_id="get_pack", dependencies=[WorkerOrAgent])
def get_pack() -> PackView:
    """Serve the active pack's declarations for the tools and the dashboard."""
    declared = loader.pack()
    return PackView(
        name=declared.name,
        display_name=declared.manifest.get("display_name", declared.name),
        resolutions=declared.resolutions,
        outcomes=declared.outcomes,
        config=declared.config,
        effects=declared.effects,
    )


@app.get("/api/cases/{case_id}", operation_id="get_case", dependencies=[WorkerOrAgent])
def get_case(case_id: str, db: Database) -> Case:
    """Get one case in full: the story, the items claimed and the documents."""
    return case_in_full(db, case_id)


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
    record = customer_record(db, customer_id)
    return [PreviousCase(**case) for case in record["previous_cases"]]


@app.get(
    "/api/agent/openapi.json",
    operation_id="get_agent_api",
    dependencies=[WorkerOrAgent],
)
def get_agent_api() -> dict[str, Any]:
    """Get the OpenAPI document of the case agent's own operations, for the Gateway."""
    return agent_api.document(app)


@app.get(
    "/api/sign-offs", operation_id="count_sign_offs", dependencies=[SignedInWorker]
)
def count_sign_offs(db: Database) -> SignOffs:
    """Count the queue's approvals held for a sign-off, and those signed off."""
    held = cases.c.status == Status.WAITING_FOR_SIGN_OFF
    signed_off = decisions.c.signed_off_by.is_not(None)
    query = (
        select(
            func.count().filter(or_(held, signed_off)).label("held"),
            func.count().filter(signed_off).label("signed_off"),
        )
        .select_from(decisions)
        .join(cases, cases.c.case_id == decisions.c.case_id)
        .where(cases.c.evaluation_id.is_(None))
    )
    held, signed_off = db.execute(query).one()
    return SignOffs(held=held, signed_off=signed_off)


@app.get("/api/me", operation_id="get_signed_in_worker")
def get_signed_in_worker(worker: SignedIn) -> Worker:
    """Get the worker signed in, with what they may sign off."""
    return worker


@app.post(
    "/api/cases/{case_id}/start", operation_id="start_case", dependencies=[AgentKey]
)
def start_case(case_id: str, request: StartRequest, db: Database) -> Case:
    """Start work on a waiting case, which moves it to in progress, only once."""
    case = find_case(db, case_id)
    if case["status"] != Status.WAITING:
        raise HTTPException(409, NOT_WAITING.format(case_id=case_id))
    if case["evaluation_id"]:
        refuse_a_round_that_cant_go_on(db, case["evaluation_id"])
    started = move_case(
        db,
        case_id,
        Status.WAITING,
        Status.IN_PROGRESS,
        thread_id=request.thread_id,
        attempts=cases.c.attempts + 1,
        resume_heard_at=None,
    )
    if not started:
        raise HTTPException(409, NOT_WAITING.format(case_id=case_id))
    return case_in_full(db, case_id)


@app.post(
    "/api/cases/{case_id}/steps", operation_id="record_step", dependencies=[AgentKey]
)
def record_step(case_id: str, request: StepRequest, db: Database) -> Step:
    """Record one step of the agent's work on a case."""
    thread_id = started_thread(db, case_id)
    return add_step(db, case_id, thread_id, NewStep(**request.model_dump()))


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
    """Record a case's decision once, as section 14 asks of it."""
    check_request(request)
    case = find_case(db, case_id)
    kind = outcome_kind() if request.decision == DecisionKind.APPROVE else None
    if case["decision"] is not None:
        if (case["decision"], case["outcome"]) == (request.decision, kind):
            return case_in_full(db, case_id)
        raise HTTPException(409, ALREADY_DECIDED.format(case_id=case_id))
    if case["status"] != Status.IN_PROGRESS:
        raise HTTPException(409, NOT_IN_PROGRESS.format(case_id=case_id))
    # An approval carries the outcome the pack resolved for the case, moved
    # opaque. A decline or a referral carries none.
    payload = None
    if kind is not None:
        payload = stored_payload(db, case, kind)
        if payload is None:
            raise falls_short(NOTHING_RESOLVED)
    limit = approval_limit(db)
    db.execute(
        insert(decisions).values(
            case_id=case_id,
            decision=request.decision,
            section=request.section,
            reason=request.reason,
            decided_by=request.decided_by,
            decided_at=now(),
            manual_version=manual_version(db),
            approval_limit=limit,
            outcome=kind,
            payload=payload,
        )
    )
    if request.decision != DecisionKind.APPROVE:
        set_status(db, case_id, Status.DECIDED)
    elif gated(db, payload, limit):
        set_status(db, case_id, Status.WAITING_FOR_SIGN_OFF)
    return case_in_full(db, case_id)


@app.post(
    "/api/cases/{case_id}/outcomes/{outcome}",
    operation_id="resolve_outcome",
    dependencies=[AgentKey],
)
def resolve_outcome(
    case_id: str, outcome: str, request: AwardRequest, db: Database
) -> Award:
    """Resolve one of a case's declared outcomes with the pack's resolve verb."""
    case = case_in_full(db, case_id)
    if case.thread_id is None:
        raise HTTPException(409, NOT_STARTED.format(case_id=case_id))
    if case.status != Status.IN_PROGRESS:
        raise HTTPException(409, NOT_IN_PROGRESS.format(case_id=case_id))
    if outcome not in loader.pack().outcomes:
        raise HTTPException(
            404, f"The pack resolves no outcome called {outcome!r}"
        )
    contract = find_contract(db, case.contract_id)
    config = {"plans": plans(), "approval_limit": approval_limit(db)}
    try:
        resolved = protocol().resolve({"contract": contract}, config, request)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    keep_outcome(db, find_case(db, case_id), outcome, resolved.model_dump())
    return resolved


@app.post(
    "/api/cases/{case_id}/effects/{effect}",
    operation_id="run_effect",
    dependencies=[AgentKey],
)
def run_effect(case_id: str, effect: str, db: Database) -> EffectRun:
    """Run one of a case's effects once, through the pack's execute verb."""
    case = find_case(db, case_id)
    if case["decision"] != DecisionKind.APPROVE:
        raise HTTPException(409, NOT_APPROVED.format(case_id=case_id))
    if effect not in loader.pack().effects:
        raise HTTPException(404, f"The pack serves no effect called {effect!r}")
    prior = db.execute(
        select(effect_runs)
        .where(effect_runs.c.case_id == case_id, effect_runs.c.effect == effect)
    ).first()
    if prior is not None:
        raise HTTPException(409, ALREADY_RAN.format(case_id=case_id, effect=effect))
    if case["status"] == Status.WAITING_FOR_SIGN_OFF:
        raise HTTPException(403, over_the_limit(case["approval_limit"]))
    limit = approval_limit(db)
    if gated(db, stored_payload(db, case, effect), limit):
        raise HTTPException(403, over_the_limit(limit))
    run_the_effect(db, case, effect)
    return case_in_full(db, case_id).effect


@app.post(
    "/api/cases/{case_id}/hold", operation_id="hold_payment", dependencies=[AgentKey]
)
def hold_payment(case_id: str, request: HoldRequest, db: Database) -> Case:
    """Hold an approval the Gateway refused for a worker's sign-off."""
    case = find_case(db, case_id)
    if case["decision"] != DecisionKind.APPROVE:
        raise HTTPException(409, NOT_APPROVED.format(case_id=case_id))
    if db.execute(
        select(effect_runs).where(effect_runs.c.case_id == case_id)
    ).first() is not None:
        effect = case["outcome"] or outcome_kind()
        raise HTTPException(409, ALREADY_RAN.format(case_id=case_id, effect=effect))
    if case["status"] == Status.WAITING_FOR_SIGN_OFF:
        return case_in_full(db, case_id)
    db.execute(
        update(decisions)
        .where(decisions.c.case_id == case_id)
        .values(gateway_refusal=request.reason)
    )
    set_status(db, case_id, Status.WAITING_FOR_SIGN_OFF)
    return case_in_full(db, case_id)


@app.post("/api/cases/{case_id}/sign-off", operation_id="sign_off_case")
def sign_off_case(case_id: str, worker: SignsOffOverTheLimit, db: Database) -> Case:
    """Sign off a held award as the worker signed in, which runs its effect."""
    case = answer_held(db, case_id, Status.DECIDED, "signed off")
    db.execute(
        update(decisions)
        .where(decisions.c.case_id == case_id)
        .values(signed_off_by=worker.name, signed_off_at=now())
    )
    run_the_effect(db, case, case["outcome"] or outcome_kind())
    db.commit()
    ask_to_resume(case_id)
    return case_in_full(db, case_id)


@app.post("/api/cases/{case_id}/send-back", operation_id="send_back_case")
def send_back_case(
    case_id: str, request: SendBackRequest, worker: SendsBack, db: Database
) -> Case:
    """Send a held decision back to the agent with a note, as the worker signed in."""
    case = answer_held(db, case_id, Status.SENT_BACK, "sent back")
    record_send_back(db, case, request.note, worker.name)
    db.commit()
    ask_to_resume(case_id)
    return case_in_full(db, case_id)


@app.post(
    "/api/cases/{case_id}/take", operation_id="take_case", dependencies=[AgentKey]
)
def take_case(case_id: str, request: TakeRequest, db: Database) -> Case:
    """Take a sent-back case back into work, once, for a dispatch or a resume."""
    find_case(db, case_id)
    check_run(db, request.run_id)
    heard = now() if request.run_id is None else None
    sent_back, in_progress = Status.SENT_BACK, Status.IN_PROGRESS
    if not move_case(db, case_id, sent_back, in_progress, resume_heard_at=heard):
        raise HTTPException(409, NOT_SENT_BACK.format(case_id=case_id))
    return case_in_full(db, case_id)


@app.post(
    "/api/cases/{case_id}/heartbeat",
    operation_id="record_case_heartbeat",
    dependencies=[AgentKey],
)
def record_case_heartbeat(case_id: str, db: Database) -> Case:
    """Record that a resume is still working on a case."""
    heard = db.execute(
        update(cases).where(cases.c.case_id == case_id).values(resume_heard_at=now())
    )
    if heard.rowcount == 0:
        raise HTTPException(404, CASE_NOT_FOUND.format(case_id=case_id))
    return case_in_full(db, case_id)


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
    error = NewStep(kind="error", content=request.reason, sources=[])
    add_step(db, case_id, case["thread_id"], error)
    status = Status.LEFT_FOR_WORKER if case["attempts"] >= ATTEMPTS else Status.WAITING
    set_status(db, case_id, status)
    return case_in_full(db, case_id)


# After every route, so the dashboard's build only answers what no route does.
app.router.routes.append(dashboard.mount)

# AWS Lambda's entry point. Nothing seeds the database there.
worker = Mangum(app, lifespan="off")
