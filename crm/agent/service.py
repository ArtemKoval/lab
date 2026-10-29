"""The agent's service: it works the dispatches and evaluations the backend starts,
one at a time, and picks a case back up after a worker's sign-off. npm run dev
starts it beside the backend and the dashboard."""

import logging
import threading
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from functools import partial
from typing import Annotated, Any

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from agent import api
from agent.console import show_reports
from agent.dispatcher import work_run
from agent.harness import (
    NewGraph,
    carry_on,
    case_graphs,
    checkpoint_pool,
    model,
    work_in_run,
)

ALREADY_RUNNING = "A dispatch or an evaluation is already running"
ACCEPTED = {"status": "accepted"}
# The most case agents at once, as the backend and the dashboard also allow.
MOST_AGENTS = 25
NO_REASONING_EFFORT = "none"

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Keep the checkpoint pool open while the service runs, after marking any run
    an earlier service left running as stopped."""
    show_reports()
    with checkpoint_pool() as pool:
        app.state.pool = pool
        api.stop_runs()
        yield


app = FastAPI(title="CRM Agent", lifespan=lifespan)

# One dispatch or evaluation at a time, and the cases being resumed after a
# sign-off, which a dispatch leaves alone.
one_run = threading.Lock()
resuming: set[str] = set()


@app.exception_handler(api.Refused)
def refused(_: Request, error: api.Refused) -> JSONResponse:
    """Pass on the backend's refusal, such as a case it doesn't know."""
    return JSONResponse({"detail": error.detail}, status_code=error.status_code)


@dataclass
class CaseAgents:
    """The service's case agents: their model, its reasoning effort, and how to
    build a case graph with a saver of its own."""

    model: str
    reasoning_effort: str
    new_graph: NewGraph


def build_case_agents(request: Request) -> CaseAgents:
    """Build the model for one request, and case graphs on the service's pool."""
    llm = model()
    return CaseAgents(
        llm.model_name,
        llm.reasoning_effort or NO_REASONING_EFFORT,
        case_graphs(llm, request.app.state.pool),
    )


CaseAgentsDep = Annotated[CaseAgents, Depends(build_case_agents)]


class DispatchRequest(BaseModel):
    agents: int = Field(ge=1, le=MOST_AGENTS, description="Case agents at once")


class EvaluationRequest(DispatchRequest):
    evaluation_set: api.EvaluationSet
    tiny: bool = Field(description="Only the set's five tiny cases")


def take_the_run() -> None:
    """Take the one run the service works at a time, or refuse with a 409."""
    if not one_run.acquire(blocking=False):
        raise HTTPException(409, ALREADY_RUNNING)


def work_in_background(
    create: Callable[[], dict[str, Any]], case_agents: CaseAgents
) -> None:
    """Create a run through the backend and work it, then let the next run start. A
    run whose dispatcher fails is marked stopped."""
    work = partial(work_in_run, new_graph=case_agents.new_graph)
    try:
        work_run(create(), work, resuming)
    except Exception:
        log.exception("The run stopped")
        api.stop_runs()
    finally:
        one_run.release()


@app.get("/api/health", operation_id="health")
def health() -> dict[str, str]:
    """Check that the agent's service is running."""
    return {"status": "ok"}


@app.post("/api/dispatches", operation_id="start_dispatch", status_code=202)
def start_dispatch(
    request: DispatchRequest, case_agents: CaseAgentsDep, background: BackgroundTasks
) -> dict[str, str]:
    """Start a dispatch with up to N case agents at once."""
    take_the_run()
    create = partial(
        api.create_dispatch,
        request.agents,
        case_agents.model,
        case_agents.reasoning_effort,
    )
    background.add_task(work_in_background, create, case_agents)
    return ACCEPTED


def resume(case_id: str, case_agents: CaseAgents) -> None:
    """Carry a signed-off case on, keeping dispatches away from it meanwhile."""
    try:
        carry_on(case_id, None, case_agents.new_graph())
    finally:
        resuming.discard(case_id)


@app.post("/api/cases/{case_id}/resume", operation_id="resume_case", status_code=202)
def resume_case(
    case_id: str, case_agents: CaseAgentsDep, background: BackgroundTasks
) -> dict[str, str]:
    """Pick a case back up after a worker's sign-off, without waiting for it."""
    case = api.get_case(case_id)
    signed_off = case["decision"] and case["decision"]["signed_off_by"]
    if case["status"] != api.Status.IN_PROGRESS or not signed_off:
        raise HTTPException(409, f"Case {case_id} has no sign-off waiting to be paid")
    resuming.add(case_id)
    background.add_task(resume, case_id, case_agents)
    return ACCEPTED


@app.post("/api/evaluations", operation_id="start_evaluation", status_code=202)
def start_evaluation(
    request: EvaluationRequest,
    case_agents: CaseAgentsDep,
    background: BackgroundTasks,
) -> dict[str, str]:
    """Start an evaluation with up to N case agents at once."""
    take_the_run()
    create = partial(
        api.create_evaluation,
        request.evaluation_set,
        request.tiny,
        request.agents,
        case_agents.model,
        case_agents.reasoning_effort,
    )
    background.add_task(work_in_background, create, case_agents)
    return ACCEPTED
