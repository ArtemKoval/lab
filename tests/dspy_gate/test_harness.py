"""Tests for the pilot triage harness and the module registry: the
four specimen behaviors, the registry opt-in contract, and the run
resolution through the manifest case."""

from dspy_gate import harness
from dspy_gate.harness import registry, triage


def test_outage_keywords_route_to_on_call():
    pred, trace = triage.triage("production down, urgent")
    assert pred["severity"] == "P0"
    assert pred["team"] == "on-call"


def test_data_loss_routes_to_on_call():
    pred, _ = triage.triage("we see data loss in the export")
    assert pred["severity"] == "P0"
    assert pred["team"] == "on-call"


def test_billing_terms_route_to_billing():
    pred, _ = triage.triage("refund request for the June invoice charge")
    assert pred["team"] == "billing"
    assert pred["severity"] in ("P1", "P2", "P3")


def test_general_tickets_route_to_general():
    pred, _ = triage.triage("how do I rename my workspace")
    assert pred["team"] == "general"
    assert pred["severity"] in ("P1", "P2", "P3")


def test_a_p0_ticket_escalates_before_the_reply_step():
    _, trace = triage.triage("production down")
    tools = [entry.get("tool") or entry.get("step") for entry in trace]
    assert tools.index("escalate") < tools.index("reply")


def test_the_registry_declares_the_pilot_capability():
    modules = registry.modules()
    assert "ticket-triage" in modules
    entry = modules["ticket-triage"]
    assert entry["impl"] == "hand"
    assert entry["module"] == "Triage"
    assert entry["entry"].endswith("harness.triage::triage")


def test_run_resolves_a_case_through_the_registry():
    case = {"capability": "ticket-triage", "scenario_id": "outage-keywords-route-to-on-call"}
    pred, trace = harness.run(case, registry.modules())
    assert pred["severity"] == "P0"
    assert isinstance(trace, list)


def test_run_refuses_an_unknown_capability():
    case = {"capability": "ghost-cap", "scenario_id": "x"}
    try:
        harness.run(case, registry.modules())
    except KeyError as exc:
        assert "ghost-cap" in str(exc)
    else:
        raise AssertionError("expected KeyError")


def test_run_carries_the_registry_example_inputs():
    modules = registry.modules()
    entry = modules["ticket-triage"]
    assert "outage-keywords-route-to-on-call" in entry["examples"]
