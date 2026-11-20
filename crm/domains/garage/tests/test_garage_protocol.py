"""The AutoFix pack's protocol: the five verbs the engine calls."""

from types import SimpleNamespace

from domains.garage import protocol, rules


def a_case():
    return {
        "contract": SimpleNamespace(plan="standard"),
        "record": {"case_id": "JOB-1001", "items": []},
    }


CONFIG = {
    "plans": SimpleNamespace(
        plans=[
            SimpleNamespace(
                plan="standard", name="AutoFix Standard Care",
                base_excess=25.0, per_repair_cap=500.0,
            )
        ],
        deductible_applies_to=[],
        add_ons=[],
    ),
    "approval_limit": 600.0,
}


def a_request(amounts):
    return SimpleNamespace(
        benefit="repair",
        paid_by_others=0,
        lines=[
            SimpleNamespace(
                description="Fault line", amount=amount, quantity=1,
                kind="item", nights=0, hours=0,
            )
            for amount in amounts
        ],
    )


def test_resolve_returns_the_rules_award():
    outcome = protocol.resolve(a_case(), CONFIG, a_request([180.0, 120.0]))
    expected = rules.work_out_award(
        a_case()["contract"], CONFIG["plans"], a_request([180.0, 120.0]), 600.0
    )
    assert outcome.award == expected.award
    assert outcome.needs_sign_off == expected.needs_sign_off


def test_gate_asks_the_sign_off_question():
    assert protocol.gate({"award": 720.0}, CONFIG) is True
    assert protocol.gate({"award": 275.0}, CONFIG) is False


def test_execute_names_the_case_and_the_amount():
    record = protocol.execute(
        {"record": {"case_id": "JOB-1001"}}, {"award": 275.0}
    )
    assert record == {"case_id": "JOB-1001", "amount": 275.0}


def test_summarize_names_the_authorization():
    line = protocol.summarize({"award": 275.0})
    assert "275" in line
    assert "authoriz" in line


def test_metric_reads_the_amount():
    assert protocol.metric({"award": 275.0}) == 275.0
