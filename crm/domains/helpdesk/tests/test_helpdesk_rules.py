"""The helpdesk pack's own tests, on the rules module and the seeded queue."""

import importlib.util
import json
import os
from pathlib import Path

import pytest

PACK = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def in_the_helpdesk_domain():
    """Run with the pack active, and put the variable back after."""
    saved = os.environ.get("CRM_DOMAIN")
    os.environ["CRM_DOMAIN"] = "helpdesk"
    yield
    if saved is None:
        os.environ.pop("CRM_DOMAIN", None)
    else:
        os.environ["CRM_DOMAIN"] = saved


@pytest.fixture(scope="module")
def rules():
    spec = importlib.util.spec_from_file_location(
        "helpdesk_rules", PACK / "rules.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def limits(rules):
    return rules.Limits(per_incident_cap=150.0, multiplier=1.5)


def credit_for(rules, limits, amount):
    """A credit for one outage line, with the pack's plan limits."""
    request = {"lines": [{"description": "Outage hour", "amount": amount}]}
    lines = [rules.step(line["description"], line["amount"])]
    total = sum(s.amount for s in lines)
    total = rules.apply_priority_multiplier(lines, total, limits)
    total = rules.cap_at_per_incident(lines, total, limits)
    return rules.Award(
        calculation=lines,
        award=round(total, 2),
        needs_sign_off=rules.needs_sign_off(round(total, 2), 200.0),
    )


def use_award(rules, limits, amount):
    """Drive the contract entry point the engine calls, with tiny doubles."""
    contract = {"plan": "priority"}
    plans = {"plans": [{"plan": "priority", "per_incident_cap": limits.per_incident_cap, "priority_multiplier": limits.multiplier}], "deductible_applies_to": []}
    request = {"lines": [{"description": "Outage hour", "amount": amount}], "paid_by_others": 0}
    return rules.work_out_award(contract, plans, request, 200.0)


def work_out_award_from_dicts(rules, limits, amount):
    """Call work_out_award with dict-backed doubles of the engine models."""
    from types import SimpleNamespace

    contract = SimpleNamespace(plan="priority")
    plans = SimpleNamespace(
        plans=[
            SimpleNamespace(
                plan="priority",
                per_incident_cap=limits.per_incident_cap,
                priority_multiplier=limits.multiplier,
            )
        ],
        deductible_applies_to=[],
    )
    request = SimpleNamespace(
        lines=[SimpleNamespace(description="Outage hour", amount=amount, kind="item")],
        paid_by_others=0,
        benefit="outage",
    )
    return rules.work_out_award(contract, plans, request, 200.0)


def test_the_pack_carries_the_schema_the_engine_needs():
    manifest = json.loads((PACK / "manifest.json").read_text())
    assert manifest["name"] == "helpdesk"
    assert manifest["settings"]["award_approval_limit"] == 200.0
    cases = json.loads((PACK / "data" / "cases.json").read_text())
    assert len(cases) == 3
    for case in cases:
        assert case["status"] == "waiting"


def test_a_priority_credit_is_multiplied(rules, limits):
    credit = work_out_award_from_dicts(rules, limits, 90.0)
    assert credit.award == 135.0
    assert credit.needs_sign_off is False


def test_a_standard_credit_is_capped_at_the_per_incident_cap(rules):
    credit = work_out_award_from_dicts(
        rules, rules.Limits(150.0, 1.0), 300.0
    )
    assert credit.award == 150.0


def test_an_over_limit_credit_needs_the_lead(rules):
    """A plan without a per-incident cap lets a credit reach the lead's gate."""
    credit = work_out_award_from_dicts(
        rules, rules.Limits(per_incident_cap=10000.0, multiplier=1.5), 500.0
    )
    assert credit.award == 750.0
    assert credit.needs_sign_off is True


def test_the_priority_multiplier_applies_only_above_zero(rules, limits):
    credit = work_out_award_from_dicts(rules, limits, 0.0)
    assert credit.award == 0.0
