"""CRM's award rules for an approved case.

The rules come from section 10 of the contract wording, the plans and sections 6, 7
and 10 of the cases manual. The plans and the approval limit come from settings.
"""

from dataclasses import dataclass
from math import ceil, inf

from backend.models import (
    Benefit,
    CalculationStep,
    Line,
    Award,
    AwardRequest,
    Plan,
    Plans,
    Contract,
)

CASH_LIMIT = 100.0
HOTEL_NIGHT_LIMIT = 350.0
MEALS_PER_TRAVELER_PER_DAY = 35.0
ELECTRONICS_PLUS = "electronics_plus"

BENEFIT_MAXIMUM = {
    "trip_cancellation": "trip_cancellation_max",
    "trip_interruption": "trip_cancellation_max",
    "trip_delay": "trip_delay_max",
    "baggage_delay": "baggage_delay_max",
    "baggage": "baggage_max",
    "passport": "passport_max",
    "emergency_medical": "emergency_medical_max",
}


@dataclass
class Limits:
    """The limits on the lines of a case under one contract."""

    per_item: float
    electronics_per_item: float
    travelers: int


def needs_sign_off(award: float, approval_limit: float) -> bool:
    """Say whether a award is over the limit, and so needs a worker's sign-off."""
    return award > approval_limit


def step(description: str, amount: float) -> CalculationStep:
    """Make one line of the calculation, rounded to the cent."""
    return CalculationStep(step=description, amount=round(amount, 2))


def limits_for(contract: Contract, plan: Plan, plans: Plans) -> Limits:
    """Return the limits on a contract's lines; Electronics Plus raises electronics."""
    electronics = plan.per_item_limit
    if ELECTRONICS_PLUS in contract.add_ons:
        add_on = next(a for a in plans.add_ons if a.add_on == ELECTRONICS_PLUS)
        electronics = add_on.electronics_per_item_limit or electronics
    return Limits(plan.per_item_limit, electronics, len(contract.travelers))


def limit_for(line: Line, limits: Limits) -> float:
    """Return the most CRM pays for one line, or infinity for no limit."""
    match line.kind:
        case "item":
            return limits.per_item * line.quantity
        case "electronics":
            return limits.electronics_per_item * line.quantity
        case "hotel":
            rooms = ceil(limits.travelers / 2)
            return HOTEL_NIGHT_LIMIT * rooms * line.nights
        case "meals_without_receipts":
            days = ceil(line.hours / 24)
            return MEALS_PER_TRAVELER_PER_DAY * limits.travelers * days
        case _:
            return inf


def eligible_amount(line: Line, limits: Limits) -> CalculationStep:
    """Return the amount claimed for one line, or its limit if that is lower."""
    limit = limit_for(line, limits)
    if line.amount > limit:
        return step(f"{line.description}, limited to ${limit:,.2f}", limit)
    return step(line.description, line.amount)


def benefit_maximum(contract: Contract, plan: Plan, benefit: Benefit) -> float:
    """Return the most the plan pays for a benefit, capped at the trip cost for
    Trip Cancellation and Interruption. A benefit the schedule does not carry is
    refused, as a wrong request rather than a server error."""
    if benefit not in BENEFIT_MAXIMUM:
        raise ValueError(f"The schedule carries no benefit called {benefit!r}")
    maximum: float = getattr(plan, BENEFIT_MAXIMUM[benefit])
    if benefit in ("trip_cancellation", "trip_interruption"):
        return min(maximum, contract.trip.trip_cost)
    return maximum


def work_out_award(
    contract: Contract, plans: Plans, request: AwardRequest, approval_limit: float
) -> Award:
    """Work out the award on an approved case, step by step, and whether it needs
    a worker's sign-off."""
    plan = next(plan for plan in plans.plans if plan.plan == contract.plan)
    limits = limits_for(contract, plan, plans)
    calculation, total = line_steps(request, limits)
    total = deductions(calculation, total, request, plan, plans)
    total = cap_at_maximum(calculation, total, contract, plan, request.benefit)
    if total < 0:
        calculation.append(step("Nothing is left to pay", -total))
        total = 0.0

    award = round(total, 2)
    return Award(
        calculation=calculation,
        award=award,
        needs_sign_off=needs_sign_off(award, approval_limit),
    )


def line_steps(
    request: AwardRequest, limits: Limits
) -> tuple[list[CalculationStep], float]:
    """The steps for each line of the case, with their total."""
    calculation = [
        eligible_amount(line, limits) for line in request.lines if line.kind != "cash"
    ]
    cash = sum(line.amount for line in request.lines if line.kind == "cash")
    if cash:
        calculation.append(
            step(f"Cash, up to ${CASH_LIMIT:,.0f} in all", min(cash, CASH_LIMIT))
        )
    return calculation, sum(entry.amount for entry in calculation)


def deductions(
    calculation: list[CalculationStep],
    total: float,
    request: AwardRequest,
    plan: Plan,
    plans: Plans,
) -> float:
    """Less what others have paid, and less the deductible when it applies."""
    if request.paid_by_others:
        calculation.append(
            step("Less what others have paid or refunded", -request.paid_by_others)
        )
        total -= request.paid_by_others
    if request.benefit in plans.deductible_applies_to and total > 0:
        deductible = min(plan.deductible, total)
        if deductible:
            calculation.append(step("Less the deductible", -deductible))
            total -= deductible
    return total


def cap_at_maximum(
    calculation: list[CalculationStep],
    total: float,
    contract: Contract,
    plan: Plan,
    benefit: str,
) -> float:
    """Cap the total at the plan's maximum for the benefit."""
    maximum = benefit_maximum(contract, plan, benefit)
    if total > maximum:
        calculation.append(
            step(
                f"Less the amount over the maximum of ${maximum:,.0f}", maximum - total
            )
        )
        total = maximum
    return total
