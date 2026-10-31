import itertools
import json
import logging

import pytest
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver

from agent import api, harness
from agent.connection import Refused
from agent.tests.records import case_of
from agent.tests.stubs import (
    INSTRUCTIONS,
    PASSED,
    StubModel,
    agent_on,
    approve,
    calculate,
    call,
    decide,
    record,
    stub,
)
from backend.tests.dashboard_reads import steps_of
from backend.tests.settings_requests import change_settings


def work(case_id, model, saver=None):
    return harness.work_case(case_id, None, agent_on(model, saver))


def test_the_graph():
    graph = agent_on(stub()).graph.get_graph()
    assert set(graph.nodes) == {
        "__start__",
        "screen",
        "refer",
        "agent",
        "tools",
        "pay",
        "wait_for_worker",
        "__end__",
    }
    edges = {(e.source, e.target, e.conditional) for e in graph.edges}
    assert edges == {
        ("__start__", "screen", False),
        ("screen", "refer", True),
        ("screen", "agent", True),
        ("refer", "__end__", False),
        ("agent", "tools", True),
        ("agent", "__end__", True),
        ("tools", "agent", True),
        ("tools", "pay", True),
        ("tools", "wait_for_worker", True),
        ("tools", "__end__", True),
        ("pay", "wait_for_worker", True),
        ("pay", "__end__", True),
        ("wait_for_worker", "agent", True),
        ("wait_for_worker", "__end__", True),
    }


def test_an_evaluations_graph_has_no_pause():
    graph = agent_on(stub(), pauses=False).graph.get_graph()
    assert "wait_for_worker" not in graph.nodes
    edges = {(e.source, e.target) for e in graph.edges}
    assert {("tools", "__end__"), ("pay", "__end__")} <= edges


def test_approves_and_the_graph_pays_within_the_limit(client, caplog):
    caplog.set_level(logging.INFO, logger="agent")
    model = stub(
        call("get_case"),
        call("get_contract", contract_id="POL-2001"),
        call("get_case_history", customer_id="CUS-3001"),
        calculate("CLM-1001", 420.0),
        record("approve", 420.0),
    )
    assert work("CLM-1001", model) == "CLM-1001  approve  $420.00"
    assert caplog.messages == ["CLM-1001  approve  $420.00"]
    assert len(model.prompts) == 5

    case = case_of(client, "CLM-1001")
    assert case["status"] == "decided"
    assert case["attempts"] == 1
    assert case["decision"]["award"] == 420.0
    assert case["effect"]["result"]["amount"] == 420.0
    assert len(case["thread_id"]) == 36

    check, *steps = steps_of(client, "CLM-1001")
    assert (check["kind"], check["content"]) == (
        "screening",
        f"No instructions found. {PASSED}",
    )
    assert [s["kind"] for s in steps] == ["tool_call", "tool_result"] * 5
    assert steps[0]["content"] == "get_case()"
    assert steps[1]["content"].startswith('get_case: {"case_id": "CLM-1001"')
    assert steps[6]["content"].startswith("calculate_award(")
    assert steps[8]["content"].startswith("record_decision(")
    assert steps[9]["content"].startswith('record_decision: {"case_id": "CLM-1001"')
    assert "pay_case" not in "".join(s["content"] for s in steps)
    assert {s["thread_id"] for s in [check, *steps]} == {case["thread_id"]}


def test_the_case_agent_reads_its_instructions_then_its_case(client):
    model = stub(*decide("refer", 0))
    work("CLM-1003", model)
    system, first = model.prompts[0]
    assert isinstance(system, SystemMessage)
    assert system.content == INSTRUCTIONS
    assert first.content == "Case CLM-1003"


def test_the_graph_follows_the_backend_on_the_limit(client):
    change_settings(client, approval_limit=2000.0)
    report = work("CLM-1002", stub(*approve("CLM-1002", 1350.0)))
    assert report == "CLM-1002  approve  $1,350.00"
    assert case_of(client, "CLM-1002")["effect"]["result"]["amount"] == 1350.0


@pytest.mark.parametrize("decision", ["decline", "refer"])
def test_declines_and_refers(client, decision):
    agent = agent_on(stub(*decide(decision, 0)))
    report = harness.work_case("CLM-1003", None, agent)
    assert report == f"CLM-1003  {decision}  $0.00"
    case = case_of(client, "CLM-1003")
    assert (case["status"], case["effect"]) == ("decided", None)
    history = agent.graph.get_state_history(harness.thread_of(case))
    assert harness.PAY not in {node for snapshot in history for node in snapshot.next}


def test_two_decisions_in_one_reply_are_recorded_and_paid_once(client):
    twice = [record("approve", 420.0).tool_calls[0] for _ in range(2)]
    model = stub(calculate("CLM-1001", 420.0), AIMessage(content="", tool_calls=twice))
    assert work("CLM-1001", model) == "CLM-1001  approve  $420.00"
    case = case_of(client, "CLM-1001")
    assert (case["status"], case["effect"]["result"]["amount"]) == ("decided", 420.0)
    results = [
        s
        for s in steps_of(client, "CLM-1001")
        if s["kind"] == "tool_result" and s["content"].startswith("record_decision")
    ]
    assert len(results) == 2


def test_a_refused_decision_goes_back_to_the_model(client):
    model = stub(
        record("approve", 0), calculate("CLM-1001", 420.0), record("approve", 420.0)
    )
    assert work("CLM-1001", model) == "CLM-1001  approve  $420.00"
    refusal = model.prompts[1][-1]
    assert isinstance(refusal, ToolMessage)
    assert refusal.text.startswith("Refused with status 422: ")
    assert case_of(client, "CLM-1001")["effect"]["result"]["amount"] == 420.0


def test_a_section_read_is_recorded_as_a_lookup(client):
    model = stub(
        call("read_section", document="manual", number=9),
        call("read_section", document="manual", number=15),
        call("search_documents", query="wild animal"),
        *decide("refer", 0),
    )
    work("CLM-1004", model)

    _, *steps = [(s["kind"], s["content"]) for s in steps_of(client, "CLM-1004")]
    assert steps[0] == (
        "tool_call",
        'read_section(document="manual", number=9)',
    )
    assert steps[1][1].startswith('read_section: {"document": "manual"')
    assert steps[2] == ("lookup", "Cases manual, section 9: Repeat claims")
    assert steps[4] == (
        "refusal",
        "read_section: Refused: Error executing tool read_section: "
        "Section 15 of the cases manual not found",
    )
    assert steps[5] == ("tool_call", 'search_documents(query="wild animal")')
    assert steps[6][1].startswith(
        'search_documents: {"sections": [{"document": "manual"'
    )
    assert [s for s in steps if s[0] == "lookup"] == [
        steps[2],
        ("lookup", 'Documents: "wild animal"'),
    ]


def test_a_section_with_bad_arguments_goes_back_to_the_model(client):
    model = stub(
        call("read_section", document="handbook", number=1), *decide("refer", 0)
    )
    assert work("CLM-1004", model) == "CLM-1004  refer  $0.00"
    assert "lookup" not in {s["kind"] for s in steps_of(client, "CLM-1004")}


def test_working_out_the_award(client):
    lines = [
        {
            "description": "Hotel",
            "amount": 245,
            "quantity": 1,
            "kind": "hotel",
            "nights": 1,
            "hours": 0,
        },
        {
            "description": "Meals",
            "amount": 95,
            "quantity": 1,
            "kind": "expense",
            "nights": 0,
            "hours": 0,
        },
        {
            "description": "Taxis",
            "amount": 80,
            "quantity": 1,
            "kind": "expense",
            "nights": 0,
            "hours": 0,
        },
    ]
    model = stub(
        call("calculate_award", benefit="trip_delay", lines=lines, paid_by_others=0),
        record("approve", 420.0),
    )
    assert work("CLM-1001", model) == "CLM-1001  approve  $420.00"
    # After the check's step and the call.
    result = steps_of(client, "CLM-1001")[2]
    assert result["kind"] == "tool_result"
    content = result["content"].removeprefix("calculate_award: ")
    assert json.loads(content)["award"] == 420.0


def test_a_case_is_traced_in_the_session_of_its_thread(client, traces):
    work("CLM-1001", stub(*decide("refer", 0)))
    thread_id = case_of(client, "CLM-1001")["thread_id"]
    assert [(t["langfuse_session_id"], t["langfuse_trace_name"]) for t in traces] == [
        (f"CLM-1001:{thread_id}", "Work case")
    ]


def test_working_a_case_saves_each_step_on_its_thread(client, monkeypatch):
    agent = agent_on(stub(*decide("refer", 0)))
    runs = []
    invoke = agent.graph.invoke

    def spy(start, config, **kwargs):
        runs.append((config, kwargs))
        return invoke(start, config, **kwargs)

    monkeypatch.setattr(agent.graph, "invoke", spy)
    harness.work_case("CLM-1003", None, agent)
    [(config, kwargs)] = runs
    assert kwargs["durability"] == "sync"
    thread_id = case_of(client, "CLM-1003")["thread_id"]
    assert config["configurable"]["thread_id"] == thread_id


def test_a_provider_error_puts_the_case_back_in_the_queue(client):
    outage = RuntimeError("503: The model is unavailable")
    saver = InMemorySaver()
    report = work("CLM-1004", stub(call("get_case"), outage), saver)
    assert report == (
        "CLM-1004  failed: RuntimeError: 503: The model is unavailable,"
        " back in the queue"
    )
    case = case_of(client, "CLM-1004")
    assert (case["status"], case["attempts"]) == ("waiting", 1)
    last = steps_of(client, "CLM-1004")[-1]
    assert (last["kind"], last["content"]) == (
        "error",
        "RuntimeError: 503: The model is unavailable",
    )

    model = stub(outage)
    again = work("CLM-1004", model, saver)
    assert again.endswith(", left for a worker")
    retried = case_of(client, "CLM-1004")
    assert (retried["status"], retried["attempts"]) == ("left_for_worker", 2)
    assert retried["thread_id"] != case["thread_id"]
    assert [m.content for m in model.prompts[0][1:]] == ["Case CLM-1004"]


def test_a_tool_that_breaks_stops_the_agent_rather_than_telling_the_model(
    client, monkeypatch
):
    def broken(contract_id):
        raise RuntimeError("The backend is unreachable")

    monkeypatch.setattr(api, "get_contract", broken)
    model = stub(call("get_contract", contract_id="POL-2001"), *decide("refer", 0))
    report = work("CLM-1001", model)
    assert report == (
        "CLM-1001  failed: RuntimeError: The backend is unreachable, back in the queue"
    )
    assert len(model.prompts) == 1


def test_finishing_without_a_decision_is_a_failure(client):
    model = stub(call("get_case"), AIMessage(content="Hmm."))
    assert work("CLM-1004", model) == (
        "CLM-1004  failed: The agent finished without recording a decision,"
        " back in the queue"
    )


def test_a_case_agent_going_round_in_circles_stops(client):
    model = StubModel(messages=(call("get_case") for _ in itertools.count()))
    report = work("CLM-1004", model)
    assert report == (
        "CLM-1004  failed: TooManyModelCalls: The case agent made 30 model calls"
        " without finishing, back in the queue"
    )
    assert len(model.prompts) == harness.CASE_MODEL_CALLS
    assert case_of(client, "CLM-1004")["status"] == "waiting"


def test_a_failure_after_the_decision_keeps_it(client, monkeypatch, caplog):
    def lost(case_id, effect):
        raise RuntimeError("The connection was lost")

    monkeypatch.setattr(api, "run_effect", lost)
    report = work("CLM-1001", stub(*approve("CLM-1001", 420.0)))
    assert report == "CLM-1001  approve  $420.00, not paid yet"
    assert "CLM-1001  RuntimeError: The connection was lost" in caplog.messages
    case = case_of(client, "CLM-1001")
    assert (case["status"], case["attempts"]) == ("in_progress", 1)
    assert case["decision"]["award"] == 420.0
    assert "error" not in {s["kind"] for s in steps_of(client, "CLM-1001")}


def test_a_case_that_isnt_waiting_is_not_started(client):
    work("CLM-1003", stub(*decide("refer", 0)))
    before = steps_of(client, "CLM-1003")
    with pytest.raises(Refused, match="^409: Case CLM-1003 is not waiting$"):
        work("CLM-1003", stub())
    assert steps_of(client, "CLM-1003") == before
    assert case_of(client, "CLM-1003")["attempts"] == 1


def test_each_case_starts_clean(client):
    model = stub(*decide("decline", 0), *decide("refer", 0))
    agent = agent_on(model)
    harness.work_case("CLM-1001", None, agent)
    harness.work_case("CLM-1003", None, agent)
    firsts = [prompt for prompt in model.prompts if len(prompt) == 2]
    assert [prompt[1].content for prompt in firsts] == [
        "Case CLM-1001",
        "Case CLM-1003",
    ]
    assert firsts[0][0] == firsts[1][0]
    decided = [case_of(client, i) for i in ("CLM-1001", "CLM-1003")]
    assert [c["decision"]["decision"] for c in decided] == ["decline", "refer"]
    assert decided[0]["thread_id"] != decided[1]["thread_id"]
