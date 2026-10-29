"""The agent's service: the backend calls it after a worker's sign-off, and it picks
the case back up. npm run dev starts it beside the backend and the dashboard."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from agent import api
from agent.console import show_reports
from agent.harness import CaseGraph, carry_on, case_graph, checkpointer, model


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Keep the case graph's checkpointer open while the service runs."""
    show_reports()
    with checkpointer() as saver:
        app.state.saver = saver
        yield


app = FastAPI(title="CRM Agent", lifespan=lifespan)


@app.exception_handler(api.Refused)
def refused(_: Request, error: api.Refused) -> JSONResponse:
    """Pass on the backend's refusal, such as a case it doesn't know."""
    return JSONResponse({"detail": error.detail}, status_code=error.status_code)


def build_graph(request: Request) -> CaseGraph:
    """Build the case graph for one request, on the service's checkpointer."""
    return case_graph(model(), request.app.state.saver)


Graph = Annotated[CaseGraph, Depends(build_graph)]


@app.get("/api/health", operation_id="health")
def health() -> dict[str, str]:
    """Check that the agent's service is running."""
    return {"status": "ok"}


@app.post("/api/cases/{case_id}/resume", operation_id="resume_case", status_code=202)
def resume_case(
    case_id: str, graph: Graph, background: BackgroundTasks
) -> dict[str, str]:
    """Pick a case back up after a worker's sign-off, without waiting for it."""
    case = api.get_case(case_id)
    signed_off = case["decision"] and case["decision"]["signed_off_by"]
    if case["status"] != api.Status.IN_PROGRESS or not signed_off:
        raise HTTPException(409, f"Case {case_id} has no sign-off waiting to be paid")
    background.add_task(carry_on, case_id, graph)
    return {"status": "accepted"}
