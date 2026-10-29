"""The agents' tools. The case agent's tools, list_cases and write_todos call the
backend operations they are named after, and work_case hands a case to a case agent.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Annotated

from langchain.tools import ToolException, ToolRuntime, tool

from agent import api


@dataclass
class CaseContext:
    """The case a case agent is working on."""

    case_id: str


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
def record_decision(
    decision: api.DecisionKind,
    award: Annotated[float, "In US dollars, and 0 for a decline or a referral"],
    section: Annotated[str, "The sections of the wording and the manual relied on"],
    reason: Annotated[str, "Two or three plain sentences for a colleague"],
    runtime: ToolRuntime[CaseContext],
) -> str:
    """Record the decision on your case, once; an approval over the limit waits."""
    case_id = runtime.context.case_id
    return json.dumps(api.record_decision(case_id, decision, award, section, reason))


@tool
def pay_case(amount: float, runtime: ToolRuntime[CaseContext]) -> str:
    """Pay your approved case its award, unless it needs a worker's sign-off."""
    return json.dumps(api.pay_case(runtime.context.case_id, amount))


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
    record_decision,
    pay_case,
]
QUEUE_TOOLS = [list_cases, write_todos, work_case]
