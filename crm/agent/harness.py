"""The harness: a queue agent works the run, and a case graph works each case."""

import contextvars
import json
import logging
import os
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from functools import partial
from typing import Any, cast

from langchain.agents import create_agent
from langchain.agents.middleware import (
    AgentMiddleware,
    ModelCallLimitMiddleware,
    ToolErrorMiddleware,
)
from langchain.tools import ToolException
from langchain_core.language_models import BaseChatModel, LanguageModelInput
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_openai import ChatOpenAI
from langfuse.langchain import CallbackHandler
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt.tool_node import ToolCallRequest
from langgraph.runtime import Runtime
from langgraph.types import Command, interrupt
from psycopg import Connection, sql
from psycopg.rows import DictRow, dict_row
from psycopg_pool import ConnectionPool
from pydantic import SecretStr

from agent import api
from agent.tools import CASE_TOOLS, QUEUE_TOOLS, CaseContext, CaseState, RunContext

log = logging.getLogger(__name__)

CaseGraph = CompiledStateGraph[CaseState, CaseContext, Any, Any]
QueueAgent = CompiledStateGraph[Any, RunContext, Any, Any]
Messages = dict[str, list[BaseMessage]]
Start = Messages | Command | None

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "deepseek/deepseek-v4.1-flash"
SCHEMA = "crm"
CONNECTIONS = 4
CASE_MODEL_CALLS = 30
QUEUE_MODEL_CALLS_PER_CASE = 6
QUEUE_MODEL_CALLS_TO_PLAN = 12
REMINDERS = 2
NO_DECISION = "The agent finished without recording a decision"
NO_SUMMARY = "The run finished without a summary."
RUN_STOPPED = "The run stopped before it finished."
WORK_CASE = "Work case"
CARRY_ON = "Carry on"
AGENT = "agent"
TOOLS = "tools"
PAUSE = "wait_for_sign_off"
PAY = "pay"


class TooManyModelCalls(Exception):
    """The case agent made as many model calls as it may without finishing."""


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


@contextmanager
def checkpointer() -> Iterator[PostgresSaver]:
    """Save the case graph's progress in Postgres at DATABASE_URL, in our own schema,
    with at most CONNECTIONS connections."""
    settings = {
        "autocommit": True,
        "prepare_threshold": 0,
        "row_factory": dict_row,
        "options": f"-c search_path={SCHEMA}",
    }
    with ConnectionPool[Connection[DictRow]](
        os.environ["DATABASE_URL"],
        min_size=1,
        max_size=CONNECTIONS,
        kwargs=settings,
    ) as pool:
        with pool.connection() as connection:
            create = sql.SQL("CREATE SCHEMA IF NOT EXISTS {}")
            connection.execute(create.format(sql.Identifier(SCHEMA)))
        saver = PostgresSaver(pool)
        saver.setup()
        yield saver


def refusal(error: Exception) -> str:
    """Show the model why a tool was refused, and let any other error stop the agent."""
    if isinstance(error, api.Refused):
        return f"Refused with status {error}"
    if isinstance(error, ToolException):
        return f"Refused: {error}"
    raise error


def record_reply(case_id: str, reply: BaseMessage) -> None:
    """Record the model's reply on the case: its text, then each tool it calls."""
    if reply.text:
        api.record_step(case_id, "message", reply.text)
    if isinstance(reply, AIMessage):
        for call in reply.tool_calls:
            args = ", ".join(f"{k}={json.dumps(v)}" for k, v in call["args"].items())
            api.record_step(case_id, "tool_call", f"{call['name']}({args})")


def record_result(
    request: ToolCallRequest,
    execute: Callable[[ToolCallRequest], ToolMessage | Command],
) -> ToolMessage | Command:
    """Run a tool and record its result on the case, then any step it gives as its
    artifact, such as a section it read."""
    result = execute(request)
    if isinstance(result, ToolMessage):
        message = result
    else:
        message = cast(dict[str, Any], result.update)["messages"][0]
    case_id = cast(CaseContext, request.runtime.context).case_id
    api.record_step(case_id, "tool_result", f"{message.name}: {message.text}")
    if message.artifact:
        api.record_step(case_id, *message.artifact)
    return result


def call_model(
    state: CaseState,
    runtime: Runtime[CaseContext],
    llm: Runnable[LanguageModelInput, BaseMessage],
    instructions: SystemMessage,
) -> dict[str, Any]:
    """Ask the model for its next step, up to CASE_MODEL_CALLS times in all, and
    record its reply on the case."""
    calls = state["model_calls"]
    if calls >= CASE_MODEL_CALLS:
        message = f"The case agent made {calls} model calls without finishing"
        raise TooManyModelCalls(message)
    reply = llm.invoke([instructions, *state["messages"]])
    record_reply(runtime.context.case_id, reply)
    return {"messages": [reply], "model_calls": 1}


def wait_for_sign_off(state: CaseState, runtime: Runtime[CaseContext]) -> None:
    """Pause until a worker signs off the award, which the backend records. On
    resume this runs again from the top, so nothing comes before the interrupt."""
    interrupt({"case_id": runtime.context.case_id})


def pay(state: CaseState, runtime: Runtime[CaseContext]) -> dict[str, Any]:
    """Pay the approved award, which the backend refuses unless it may be paid."""
    case = api.pay_case(runtime.context.case_id, state["decision"]["award"])
    return {"status": case["status"]}


def after_agent(state: CaseState) -> str:
    """Run the tools the model asked for, or stop: it finished without a decision."""
    reply = state["messages"][-1]
    return TOOLS if isinstance(reply, AIMessage) and reply.tool_calls else END


def after_tools(state: CaseState) -> str:
    """Go back to the model until a decision is recorded, then pay an approval, after
    a sign-off if the backend holds it, or stop."""
    decision, status = state["decision"], state["status"]
    if not decision:
        return AGENT
    if status == api.Status.WAITING_FOR_SIGN_OFF:
        return PAUSE
    if decision["decision"] == api.APPROVE and status == api.Status.IN_PROGRESS:
        return PAY
    return END


def case_graph(llm: BaseChatModel, saver: BaseCheckpointSaver[Any]) -> CaseGraph:
    """Build the case agent's graph, which saves its progress after every step."""
    instructions = SystemMessage(api.get_instructions()["case"])
    builder = StateGraph(CaseState, context_schema=CaseContext)
    builder.add_node(
        AGENT,
        partial(call_model, llm=llm.bind_tools(CASE_TOOLS), instructions=instructions),
    )
    builder.add_node(
        TOOLS,
        ToolNode(CASE_TOOLS, handle_tool_errors=refusal, wrap_tool_call=record_result),
    )
    builder.add_node(PAUSE, wait_for_sign_off)
    builder.add_node(PAY, pay)
    builder.add_edge(START, AGENT)
    builder.add_conditional_edges(AGENT, after_agent, [TOOLS, END])
    builder.add_conditional_edges(TOOLS, after_tools, [AGENT, PAUSE, PAY, END])
    builder.add_edge(PAUSE, PAY)
    builder.add_edge(PAY, END)
    return builder.compile(checkpointer=saver)


def thread_of(case: dict[str, Any]) -> RunnableConfig:
    """Address the case's thread, where the case graph saves its progress."""
    return {"configurable": {"thread_id": case["thread_id"]}}


def case_config(case: dict[str, Any], name: str) -> RunnableConfig:
    """Run on the case's thread, traced in Langfuse in the session of that thread."""
    session = f"{case['case_id']}:{case['thread_id']}"
    return thread_of(case) | {
        "callbacks": [CallbackHandler()],
        "metadata": {"langfuse_session_id": session, "langfuse_trace_name": name},
        # One tool call at a time, so two decisions in one reply can't race.
        "max_concurrency": 1,
    }


def ask(text: str) -> Messages:
    """Give an agent one message from the user."""
    return {"messages": [HumanMessage(text)]}


def begin(case_id: str) -> Messages:
    """Give a case agent its first message, naming the case it works on."""
    return ask(f"Case {case_id}")


def describe(error: Exception) -> str:
    """Say in one line what went wrong."""
    lines = str(error).splitlines()
    return f"{type(error).__name__}: {lines[0]}" if lines else type(error).__name__


def report(case: dict[str, Any], reason: str) -> str:
    """Say in one line how a case ended: its decision and award, or why it failed."""
    case_id, status, decision = case["case_id"], case["status"], case["decision"]
    if status == api.Status.WAITING:
        return f"{case_id}  failed: {reason}, back in the queue"
    if status == api.Status.LEFT_FOR_WORKER:
        return f"{case_id}  failed: {reason}, left for a worker"
    line = f"{case_id}  {decision['decision']}  ${decision['award']:,.2f}"
    if status == api.Status.WAITING_FOR_SIGN_OFF:
        return f"{line}, waiting for sign-off"
    if decision["decision"] == api.APPROVE and case["payment"] is None:
        return f"{line}, not paid yet"
    return line


def run_case_graph(
    graph: CaseGraph, start: Start, case: dict[str, Any], name: str
) -> str | None:
    """Run the case graph on the case's thread, saving each step, and say what went
    wrong, if anything."""
    try:
        # A fresh context makes this a root run even inside the queue agent's tool,
        # which Langfuse needs to put it in the case's session.
        contextvars.Context().run(
            graph.invoke,
            start,
            case_config(case, name),
            context=CaseContext(case["case_id"]),
            durability="sync",
        )
    except Exception as error:  # a case that fails must not stop the run
        return describe(error)
    return None


def settle(case_id: str, error: str | None) -> str:
    """Fail a case the agent left undecided, and report how the case ended. An
    error after the decision is logged, and the case keeps its decision."""
    case = api.get_case(case_id)
    reason = error or NO_DECISION
    if case["status"] == api.Status.IN_PROGRESS and case["decision"] is None:
        case = api.fail_case(case_id, reason)
    elif error:
        log.warning("%s  %s", case_id, error)
    line = report(case, reason)
    log.info(line)
    return line


def work_case(case_id: str, graph: CaseGraph) -> str:
    """Work one case from a clean start, as a new attempt, and report how it ended."""
    case = api.start_case(case_id, str(uuid.uuid4()))
    error = run_case_graph(graph, begin(case_id), case, WORK_CASE)
    return settle(case_id, error)


def carry_on(case_id: str, graph: CaseGraph) -> str:
    """Carry a case in progress on from its saved progress, as the same attempt, and
    report how it ended. A case at the pause has been signed off, so it resumes past
    it. One with nothing saved, stopped before its first step, starts on its own
    thread; any other carries on, finishing a step whose writes were saved."""
    case = api.get_case(case_id)
    saved = graph.get_state(thread_of(case))
    start: Start = None
    if saved.next == (PAUSE,):
        start = Command(resume=True)
    elif saved.created_at is None and case["decision"] is None:
        start = begin(case_id)
    error = run_case_graph(graph, start, case, CARRY_ON)
    return settle(case_id, error)


def waiting() -> list[str]:
    """Return the ids of the cases waiting in the queue, oldest submitted first."""
    cases = sorted(api.list_cases(), key=lambda case: case["submitted_on"])
    return [c["case_id"] for c in cases if c["status"] == api.Status.WAITING]


def finish_stopped_run() -> None:
    """Finish the latest run if it stopped before it finished."""
    run = api.get_latest_run()
    if run is not None and run["status"] == api.RunStatus.RUNNING:
        api.finish_run(run["run_id"], RUN_STOPPED)


def carry_on_stopped(graph: CaseGraph) -> None:
    """Carry on every case in progress: stopped partway, or signed off while the
    agent was away."""
    for case in api.list_cases():
        if case["status"] == api.Status.IN_PROGRESS:
            carry_on(case["case_id"], graph)


def missed(run: RunContext) -> list[str]:
    """Return the waiting cases the run should still work: its own, then new ones."""
    ids = waiting()
    own = [case_id for case_id in ids if case_id in run.started]
    new = [case_id for case_id in ids if case_id not in run.started]
    return own + new[: run.cap - len(run.started)]


def queue_agent(llm: BaseChatModel, cap: int) -> QueueAgent:
    """Build the queue agent for a run, which keeps its conversation between turns."""
    calls = QUEUE_MODEL_CALLS_PER_CASE * cap + QUEUE_MODEL_CALLS_TO_PLAN
    middleware: list[AgentMiddleware[Any, Any]] = [
        ModelCallLimitMiddleware(run_limit=calls, exit_behavior="error"),
        ToolErrorMiddleware(lambda error, _: refusal(error)),
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


def run_queue(cap: int | None, llm: BaseChatModel, graph: CaseGraph) -> None:
    """Finish a run that stopped and carry on every case in progress, then work the
    queue with a queue agent, up to cap cases or every waiting case."""
    finish_stopped_run()
    carry_on_stopped(graph)
    count = len(waiting())
    if count == 0:
        log.info("No cases are waiting")
        return
    cap = min(cap or count, count)
    run_id = api.start_run(cap)["run_id"]
    run = RunContext(run_id, cap, partial(work_case, graph=graph))
    try:
        summary = work_queue(run, queue_agent(llm, cap))
    except Exception as error:
        api.finish_run(run_id, f"The run stopped: {describe(error)}")
        raise
    api.finish_run(run_id, summary)
    log.info(summary)
