"""The Northgate pack's rules: the loan term arithmetic and the sign-off
question, on dict-backed doubles of the engine models."""

from types import SimpleNamespace

from domains.library import rules


def load_rules():
    return rules


def a_request(nights):
    """One approved request of one line, whose nights carry the days."""
    return SimpleNamespace(
        benefit="loan",
        paid_by_others=0,
        lines=[
            SimpleNamespace(
                description="The Lighthouse Keeper",
                amount=24.0,
                quantity=1,
                kind="item",
                nights=nights,
                hours=0,
            )
        ],
    )


def tier(plan, base, cap):
    return SimpleNamespace(
        plan=plan,
        name=f"Northgate {plan.title()}",
        base_loan_days=base,
        max_loan_days=cap,
    )


PLANS = SimpleNamespace(
    plans=[tier("standard", 14, 14), tier("research", 14, 28)],
    deductible_applies_to=[],
    add_ons=[],
)


def a_membership(plan):
    return SimpleNamespace(plan=plan)


def test_a_standard_checkout_holds_14_days():
    award = load_rules().work_out_award(
        a_membership("standard"), PLANS, a_request(14), 14.0
    )
    assert award.award == 14.0
    steps = [(entry.step, entry.amount) for entry in award.calculation]
    assert any("standard" in step and "base" in step.lower() for step, _ in steps)
    assert award.needs_sign_off is False


def test_a_research_renewal_over_the_limit_needs_sign_off():
    rules = load_rules()
    award = rules.work_out_award(a_membership("research"), PLANS, a_request(21), 14.0)
    assert award.award == 21.0
    steps = [(entry.step, entry.amount) for entry in award.calculation]
    assert ("Renewal, 7 days past the base term", 7.0) in steps
    assert award.needs_sign_off is True


def test_a_term_over_the_tier_cap_is_truncated():
    award = load_rules().work_out_award(
        a_membership("research"), PLANS, a_request(35), 14.0
    )
    assert award.award == 28.0
    steps = [(entry.step, entry.amount) for entry in award.calculation]
    assert (
        "Less the days over the research term cap of 28 days",
        -7.0,
    ) in steps


def test_an_exact_base_request_adds_no_renewal_step():
    rules = load_rules()
    award = rules.work_out_award(a_membership("standard"), PLANS, a_request(14), 14.0)
    steps = [(entry.step, entry.amount) for entry in award.calculation]
    assert steps == [("Base term of the standard plan, 14 days", 14.0)]
    assert award.award == 14.0


def test_a_one_day_renewal_is_added():
    rules = load_rules()
    award = rules.work_out_award(a_membership("research"), PLANS, a_request(15), 14.0)
    steps = [(entry.step, entry.amount) for entry in award.calculation]
    assert ("Renewal, 1 days past the base term", 1.0) in steps
    assert award.award == 15.0


def test_an_exact_cap_renewal_adds_no_cap_step():
    rules = load_rules()
    award = rules.work_out_award(a_membership("research"), PLANS, a_request(28), 14.0)
    steps = [(entry.step, entry.amount) for entry in award.calculation]
    assert steps == [
        ("Base term of the research plan, 14 days", 14.0),
        ("Renewal, 14 days past the base term", 14.0),
    ]
    assert award.award == 28.0


def test_a_zero_day_tier_awards_zero_days():
    """The term never drops below zero, and a tier with no days grants none."""
    rules = load_rules()
    plans = SimpleNamespace(
        plans=[tier("closed", 0, 0)], deductible_applies_to=[], add_ons=[]
    )
    award = rules.work_out_award(a_membership("closed"), plans, a_request(0), 14.0)
    assert award.award == 0.0


def test_needs_sign_off_asks_at_the_limit():
    rules = load_rules()
    assert rules.needs_sign_off(21.0, 14.0) is True
    assert rules.needs_sign_off(14.0, 14.0) is False
    assert rules.needs_sign_off(7.0, 14.0) is False
