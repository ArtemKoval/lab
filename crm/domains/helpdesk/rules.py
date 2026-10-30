"""FastFix's service-credit rules for an approved case.

The rules come from section 10 of the support wording and section 10 of the
support manual. The plans and the approval limit come from settings.
"""

from dataclasses import dataclass

from backend.models import (
    CalculationStep,
    Award,
    AwardRequest,
    Plan,
    Plans,
    Contract,
)


@dataclass
class Limits:
    """The limits on the credit for one case under one contract."""

    per_incident_cap: float
    multiplier: float


def needs_sign_off(award: float, approval_limit: float) -> bool:
    """Say whether a credit is over the limit, and so needs a lead's sign-off."""
    return award > approval_limit


def step(description: str, amount: float) -> CalculationStep:
    """Make one line of the calculation, rounded to the cent."""
    return CalculationStep(step=description, amount=round(amount, 2))


def limits_for(plan: Plan) -> Limits:
    """Return a plan's per-incident cap and its priority multiplier."""
    return Limits(plan.per_incident_cap, plan.priority_multiplier)


def line_steps(
    request: AwardRequest,
) -> tuple[list[CalculationStep], float]:
    """The steps for each line of the case, with their total."""
    calculation = [step(line.description, line.amount) for line in request.lines]
    return calculation, sum(entry.amount for entry in calculation)


def less_already_issued(
    calculation: list[CalculationStep], total: float, request: AwardRequest
) -> float:
    """Less the credit FastFix already issued for the same incident."""
    if request.paid_by_others:
        calculation.append(
            step("Less the credit already issued for this incident", -request.paid_by_others)
        )
        total -= request.paid_by_others
    return total


def apply_priority_multiplier(
    calculation: list[CalculationStep], total: float, limits: Limits
) -> float:
    """Multiply the credit on a plan that carries a priority multiplier."""
    if limits.multiplier > 1.0 and total > 0:
        calculation.append(
            step(
                f"Priority multiplier of {limits.multiplier:g}",
                total * (limits.multiplier - 1.0),
            )
        )
        total *= limits.multiplier
    return total


def cap_at_per_incident(
    calculation: list[CalculationStep], total: float, limits: Limits
) -> float:
    """Cap the total at the plan's per-incident cap."""
    if total > limits.per_incident_cap:
        calculation.append(
            step(
                f"Less the amount over the per-incident cap of "
                f"${limits.per_incident_cap:,.0f}",
                limits.per_incident_cap - total,
            )
        )
        total = limits.per_incident_cap
    return total


def work_out_award(
    contract: Contract, plans: Plans, request: AwardRequest, approval_limit: float
) -> Award:
    """Work out the service credit on an approved case, step by step, and whether
    it needs a lead's sign-off."""
    plan = next(plan for plan in plans.plans if plan.plan == contract.plan)
    limits = limits_for(plan)
    calculation, total = line_steps(request)
    total = less_already_issued(calculation, total, request)
    total = apply_priority_multiplier(calculation, total, limits)
    total = cap_at_per_incident(calculation, total, limits)
    if total < 0:
        calculation.append(step("Nothing is left to credit", -total))
        total = 0.0

    award = round(total, 2)
    return Award(
        calculation=calculation,
        award=award,
        needs_sign_off=needs_sign_off(award, approval_limit),
    )
