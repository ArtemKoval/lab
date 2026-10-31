"""The OpsDesk pack's own tests, on the rules module, the protocol, and the
seeded queue."""

import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

PACK = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def in_the_opsdemo_domain():
    """Run with the pack active, and put the variable back after."""
    saved = os.environ.get("CRM_DOMAIN")
    os.environ["CRM_DOMAIN"] = "opsdemo"
    yield
    if saved is None:
        os.environ.pop("CRM_DOMAIN", None)
    else:
        os.environ["CRM_DOMAIN"] = saved


@pytest.fixture(scope="module")
def rules():
    spec = importlib.util.spec_from_file_location("opsdemo_rules", PACK / "rules.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def protocol():
    spec = importlib.util.spec_from_file_location(
        "opsdemo_protocol", PACK / "protocol.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def an_estimate(rules, hours_per_item, multiplier=1.5, capacity=40.0):
    """Drive work_out_award with dict-backed doubles of the engine models."""
    contract = SimpleNamespace(plan="priority")
    plans = SimpleNamespace(
        plans=[
            SimpleNamespace(
                plan="priority",
                response_target_hours=2,
                escalation_multiplier=multiplier,
                weekly_capacity=capacity,
            )
        ],
        deductible_applies_to=[],
    )
    request = SimpleNamespace(
        lines=[
            SimpleNamespace(description=f"Work item {n}", amount=hours, kind="item")
            for n, hours in enumerate(hours_per_item, start=1)
        ],
        paid_by_others=0,
        benefit="effort",
    )
    return rules.work_out_award(contract, plans, request, 16.0)


def test_the_pack_carries_the_schema_the_engine_needs():
    manifest = json.loads((PACK / "manifest.json").read_text())
    assert manifest["name"] == "opsdemo"
    assert manifest["engine_api"] == 2
    assert manifest["outcomes"] == {"effort": "resolve"}
    assert manifest["effects"]["effort"]["gated"] is True
    assert "records" not in manifest["effects"]["effort"]
    assert manifest["settings"]["award_approval_limit"] == 16.0
    cases = json.loads((PACK / "data" / "cases.json").read_text())
    assert len(cases) == 3
    for case in cases:
        assert case["status"] == "waiting"


def test_the_pack_is_never_about_money():
    """No money moves anywhere in the pack: the effect writes no payment, and
    the summary speaks of hours."""
    manifest = json.loads((PACK / "manifest.json").read_text())
    assert "records" not in manifest["effects"]["effort"]
    wording = (PACK / "policy" / "wording.md").read_text()
    assert "engineer-hours" in wording


def test_a_priority_estimate_carries_the_on_call_margin(rules):
    estimate = an_estimate(rules, [2.0, 4.0, 1.0])
    assert estimate.award == 10.5
    steps = [(entry.step, entry.amount) for entry in estimate.calculation]
    assert ("On-call margin, times 1.5", 3.5) in steps
    assert estimate.needs_sign_off is False


def test_an_estimate_caps_at_the_tier_capacity(rules):
    estimate = an_estimate(rules, [50.0])
    assert estimate.award == 40.0
    steps = [(entry.step, entry.amount) for entry in estimate.calculation]
    assert any("capacity" in step for step, _ in steps)


def test_an_estimate_over_the_limit_needs_the_lead(rules):
    estimate = an_estimate(rules, [2.0, 12.0])
    assert (estimate.award, estimate.needs_sign_off) == (21.0, True)


def test_a_standard_tier_adds_no_margin(rules):
    estimate = an_estimate(rules, [3.0], multiplier=1.0)
    assert estimate.award == 3.0


def test_the_effort_gate_asks_the_rules(protocol):
    assert protocol.gate({"award": 21.0}, {"approval_limit": 16.0}) is True
    assert protocol.gate({"award": 16.0}, {"approval_limit": 16.0}) is False


def test_the_escalation_record_moves_no_money(protocol):
    case = {"case_id": "ESC-5001", "customer_id": "CUS-5001", "award": 10.5}
    assert protocol.execute(case, {"award": 10.5}) == {
        "queue": "platform",
        "hours": 10.5,
    }


def test_the_summary_speaks_of_hours(protocol):
    assert protocol.summarize({"award": 10.5}) == "10.5 engineer-hours to escalate"


def test_the_metric_gives_the_hours(protocol):
    assert protocol.metric({"award": 10.5}) == 10.5


def test_resolve_estimates_through_the_rules(protocol):
    contract = SimpleNamespace(plan="priority")
    config = {
        "plans": SimpleNamespace(
            plans=[
                SimpleNamespace(
                    plan="priority",
                    response_target_hours=2,
                    escalation_multiplier=1.5,
                    weekly_capacity=40.0,
                )
            ],
            deductible_applies_to=[],
        ),
        "approval_limit": 16.0,
    }
    from backend.models import AwardRequest, Line

    request = AwardRequest(
        benefit="effort",
        lines=[Line(description="Escalate the fault", amount=4.0, quantity=1, kind="item", nights=0, hours=0)],
        paid_by_others=0,
    )
    estimate = protocol.resolve({"contract": contract}, config, request)
    assert (estimate.award, estimate.needs_sign_off) == (6.0, False)


@pytest.fixture
def client(tmp_path, monkeypatch):
    """The backend on a database seeded from this pack, called with the
    agent's key."""
    from fastapi.testclient import TestClient

    from backend.database import engine, seed
    from backend.dependencies import API_KEY_HEADER
    from backend.main import app

    monkeypatch.setenv("CRM_DB", str(tmp_path / "opsdemo.db"))
    seed(engine())
    with TestClient(app, headers={API_KEY_HEADER: "test-agent-key-0123456789abcdefghijklmnop"}) as caller:
        yield caller


def test_an_escalation_runs_its_effect_through_the_engine(client):
    """The whole engine path on the pack: start, resolve, approve, and run the
    effect, which lands in the platform queue and moves no money."""
    from backend.tests.case_requests import line, record_decision, resolve_outcome, start

    start(client, "ESC-5001")
    resolved = resolve_outcome(
        client,
        "ESC-5001",
        "effort",
        {
            "benefit": "effort",
            "lines": [
                line("Diagnose with the site lead", 2.0),
                line("Escalate to the platform team", 4.0),
            ],
            "paid_by_others": 0,
        },
    )
    assert resolved.status_code == 200
    case = client.get("/api/cases/ESC-5001").json()
    assert case["decision"] is None
    recorded = record_decision(client, "ESC-5001", decision="approve")
    assert recorded.status_code == 200
    run = client.post("/api/cases/ESC-5001/effects/effort")
    assert run.status_code == 200
    case = client.get("/api/cases/ESC-5001").json()
    assert (case["status"], case["effect"]["effect"]) == ("decided", "effort")
    assert set(case["effect"]["result"]) == {"queue", "hours"}
    assert case["effect"]["summary"] == "9 engineer-hours to escalate"
