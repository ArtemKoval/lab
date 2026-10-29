"""The harness: a queue agent works the run, and a case agent works each case."""

import json
import logging
import os
import uuid
from collections.abc import Callable
from functools import partial
from typing import Any, cast

from langchain.agents import AgentState, create_agent
from langchain.agents.middleware import (
    AgentMiddleware,
    InputAgentState,
    ModelCallLimitMiddleware,
    ToolCallRequest,
    ToolErrorMiddleware,
)
from langchain.tools import ToolException
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.state import CompiledStateGraph
from langgraph.runtime import Runtime
from langgraph.types import Command
from pydantic import SecretStr

from agent import api
from agent.tools import CASE_TOOLS, QUEUE_TOOLS, CaseContext, RunContext

log = logging.getLogger(__name__)

CaseAgent = CompiledStateGraph[Any, CaseContext, Any, Any]
QueueAgent = CompiledStateGraph[Any, RunContext, Any, Any]

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "deepseek/deepseek-v4.1-flash"
CASE_MODEL_CALLS = 30
QUEUE_MODEL_CALLS_PER_CLAIM = 6
QUEUE_MODEL_CALLS_TO_PLAN = 12
REMINDERS = 2
NO_DECISION = "The agent finished without recording a decision"
NO_SUMMARY = "The run finished without a summary."
STOPPED = "The run stopped before this case was finished"


def model() -> ChatOpenAI:
    """Return the model named in MODEL_NAME, or DeepSeek V4.1 Flash by default."""
    name = os.getenv("MODEL_NAME")
    return ChatOpenAI(
        model=name or DEFAULT_MODEL,
        base_url=OPENROUTER_BASE_URL,
        api_key=SecretStr(os.environ["OPENROUTER_API_KEY"]),
        reasoning_effort=None if name else "low",
        timeout=120,
        max_retries=5,
    )


def refusal(error: Exception, request: ToolCallRequest) -> str | None:
    """Show the model why a tool was refused; let any other error stop the agent."""
    if isinstance(error, api.Refused):
        return f"Refused with status {error}"
    if isinstance(error, ToolException):
        return f"Refused: {error}"
    return None


class RecordSteps(AgentMiddleware[AgentState, CaseContext]):
    """Record each step of a case agent's work on its case, for the dashboard,
    including any step a tool gives as its artifact, such as a section it read."""

    def after_model(
        self, state: AgentState, runtime: Runtime[CaseContext]
    ) -> dict[str, Any] | None:
        case_id = runtime.context.case_id
        message = state["messages"][-1]
        if message.text:
            api.record_step(case_id, "message", message.text)
        if isinstance(message, AIMessage):
            for call in message.tool_calls:
                args = ", ".join(
                    f"{k}={json.dumps(v)}" for k, v in call["args"].items()
                )
                api.record_step(case_id, "tool_call", f"{call['name']}({args})")

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        result = handler(request)
        if isinstance(result, ToolMessage):
            case_id = cast(CaseContext, request.runtime.context).case_id
            api.record_step(case_id, "tool_result", f"{result.name}: {result.text}")
            if result.artifact:
                api.record_step(case_id, *result.artifact)
        return result


def ask(text: str) -> InputAgentState:
    """Give an agent one message from the user."""
    return {"messages": [HumanMessage(text)]}


def describe(error: Exception) -> str:
    """Say in one line what went wrong."""
    lines = str(error).splitlines()
    return f"{type(error).__name__}: {lines[0]}" if lines else type(error).__name__


def report(case: dict[str, Any], reason: str) -> str:
    """Say in one line how a case ended: its decision and award, or why it failed."""
    case_id, status, decision = case["case_id"], case["status"], case["decision"]
    if status == "waiting":
        return f"{case_id}  failed: {reason}, back in the queue"
    if status == "left_for_worker":
        return f"{case_id}  failed: {reason}, left for a worker"
    line = f"{case_id}  {decision['decision']}  ${decision['award']:,.2f}"
    if status == "waiting_for_sign_off":
        return f"{line}, waiting for sign-off"
    if decision["decision"] == "approve" and case["payment"] is None:
        return f"{line}, not paid"
    return line


def case_agent(llm: BaseChatModel) -> CaseAgent:
    """Build the case agent, which works one case from a clean start each time."""
    middleware: list[AgentMiddleware[Any, Any]] = [
        ModelCallLimitMiddleware(run_limit=CASE_MODEL_CALLS, exit_behavior="error"),
        RecordSteps(),
        ToolErrorMiddleware(refusal),
    ]
    return create_agent(
        llm,
        tools=CASE_TOOLS,
        system_prompt=api.get_instructions()["case"],
        middleware=middleware,
        context_schema=CaseContext,
        checkpointer=False,
    )


def work_case(case_id: str, agent: CaseAgent) -> str:
    """Work one case from a clean start, as a new attempt, and report how it ended."""
    api.start_case(case_id, str(uuid.uuid4()))
    reason = NO_DECISION
    try:
        agent.invoke(ask(f"Case {case_id}"), context=CaseContext(case_id))
    except Exception as error:  # a case that fails must not stop the run
        reason = describe(error)
    case = api.get_case(case_id)
    if case["status"] == "in_progress":
        case = api.fail_case(case_id, reason)
    line = report(case, reason)
    log.info(line)
    return line


def waiting() -> list[str]:
    """Return the ids of the cases waiting in the queue, oldest submitted first."""
    cases = sorted(api.list_cases(), key=lambda case: case["submitted_on"])
    return [case["case_id"] for case in cases if case["status"] == "waiting"]


def recover() -> None:
    """Put back in the queue any case left in progress by a run that stopped."""
    for case in api.list_cases():
        if case["status"] == "in_progress":
            api.fail_case(case["case_id"], STOPPED)


def missed(run: RunContext) -> list[str]:
    """Return the waiting cases the run should still work: its own, then new ones."""
    ids = waiting()
    own = [case_id for case_id in ids if case_id in run.started]
    new = [case_id for case_id in ids if case_id not in run.started]
    return own + new[: run.cap - len(run.started)]


def queue_call_budget(cap: int) -> int:
    """Return the queue agent's model call limit for a run of this cap."""
    return QUEUE_MODEL_CALLS_PER_CLAIM * cap + QUEUE_MODEL_CALLS_TO_PLAN


def queue_agent(llm: BaseChatModel, cap: int) -> QueueAgent:
    """Build the queue agent for a run, which keeps its conversation between turns."""
    middleware: list[AgentMiddleware[Any, Any]] = [
        ModelCallLimitMiddleware(
            run_limit=queue_call_budget(cap), exit_behavior="error"
        ),
        ToolErrorMiddleware(refusal),
    ]
    return create_agent(
        llm,
        tools=QUEUE_TOOLS,
        system_prompt=api.get_instructions()["queue"],
        middleware=middleware,
        context_schema=RunContext,
        checkpointer=InMemorySaver(),
    )


def work_queue(run: RunContext, agent: QueueAgent) -> str:
    """Let the queue agent work the run, naming any cases it missed, and summarize."""
    # One tool call at a time, so the cap holds when several cases are handed over.
    config: RunnableConfig = {
        "configurable": {"thread_id": run.run_id},
        "max_concurrency": 1,
    }
    message = f"Please work the queue. This run can work up to {run.cap} cases."
    state = agent.invoke(ask(message), config, context=run)
    for _ in range(REMINDERS):
        left = missed(run)
        if not left:
            break
        reminder = (
            "These cases are still waiting within the run's cap: "
            f"{', '.join(left)}. Please work them, then finish with the summary."
        )
        state = agent.invoke(ask(reminder), config, context=run)
    return state["messages"][-1].text or NO_SUMMARY


def run_queue(cap: int | None, llm: BaseChatModel, case_llm: BaseChatModel) -> None:
    """Work the queue with a queue agent, up to cap cases or every waiting case."""
    recover()
    count = len(waiting())
    if count == 0:
        log.info("No cases are waiting")
        return
    cap = min(cap or count, count)
    run_id = api.start_run(cap)["run_id"]
    run = RunContext(run_id, cap, partial(work_case, agent=case_agent(case_llm)))
    try:
        summary = work_queue(run, queue_agent(llm, cap))
    except Exception as error:
        api.finish_run(run_id, f"The run stopped: {describe(error)}")
        raise
    api.finish_run(run_id, summary)
    log.info(summary)
