"""The dispatcher: a LangGraph graph with no model that works a dispatch or an
evaluation, handing each case to a case agent of its own, up to N at once."""

import logging
import operator
from collections.abc import Callable
from dataclasses import dataclass
from http import HTTPStatus
from typing import Annotated, Any, TypedDict, cast

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.runtime import ExecutionInfo, Runtime
from langgraph.types import RetryPolicy, Send

from agent import api, app_terms, harness
from agent.connection import Refused
from agent.console import describe
from agent.root_run import as_root_run

log = logging.getLogger(__name__)

LIST_CASES = "list_cases"
WORK_CASE = "work_case"
FINISH_RUN = "finish_run"
TO_WORK = (
    app_terms.Status.IN_PROGRESS,
    app_terms.Status.WAITING,
    app_terms.Status.SENT_BACK,
)
TAKEN_BY_A_RESUME = "{case_id}  taken by a resume"

# A rate limit or a timeout waits about 10 seconds, then about 20, on top of the
# model client's own retries, and carries the case on from its last saved step.
RETRY = RetryPolicy(max_attempts=3, initial_interval=10, retry_on=harness.TRANSIENT)


class Dispatch(TypedDict):
    """What the dispatcher keeps for one run: the cases to work, and a report line
    for each, added together as the case agents finish."""

    cases: list[str]
    reports: Annotated[list[str], operator.add]


class CaseToWork(TypedDict):
    """What the dispatcher sends a case agent: the case it works."""

    case_id: str


# Works one case in a run, given the case's id and the run's, and reports how it
# ended: the harness's work_in_run, bound to how its case agents are built.
WorkInRun = Callable[[str, str], str]

# How a case still failing after its tries is left, by the kind of run.
LEFT = {
    app_terms.DISPATCH: "left for the next dispatch",
    app_terms.EVALUATION: "left in progress",
}


@dataclass
class DispatchContext:
    """The run being worked, and how to work one of its cases."""

    run: dict[str, Any]
    work: WorkInRun


Dispatcher = CompiledStateGraph[Dispatch, DispatchContext, Any, Any]


def list_cases(state: Dispatch, runtime: Runtime[DispatchContext]) -> dict[str, Any]:
    """Choose the cases to work: an evaluation's copies, which the backend made, or
    the queue's cases in progress, waiting and sent back, oldest submitted first,
    which the dispatch records. It leaves out a case a resume is working on, and
    takes each sent-back case as it lists it, so a resume can't take it
    afterwards; one a resume took first is reported and left out."""
    run = runtime.context.run
    if run["kind"] == app_terms.EVALUATION:
        return {"cases": [case["case_id"] for case in run["cases"]]}
    queue = sorted(api.list_cases(), key=lambda c: (c["submitted_on"], c["case_id"]))
    cases, reports = [], []
    for case in queue:
        if case["status"] not in TO_WORK or case["resuming"]:
            continue
        case_id = case["case_id"]
        if case["status"] == app_terms.Status.SENT_BACK and not took(case_id, run):
            reports.append(TAKEN_BY_A_RESUME.format(case_id=case_id))
        else:
            cases.append(case_id)
    api.record_run_cases(run["run_id"], cases)
    return {"cases": cases, "reports": reports}


def took(case_id: str, run: dict[str, Any]) -> bool:
    """Take a sent-back case for the run, and say whether the run got it rather
    than a resume."""
    try:
        api.take_case(case_id, run["run_id"])
    except Refused as refusal:
        if refusal.status_code != HTTPStatus.CONFLICT:
            raise
        log.info(TAKEN_BY_A_RESUME.format(case_id=case_id))
        return False
    return True


def fan_out(state: Dispatch) -> list[Send] | str:
    """Send each case to a case agent of its own, or finish a run with none."""
    sends = [Send(WORK_CASE, CaseToWork(case_id=c)) for c in state["cases"]]
    return sends or FINISH_RUN


def hand_over(case_id: str, context: DispatchContext) -> str:
    """Hand a case to the case agent, and once more if its first attempt failed and
    put it back in the queue."""
    run_id = context.run["run_id"]
    report = context.work(case_id, run_id)
    if api.get_case(case_id)["status"] == app_terms.Status.WAITING:
        report = context.work(case_id, run_id)
    return report


def work_case(state: CaseToWork, runtime: Runtime[DispatchContext]) -> dict[str, Any]:
    """Work one case. A rate limit or a timeout goes to the RetryPolicy, which waits
    and carries the case on, until the last try leaves it in progress. No error
    stops the dispatch."""
    case_id = state["case_id"]
    try:
        report = hand_over(case_id, runtime.context)
    except Exception as error:
        # LangGraph sets the execution info in every node.
        attempt = cast(ExecutionInfo, runtime.execution_info).node_attempt
        if isinstance(error, harness.TRANSIENT) and attempt < RETRY.max_attempts:
            raise
        left = LEFT[runtime.context.run["kind"]]
        report = f"{case_id}  {left}: {describe(error)}"
        log.warning(report)
    return {"reports": [report]}


def finish_run(state: Dispatch, runtime: Runtime[DispatchContext]) -> None:
    """Finish the run once every case has been handed over and come back."""
    api.finish_run(runtime.context.run["run_id"])


def dispatcher() -> Dispatcher:
    """Build the dispatcher's graph."""
    builder = StateGraph(Dispatch, context_schema=DispatchContext)
    builder.add_node(LIST_CASES, list_cases)
    builder.add_node(WORK_CASE, work_case, retry_policy=RETRY)
    builder.add_node(FINISH_RUN, finish_run)
    builder.add_edge(START, LIST_CASES)
    builder.add_conditional_edges(LIST_CASES, fan_out, [WORK_CASE, FINISH_RUN])
    builder.add_edge(WORK_CASE, FINISH_RUN)
    builder.add_edge(FINISH_RUN, END)
    return builder.compile()


def work_run(run: dict[str, Any], work: WorkInRun) -> list[str]:
    """Work a dispatch or an evaluation with up to its N case agents at once, and
    return each case's report line."""
    context = DispatchContext(run, work)
    config: RunnableConfig = {"max_concurrency": run["agents"]}
    state = as_root_run(
        dispatcher().invoke, {"cases": [], "reports": []}, config, context=context
    )
    return state["reports"]
