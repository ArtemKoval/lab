"""The OpsDesk effort rules for an approved escalation.

The rules come from section 4 of the operations wording and section 3 of the
operations manual. The SLA tiers and the escalation limit come from settings.
The effort is in engineer-hours, and no money moves anywhere in this pack.
"""

from dataclasses import dataclass

from backend.models import (
    Award,
    AwardRequest,
    CalculationStep,
    Contract,
    Plan,
    Plans,
)


@dataclass
class Tier:
    """The SLA tier of one contract, with its escalation numbers."""

    response_target_hours: float
    escalation_multiplier: float
    weekly_capacity: float


def needs_sign_off(award: float, approval_limit: float) -> bool:
    """Say whether the effort needs the operations lead's sign-off."""
    return award > approval_limit


def step(description: str, hours: float) -> CalculationStep:
    """Make one line of the estimate, to half an hour."""
    return CalculationStep(step=description, amount=round(hours * 2) / 2)


def with_on_call_margin(
    estimate: list[CalculationStep], total: float, tier: Tier
) -> float:
    """Add the on-call margin a tier carries over two hours of work."""
    if total > 2.0 and tier.escalation_multiplier > 1.0:
        extra = total * (tier.escalation_multiplier - 1.0)
        estimate.append(
            step(f"On-call margin, times {tier.escalation_multiplier:g}", extra)
        )
        total += extra
    return total


def cap_at_capacity(
    estimate: list[CalculationStep], total: float, tier: Tier
) -> float:
    """Cap the effort at the tier's weekly capacity for one escalation."""
    if total > tier.weekly_capacity:
        estimate.append(
            step(
                f"Less the effort over the tier capacity of "
                f"{tier.weekly_capacity:g} hours",
                tier.weekly_capacity - total,
            )
        )
        total = tier.weekly_capacity
    return total


def tier_for(plan: Plan) -> Tier:
    """Return a contract's SLA tier from the plan the contract names."""
    return Tier(
        plan.response_target_hours,
        plan.escalation_multiplier,
        plan.weekly_capacity,
    )


def work_out_award(
    contract: Contract, plans: Plans, request: AwardRequest, approval_limit: float
) -> Award:
    """Estimate the effort to escalate one case, step by step, and whether it
    needs the operations lead's sign-off."""
    plan = next(plan for plan in plans.plans if plan.plan == contract.plan)
    tier = tier_for(plan)
    estimate = [step(item.description, item.amount) for item in request.lines]
    total = sum(entry.amount for entry in estimate)
    total = with_on_call_margin(estimate, total, tier)
    total = cap_at_capacity(estimate, total, tier)
    if total < 0:
        estimate.append(step("No work is left to escalate", -total))
        total = 0.0

    effort = round(total * 2) / 2
    return Award(
        calculation=estimate,
        award=effort,
        needs_sign_off=needs_sign_off(effort, approval_limit),
    )
