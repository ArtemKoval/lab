"""The harness: it builds the case agent's graph and works a case with it."""

import contextvars
import json
import logging
import os
import time
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from functools import partial
from typing import Any, cast

from langchain.tools import ToolException
from langchain_core.exceptions import ModelRateLimitError, ModelTimeoutError
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
from agent.console import describe
from agent.tools import CASE_TOOLS, CaseContext, CaseState

log = logging.getLogger(__name__)

CaseGraph = CompiledStateGraph[CaseState, CaseContext, Any, Any]
NewGraph = Callable[[], CaseGraph]
Pool = ConnectionPool[Connection[DictRow]]
Messages = dict[str, list[BaseMessage]]
Start = Messages | Command | None

# The model's errors that pass with time: a case that hits one is left in progress,
# with its progress saved, to carry on later.
TRANSIENT = (ModelRateLimitError, ModelTimeoutError)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-6-luna"
SCHEMA = "crm"
CONNECTIONS = 4
CONNECTION_WAIT = 120
CASE_MODEL_CALLS = 30
NO_DECISION = "The agent finished without recording a decision"
WORK_CASE = "Work case"
CARRY_ON = "Carry on"
AGENT = "agent"
TOOLS = "tools"
PAUSE = "wait_for_sign_off"
PAY = "pay"


class TooManyModelCalls(Exception):
    """The case agent made as many model calls as it may without finishing."""


def model() -> ChatOpenAI:
    """Return the model named in MODEL_NAME, or GPT-6 Luna by default."""
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
def checkpoint_pool() -> Iterator[Pool]:
    """Open the process's pool of at most CONNECTIONS connections to DATABASE_URL,
    where case graphs save their progress in our own schema, set up once. A case
    agent waits up to CONNECTION_WAIT seconds for a connection."""
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
        timeout=CONNECTION_WAIT,
        kwargs=settings,
    ) as pool:
        with pool.connection() as connection:
            create = sql.SQL("CREATE SCHEMA IF NOT EXISTS {}")
            connection.execute(create.format(sql.Identifier(SCHEMA)))
        PostgresSaver(pool).setup()
        yield pool


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


def record_call(context: CaseContext, reply: BaseMessage) -> None:
    """Record the tokens and the cost of one model call, as OpenRouter reports them."""
    usage = reply.response_metadata["token_usage"]
    api.record_model_call(
        context.case_id,
        context.run_id,
        usage["prompt_tokens"],
        usage["completion_tokens"],
        usage["cost"],
    )


def call_model(
    state: CaseState,
    runtime: Runtime[CaseContext],
    llm: Runnable[LanguageModelInput, BaseMessage],
    instructions: SystemMessage,
) -> dict[str, Any]:
    """Ask the model for its next step, up to CASE_MODEL_CALLS times in all, and
    record its cost and its reply on the case."""
    calls = state["model_calls"]
    if calls >= CASE_MODEL_CALLS:
        message = f"The case agent made {calls} model calls without finishing"
        raise TooManyModelCalls(message)
    reply = llm.invoke([instructions, *state["messages"]])
    record_call(runtime.context, reply)
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


def case_graphs(llm: BaseChatModel, pool: Pool) -> NewGraph:
    """Return how to build a case graph with a saver of its own on the pool, since
    a saver lets one case at a time read or write."""

    def new_graph() -> CaseGraph:
        return case_graph(llm, PostgresSaver(pool))

    return new_graph


def thread_of(case: dict[str, Any]) -> RunnableConfig:
    """Address the case's thread, where the case graph saves its progress."""
    return {"configurable": {"thread_id": case["thread_id"]}}


def case_config(case: dict[str, Any], name: str, run_id: str | None) -> RunnableConfig:
    """Run on the case's thread, traced in Langfuse in the session of that thread
    and tagged with the run, if any."""
    session = f"{case['case_id']}:{case['thread_id']}"
    metadata: dict[str, Any] = {
        "langfuse_session_id": session,
        "langfuse_trace_name": name,
    }
    if run_id is not None:
        metadata["langfuse_tags"] = [run_id]
    return thread_of(case) | {
        "callbacks": [CallbackHandler()],
        "metadata": metadata,
        # One tool call at a time, so two decisions in one reply can't race.
        "max_concurrency": 1,
    }


def begin(case_id: str) -> Messages:
    """Give a case agent its first message, naming the case it works on."""
    return {"messages": [HumanMessage(f"Case {case_id}")]}


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
    graph: CaseGraph,
    start: Start,
    case: dict[str, Any],
    name: str,
    run_id: str | None,
) -> str | None:
    """Run the case graph on the case's thread, saving each step, and say what went
    wrong, if anything. A rate limit or a timeout is raised again, leaving the case
    in progress with its progress saved, to carry on later."""
    try:
        # A fresh context makes this a root run even inside the dispatcher, which
        # Langfuse needs to put it in the case's session.
        contextvars.Context().run(
            graph.invoke,
            start,
            case_config(case, name, run_id),
            context=CaseContext(case["case_id"], run_id),
            durability="sync",
        )
    except TRANSIENT:
        raise
    except Exception as error:  # a case that fails must not stop the run
        return describe(error)
    return None


@contextmanager
def spell(case_id: str, run_id: str | None) -> Iterator[None]:
    """Time one spell of work on a case, and record it however it ends."""
    started = time.monotonic()
    try:
        yield
    finally:
        api.record_work_time(case_id, run_id, time.monotonic() - started)


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


def work_case(case_id: str, run_id: str | None, graph: CaseGraph) -> str:
    """Work one case from a clean start, as a new attempt, in the run given if any,
    and report how it ended."""
    case = api.start_case(case_id, str(uuid.uuid4()))
    with spell(case_id, run_id):
        error = run_case_graph(graph, begin(case_id), case, WORK_CASE, run_id)
        return settle(case_id, error)


def carry_on(case_id: str, run_id: str | None, graph: CaseGraph) -> str:
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
    with spell(case_id, run_id):
        error = run_case_graph(graph, start, case, CARRY_ON, run_id)
        return settle(case_id, error)


def work_in_run(case_id: str, run_id: str, new_graph: NewGraph) -> str:
    """Work one case in a run on a case graph of its own, carrying it on if it is
    in progress or starting it if it is waiting, and report how it ended. A copy in
    an evaluation held for sign-off is finished."""
    graph = new_graph()
    if api.get_case(case_id)["status"] == api.Status.IN_PROGRESS:
        line = carry_on(case_id, run_id, graph)
    else:
        line = work_case(case_id, run_id, graph)
    finish_held_copy(case_id, graph)
    return line


def finish_held_copy(case_id: str, graph: CaseGraph) -> None:
    """Clear the saved progress of an evaluation's copy held for sign-off: nobody
    can sign a copy off, so its work is finished."""
    case = api.get_case(case_id)
    held = case["status"] == api.Status.WAITING_FOR_SIGN_OFF
    if case["evaluation_id"] and held:
        # case_graph always compiles the graph with a saver.
        saver = cast(BaseCheckpointSaver[Any], graph.checkpointer)
        saver.delete_thread(case["thread_id"])
