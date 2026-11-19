"""The Northgate loan term rules for an approved request.

The arithmetic reads the requested days from the request lines' ``nights``
field, grants the plan's base term, adds the days past the base term, and
caps the term at the tier's ``max_loan_days``. Each step lands in the
calculation, and the term over the approval limit of 14 days needs the lead
librarian's sign-off. The rules are pure code, with no engine I/O.
"""

from backend.models import Award, AwardRequest, CalculationStep, Contract, Plans


def needs_sign_off(award: float, approval_limit: float) -> bool:
    """Say whether the loan term needs the lead librarian's sign-off."""
    return award > approval_limit


def step(description: str, days: float) -> CalculationStep:
    """Make one line of the term calculation, in whole days."""
    return CalculationStep(step=description, amount=round(days))


def requested_days(request: AwardRequest) -> float:
    """Add the requested days up over the request lines."""
    return sum(line.nights for line in request.lines)


def base_term(calculation: list[CalculationStep], plan) -> float:
    """Grant the plan's base term, as the first line of the calculation."""
    base = f"Base term of the {plan.plan} plan, {plan.base_loan_days:g} days"
    calculation.append(step(base, plan.base_loan_days))
    return plan.base_loan_days


def add_renewal(
    calculation: list[CalculationStep], total: float, plan, days: float
) -> float:
    """Add the requested days past the base term of the plan."""
    extra = days - plan.base_loan_days
    if extra > 0:
        calculation.append(step(f"Renewal, {extra:g} days past the base term", extra))
        total += extra
    return total


def cap_at_tier(calculation: list[CalculationStep], total: float, plan) -> float:
    """Cap the term at the tier's maximum loan days."""
    if total > plan.max_loan_days:
        cap = (
            f"Less the days over the {plan.plan} term cap of "
            f"{plan.max_loan_days:g} days"
        )
        calculation.append(step(cap, plan.max_loan_days - total))
        total = plan.max_loan_days
    return total


def work_out_award(
    contract: Contract, plans: Plans, request: AwardRequest, approval_limit: float
) -> Award:
    """Work out the loan term of an approved request, step by step, and
    whether it needs the lead librarian's sign-off."""
    plan = next(plan for plan in plans.plans if plan.plan == contract.plan)
    days = requested_days(request)
    calculation: list[CalculationStep] = []
    total = base_term(calculation, plan)
    total = add_renewal(calculation, total, plan, days)
    total = cap_at_tier(calculation, total, plan)
    award = round(max(total, 0.0))
    return Award(
        calculation=calculation,
        award=award,
        needs_sign_off=needs_sign_off(award, approval_limit),
    )
