"""The AutoFix pack's rules: the authorization arithmetic and the
sign-off question, on dict-backed doubles of the engine models."""

from types import SimpleNamespace

from domains.garage import rules


def a_request(amounts):
    """One approved request of fault lines, whose amounts carry estimates."""
    return SimpleNamespace(
        benefit="repair",
        paid_by_others=0,
        lines=[
            SimpleNamespace(
                description=f"Fault line {index}",
                amount=amount,
                quantity=1,
                kind="item",
                nights=0,
                hours=0,
            )
            for index, amount in enumerate(amounts)
        ],
    )


def tier(plan, excess, cap):
    return SimpleNamespace(
        plan=plan,
        name=f"AutoFix {plan.title()} Care",
        base_excess=excess,
        per_repair_cap=cap,
    )


PLANS = SimpleNamespace(
    plans=[tier("standard", 25.0, 500.0), tier("ev", 0.0, 400.0), tier("fleet", 0.0, 900.0)],
    deductible_applies_to=[],
    add_ons=[],
)


def an_agreement(plan):
    return SimpleNamespace(plan=plan)


def steps_of(award):
    return [(entry.step, entry.amount) for entry in award.calculation]


def test_a_covered_repair_subtracts_the_excess_once():
    award = rules.work_out_award(
        an_agreement("standard"), PLANS, a_request([180.0, 120.0]), 600.0
    )
    assert award.award == 275.0
    steps = steps_of(award)
    assert any("base excess" in step and "standard" in step for step, _ in steps)
    assert award.needs_sign_off is False


def test_a_repair_past_the_cap_is_truncated():
    award = rules.work_out_award(
        an_agreement("standard"), PLANS, a_request([640.0]), 600.0
    )
    assert award.award == 500.0
    steps = steps_of(award)
    assert any("base excess" in step for step, _ in steps)
    assert any("cap of 500" in step for step, _ in steps)


def test_an_ev_repair_caps_at_the_ev_cap():
    award = rules.work_out_award(an_agreement("ev"), PLANS, a_request([520.0]), 600.0)
    assert award.award == 400.0


def test_a_fleet_repair_over_the_limit_needs_sign_off():
    award = rules.work_out_award(
        an_agreement("fleet"), PLANS, a_request([720.0]), 600.0
    )
    assert award.award == 720.0
    assert award.needs_sign_off is True


def test_a_total_under_the_excess_floors_at_zero():
    award = rules.work_out_award(
        an_agreement("standard"), PLANS, a_request([15.0]), 600.0
    )
    assert award.award == 0.0
    assert any("Nothing is left" in step for step, _ in steps_of(award))


def test_a_plan_without_an_excess_adds_no_excess_step():
    award = rules.work_out_award(an_agreement("fleet"), PLANS, a_request([300.0]), 600.0)
    assert award.award == 300.0
    assert all("excess" not in step for step, _ in steps_of(award))


def test_needs_sign_off_draws_the_line_at_the_limit():
    assert rules.needs_sign_off(600.0, 600.0) is False
    assert rules.needs_sign_off(600.01, 600.0) is True
    assert rules.needs_sign_off(275.0, 600.0) is False
