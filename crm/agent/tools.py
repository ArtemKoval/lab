"""The case agent's tools, the app's operations it calls on its route, the context
layer's lookups both agents have, and the search of its memory, and the context and
state they read."""

import operator
from dataclasses import dataclass
from typing import Annotated, Any, TypedDict, cast

from langchain.tools import BaseTool, ToolException, ToolRuntime, tool
from langchain_core.messages import AnyMessage, ToolMessage
from langgraph.graph.message import add_messages
from langgraph.store.base import BaseStore
from langgraph.types import Command

from agent import api, app_terms, memory
from agent.agentcore_memory import UNREACHABLE
from agent.context_tools import CONTEXT_TOOLS, Query
from agent.json_text import as_json
from agent.routes import Route, Target
from domains import loader


@dataclass
class CaseContext:
    """The case a case agent is working on, its contract and customer, the run it
    works in, if any, the route its tools take, and who its decisions are made by."""

    case_id: str
    run_id: str | None
    contract_id: str
    customer_id: str
    route: Route
    decided_by: str


def keep_last(_: Any, new: Any) -> Any:
    """Keep the newest value, even when two tool calls set it in the same step. With
    it, LangGraph starts the key empty, as {} or "", so the key is always there."""
    return new


class CaseState(TypedDict):
    """What the case graph keeps for one case, saved after every step: the check
    for hidden instructions' result, its reason and instructions_found, empty until
    the check has run, and the decision and the case's status as the backend
    recorded them, empty until then."""

    messages: Annotated[list[AnyMessage], add_messages]
    model_calls: Annotated[int, operator.add]
    screening: Annotated[dict[str, Any], keep_last]
    decision: Annotated[dict[str, Any], keep_last]
    status: Annotated[str, keep_last]


# What the case agent never reads of a case: the decisions workers sent back,
# whose notes reach its model only as a worker's message.
UNREAD = "sent_back_decisions"


def case_as_read(case: dict[str, Any]) -> str:
    """A case in full, as the case agent reads it, which is also what the check for
    hidden instructions reads."""
    return as_json({field: value for field, value in case.items() if field != UNREAD})


def on_app(runtime: ToolRuntime[CaseContext], operation: str, **inputs: Any) -> Any:
    """Call one of the app's operations on the case agent's route."""
    return runtime.context.route.call(Target.APP, operation, inputs)


# A step a tool gives as its artifact, which the harness records on the case: its
# kind, its content and the context files it came from.
Step = tuple[api.StepKind, str, api.Sources]


@tool
def get_case(runtime: ToolRuntime[CaseContext]) -> str:
    """Get your case in full: the story, the items claimed and the documents."""
    return case_as_read(on_app(runtime, "get_case", case_id=runtime.context.case_id))


@tool
def get_contract(runtime: ToolRuntime[CaseContext]) -> str:
    """Get your case's contract: the plan, add-ons, purchase date,
    trip and travelers."""
    contract_id = runtime.context.contract_id
    return as_json(on_app(runtime, "get_contract", contract_id=contract_id))


@tool
def get_case_history(runtime: ToolRuntime[CaseContext]) -> str:
    """Get your customer's earlier cases, with the outcome and the amount paid."""
    customer_id = runtime.context.customer_id
    return as_json(on_app(runtime, "get_case_history", customer_id=customer_id))


@tool(response_format="content_and_artifact")
def search_memory(query: Query, runtime: ToolRuntime[CaseContext]) -> tuple[str, Step]:
    """Search what we remember about this case's customer from their earlier cases."""
    context = runtime.context
    try:
        found = memory.recall(
            cast(BaseStore, runtime.store),
            context.customer_id,
            context.case_id,
            query,
        )
    except UNREACHABLE as error:
        raise ToolException(f"The memory can't be reached. {error}") from error
    return as_json(found), ("memory_search", what_was_found(query, found), [])


def what_was_found(query: str, found: list[str]) -> str:
    """Say what a search of the memory looked for and what it found."""
    if not found:
        return f'"{query}": nothing found'
    return "\n".join([f'"{query}"', *(f"- {text}" for text in found)])


@tool
def resolve_outcome(
    benefit: Annotated[api.Benefit, "The benefit the case is resolved under"],
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
    """Resolve your case's outcome with the pack's rules."""
    resolved = on_app(
        runtime,
        "resolve_outcome",
        case_id=runtime.context.case_id,
        outcome=next(iter(loader.pack().outcomes)),
        benefit=benefit,
        lines=[line.model_dump() for line in lines],
        paid_by_others=paid_by_others,
    )
    return as_json(resolved)


@tool
def record_decision(
    decision: app_terms.DecisionKind,
    section: Annotated[str, "The sections of the wording and the manual relied on"],
    reason: Annotated[str, "Two or three plain sentences for a colleague"],
    runtime: ToolRuntime[CaseContext],
) -> Command:
    """Record the decision on your case, once, which ends your work on it. An
    approval carries the outcome resolve_outcome worked out for the case."""
    case = on_app(
        runtime,
        "record_decision",
        case_id=runtime.context.case_id,
        decision=decision,
        section=section,
        reason=reason,
        decided_by=runtime.context.decided_by,
    )
    message = ToolMessage(case_as_read(case), tool_call_id=runtime.tool_call_id)
    update = {
        "messages": [message],
        "decision": case["decision"],
        "status": case["status"],
    }
    return Command(update=update)


APP_TOOLS = [
    get_case,
    get_contract,
    get_case_history,
    resolve_outcome,
    record_decision,
]
CASE_TOOLS = APP_TOOLS + CONTEXT_TOOLS


def case_tools(remembers: bool) -> list[BaseTool]:
    """The case agent's tools, with a search of its memory when it has one."""
    return CASE_TOOLS + [search_memory] if remembers else CASE_TOOLS


# The target each tool calls, by which a route names a call to it.
TARGETS = {tool.name: Target.APP for tool in APP_TOOLS} | {
    tool.name: Target.CONTEXT for tool in CONTEXT_TOOLS
}
