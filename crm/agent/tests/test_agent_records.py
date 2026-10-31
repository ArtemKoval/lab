"""The case agent's decision records, as cases manual section 14 asks: who or
what made each decision, and the calculation of every approval's award."""

from typing import cast

from langchain_core.messages import ToolMessage
from langgraph.checkpoint.memory import InMemorySaver

from agent import api, checkpoints, harness
from agent.gateway import Gateway
from agent.tests.records import case_of
from agent.tests.stubs import (
    INSTRUCTIONS,
    agent_on,
    calculate,
    call,
    decide,
    flags,
    record,
    stub,
)
from agent.tools import record_decision
from backend.tests.dashboard_reads import steps_of

NO_OUTCOME = (
    "Cases manual section 14: an approval needs the outcome the pack resolved "
    "for this attempt. Work it out with resolve_outcome"
)


def test_the_case_agent_decides_as_its_version(client):
    harness.work_case("CLM-1003", None, agent_on(stub(*decide("refer", 0))))
    decision = case_of(client, "CLM-1003")["decision"]
    assert decision["decided_by"] == "CRM Agent, version 1"
    version_3 = {"number": 3, "instructions": INSTRUCTIONS}
    agent = agent_on(stub(*decide("decline", 0)), version=version_3)
    harness.work_case("CLM-1004", None, agent)
    decision = case_of(client, "CLM-1004")["decision"]
    assert decision["decided_by"] == "CRM Agent, version 3"


def test_a_runs_case_agents_decide_as_its_version(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(harness, "PostgresSaver", lambda pool: InMemorySaver())
    version = api.get_current_version() | {"number": 2}
    agent = harness.case_graphs(version, None, cast(checkpoints.Pool, None))()
    assert agent.decided_by == "CRM Agent, version 2"


def test_the_checks_referral_is_made_by_the_security_check(client):
    agent = agent_on(stub(), screener=flags())
    harness.work_case("CLM-1901", None, agent)
    decision = case_of(client, "CLM-1901")["decision"]
    assert decision["decided_by"] == "Security check"
    assert decision["manual_version"] == "2026.2"


def test_the_model_never_gives_the_maker():
    assert "decided_by" not in record_decision.args


def test_an_approval_with_no_calculation_goes_back_to_the_model(client):
    model = stub(
        call("get_case"),
        record("approve"),
        calculate("CLM-1001", 420.0),
        record("approve"),
    )
    assert harness.work_case("CLM-1001", None, agent_on(model)) == (
        "CLM-1001  approve  420.00 awarded"
    )
    refusal = model.prompts[2][-1]
    assert isinstance(refusal, ToolMessage)
    assert refusal.text == f"Refused with status 422: {NO_OUTCOME}"
    steps = [(s["kind"], s["content"]) for s in steps_of(client, "CLM-1001")]
    refused = steps.index(("refusal", f"record_decision: {refusal.text}"))
    # The refusal is followed by the model's next attempt at the record.
    after = [content for kind, content in steps[refused:] if kind == "tool_call"]
    assert after[0].startswith("resolve_outcome(")
    assert after[1].startswith('record_decision(decision="approve"')
    decisions = [c for k, c in steps if k == "tool_result" and "record_decision" in c]
    assert len(decisions) == 1
    case = case_of(client, "CLM-1001")
    assert case["decision"]["payload"]["award"] == 420.0
    assert case["effect"]["result"]["amount"] == 420.0


def test_the_gateway_receives_the_maker(client, gateway):
    model = stub(*decide("refer", 0))
    agent = agent_on(model, route=Gateway(gateway.url))
    harness.work_case("CLM-1003", None, agent)
    [recorded] = [c for c in gateway.calls if c.name.endswith("record_decision")]
    assert recorded.inputs["decided_by"] == "CRM Agent, version 1"
