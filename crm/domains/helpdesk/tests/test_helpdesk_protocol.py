"""The helpdesk pack's protocol: the four verbs, on the pack's own rules."""

import importlib.util
from pathlib import Path

import pytest

PACK = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def protocol():
    spec = importlib.util.spec_from_file_location(
        "helpdesk_protocol", PACK / "protocol.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_credit_gate_asks_the_rules(protocol):
    assert protocol.gate({"award": 250.0}, {"approval_limit": 200.0}) is True
    assert protocol.gate({"award": 200.0}, {"approval_limit": 200.0}) is False


def test_the_credit_issue_record_carries_the_amount(protocol):
    assert protocol.execute({"award": 135.0}, None) == {"amount": 135.0}


def test_the_summary_says_the_credit(protocol):
    assert protocol.summarize({"award": 135.0}) == "135.00 of service credit issued"


def test_resolve_works_the_credit_through_the_rules(protocol):
    from types import SimpleNamespace

    from backend.models import AwardRequest, Line

    case = {"contract": SimpleNamespace(plan="priority")}
    config = {
        "plans": SimpleNamespace(
            plans=[
                SimpleNamespace(
                    plan="priority", per_incident_cap=150.0, priority_multiplier=1.5
                )
            ],
            deductible_applies_to=[],
        ),
        "approval_limit": 200.0,
    }
    request = AwardRequest(
        benefit="outage",
        lines=[
            Line(
                description="Outage hour",
                amount=90.0,
                quantity=1,
                kind="item",
                nights=0,
                hours=0,
            )
        ],
        paid_by_others=0,
    )
    credit = protocol.resolve(case, config, request)
    assert (credit.award, credit.needs_sign_off) == (135.0, False)
