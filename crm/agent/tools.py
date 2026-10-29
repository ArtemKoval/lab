"""The agents' tools. The case agent's tools, list_cases and write_todos call the
backend operations they are named after, and work_case hands a case to a case agent.
"""

import json
import operator
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Annotated, Any, TypedDict

from langchain.tools import ToolException, ToolRuntime, tool
from langchain_core.messages import AnyMessage, ToolMessage
from langgraph.graph.message import add_messages
from langgraph.types import Command

from agent import api


@dataclass
class CaseContext:
    """The case a case agent is working on."""

    case_id: str


def keep_last(_: Any, new: Any) -> Any:
    """Keep the newest value, even when two tool calls set it in the same step. With
    it, LangGraph starts the key empty, as {} or "", so the key is always there."""
    return new


class CaseState(TypedDict):
    """What the case graph keeps for one case, saved after every step. The decision
    and the case's status are as the backend recorded them, and empty until then."""

    messages: Annotated[list[AnyMessage], add_messages]
    model_calls: Annotated[int, operator.add]
    decision: Annotated[dict[str, Any], keep_last]
    status: Annotated[str, keep_last]


@dataclass
class RunContext:
    """A queue agent's run: its cap, how to work a case, and the cases started."""

    run_id: str
    cap: int
    work_case: Callable[[str], str]
    started: set[str] = field(default_factory=set)


@tool
def get_case(runtime: ToolRuntime[CaseContext]) -> str:
    """Get your case in full: the story, the items claimed and the documents."""
    return json.dumps(api.get_case(runtime.context.case_id))


@tool
def get_contract(contract_id: str) -> str:
    """Get a contract: the plan, add-ons, purchase date, trip and travelers."""
    return json.dumps(api.get_contract(contract_id))


@tool
def get_case_history(customer_id: str) -> str:
    """Get a customer's earlier cases, with the outcome and the amount paid."""
    return json.dumps(api.get_case_history(customer_id))


@tool
def search_documents(query: str) -> str:
    """Find the sections of the wording and the manual containing one word or phrase."""
    return json.dumps(api.search_documents(query))


@tool(response_format="content_and_artifact")
def read_section(
    document: api.DocumentName, number: int
) -> tuple[str, tuple[api.StepKind, str]]:
    """Read one section of the contract wording or the cases manual in full."""
    section = api.read_section(document, number)
    read = f"{section['document_title']}, section {number}: {section['title']}"
    return json.dumps(section), ("reading", read)


@tool
def calculate_award(
    benefit: Annotated[api.Benefit, "The benefit the case is paid under"],
    lines: Annotated[
        list[api.Line],
        "The covered items and expenses, one for each line of the case, with any "
        "excluded ones left out",
    ],
    paid_by_others: Annotated[
        float, "What a carrier, hotel or anyone else has paid or refunded, or 0"
    ],
    runtime: ToolRuntime[CaseContext],
) -> str:
    """Work out the award on your case with CRM's award rules."""
    case_id = runtime.context.case_id
    return json.dumps(api.calculate_award(case_id, benefit, lines, paid_by_others))


@tool
def record_decision(
    decision: api.DecisionKind,
    award: Annotated[float, "In US dollars, and 0 for a decline or a referral"],
    section: Annotated[str, "The sections of the wording and the manual relied on"],
    reason: Annotated[str, "Two or three plain sentences for a colleague"],
    runtime: ToolRuntime[CaseContext],
) -> Command:
    """Record the decision on your case, once, which ends your work on it."""
    case_id = runtime.context.case_id
    case = api.record_decision(case_id, decision, award, section, reason)
    message = ToolMessage(json.dumps(case), tool_call_id=runtime.tool_call_id)
    update = {
        "messages": [message],
        "decision": case["decision"],
        "status": case["status"],
    }
    return Command(update=update)


@tool
def list_cases() -> str:
    """List every case in the queue, in id order, with its status and decision."""
    return json.dumps(api.list_cases())


@tool
def write_todos(todos: list[api.Todo], runtime: ToolRuntime[RunContext]) -> str:
    """Replace the run's to-do list, sending every item with its current status."""
    return json.dumps(api.write_todos(runtime.context.run_id, todos))


@tool
def work_case(case_id: str, runtime: ToolRuntime[RunContext]) -> str:
    """Hand one case to a new case agent, which reports back in one line."""
    run = runtime.context
    if case_id not in run.started and len(run.started) >= run.cap:
        started = ", ".join(sorted(run.started))
        raise ToolException(
            f"this run can work {run.cap} cases, and has started {started}"
        )
    report = run.work_case(case_id)
    run.started.add(case_id)
    return report


CASE_TOOLS = [
    get_case,
    get_contract,
    get_case_history,
    search_documents,
    read_section,
    calculate_award,
    record_decision,
]
QUEUE_TOOLS = [list_cases, write_todos, work_case]
