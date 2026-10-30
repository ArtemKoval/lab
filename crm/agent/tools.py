"""The case agent's tools, each calling the backend operation it is named after, and
the context and state they read."""

import operator
from dataclasses import dataclass
from typing import Annotated, Any, TypedDict

from langchain.tools import ToolRuntime, tool
from langchain_core.messages import AnyMessage, ToolMessage
from langgraph.graph.message import add_messages
from langgraph.types import Command

from agent import api
from agent.json_text import as_json


@dataclass
class CaseContext:
    """The case a case agent is working on, and the run it works in, if any."""

    case_id: str
    run_id: str | None


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


@tool
def get_case(runtime: ToolRuntime[CaseContext]) -> str:
    """Get your case in full: the story, the items claimed and the documents."""
    return as_json(api.get_case(runtime.context.case_id))


@tool
def get_contract(contract_id: str) -> str:
    """Get a contract: the plan, add-ons, purchase date, trip and travelers."""
    return as_json(api.get_contract(contract_id))


@tool
def get_case_history(customer_id: str) -> str:
    """Get a customer's earlier cases, with the outcome and the amount paid."""
    return as_json(api.get_case_history(customer_id))


@tool
def search_documents(query: str) -> str:
    """Find the sections of the wording and the manual containing one word or phrase."""
    return as_json(api.search_documents(query))


@tool(response_format="content_and_artifact")
def read_section(
    document: api.DocumentName, number: int
) -> tuple[str, tuple[api.StepKind, str]]:
    """Read one section of the contract wording or the cases manual in full."""
    section = api.read_section(document, number)
    read = f"{section['document_title']}, section {number}: {section['title']}"
    return as_json(section), ("reading", read)


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
    return as_json(api.calculate_award(case_id, benefit, lines, paid_by_others))


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
    message = ToolMessage(as_json(case), tool_call_id=runtime.tool_call_id)
    update = {
        "messages": [message],
        "decision": case["decision"],
        "status": case["status"],
    }
    return Command(update=update)


CASE_TOOLS = [
    get_case,
    get_contract,
    get_case_history,
    search_documents,
    read_section,
    calculate_award,
    record_decision,
]
