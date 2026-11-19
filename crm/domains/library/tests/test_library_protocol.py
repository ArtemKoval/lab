"""The Northgate pack's protocol: the five verbs the engine calls."""

from types import SimpleNamespace

from domains.library import protocol


def load_protocol():
    return protocol


CONFIG = {
    "plans": SimpleNamespace(
        plans=[
            SimpleNamespace(
                plan="research", name="Northgate Research", base_loan_days=14, max_loan_days=28
            )
        ],
        deductible_applies_to=[],
        add_ons=[],
    ),
    "approval_limit": 14.0,
}

A_REQUEST = SimpleNamespace(
    benefit="loan",
    paid_by_others=0,
    lines=[
        SimpleNamespace(
            description="The Lighthouse Keeper",
            amount=24.0,
            quantity=1,
            kind="item",
            nights=21,
            hours=0,
        )
    ],
)


def test_resolve_returns_the_rules_award():
    protocol = load_protocol()
    case = {"contract": SimpleNamespace(plan="research")}
    award = protocol.resolve(case, CONFIG, A_REQUEST)
    assert award.award == 21.0


def test_gate_asks_the_sign_off_question():
    protocol = load_protocol()
    assert protocol.gate({"award": 21.0}, {"approval_limit": 14.0}) is True
    assert protocol.gate({"award": 14.0}, {"approval_limit": 14.0}) is False


def test_the_loan_record_names_the_copy_and_the_days():
    protocol = load_protocol()
    case = {"record": {"items": [{"description": "The Lighthouse Keeper"}]}}
    assert protocol.execute(case, {"award": 14.0}) == {
        "title": "The Lighthouse Keeper",
        "days": 14.0,
    }


def test_the_worker_line_names_the_days():
    assert load_protocol().summarize({"award": 14.0}) == "14-day loan issued"


def test_the_metric_reads_the_days():
    assert load_protocol().metric({"award": 14.0}) == 14.0
