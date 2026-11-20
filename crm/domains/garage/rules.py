"""The AutoFix authorization rules for an approved repair job.

The arithmetic sums the covered fault lines, subtracts the plan's base
excess once, floors the total at zero, caps the total at the plan's
``per_repair_cap``, and records every step. An authorization over the
approval limit of 600 needs a service manager's sign-off. The rules are
pure code, with no engine I/O.
"""

from backend.models import Award, AwardRequest, CalculationStep, Contract, Plans


def needs_sign_off(award: float, approval_limit: float) -> bool:
    """Say whether the authorization needs the service manager's sign-off."""
    return award > approval_limit


def step(description: str, amount: float) -> CalculationStep:
    """Make one line of the authorization calculation, at the penny."""
    return CalculationStep(step=description, amount=round(amount, 2))


def fault_lines(request: AwardRequest) -> list[CalculationStep]:
    """Make one calculation line per covered fault line of the request."""
    return [step(line.description, line.amount) for line in request.lines]


def subtract_excess(calculation: list[CalculationStep], total: float, plan) -> float:
    """Subtract the base excess of the plan once, under the fault lines."""
    excess = getattr(plan, "base_excess", 0.0)
    if excess > 0:
        calculation.append(
            step(f"Less the base excess of the {plan.plan} plan", -excess)
        )
        total -= excess
    return total


def floor_at_zero(calculation: list[CalculationStep], total: float) -> float:
    """Floor the total at zero when the excess eats the whole estimate."""
    if total < 0:
        calculation.append(step("Nothing is left to authorize", -total))
        total = 0.0
    return total


def cap_at_plan(calculation: list[CalculationStep], total: float, plan) -> float:
    """Cap the authorization at the plan's per-repair cap."""
    cap = getattr(plan, "per_repair_cap", 0.0)
    if cap > 0 and total > cap:
        calculation.append(
            step(f"Less the amount over the {plan.plan} cap of {cap:g}", cap - total)
        )
        total = cap
    return total


def work_out_award(
    contract: Contract, plans: Plans, request: AwardRequest, approval_limit: float
) -> Award:
    """Work out the authorization of an approved job, step by step, and
    whether it needs the service manager's sign-off."""
    plan = next(plan for plan in plans.plans if plan.plan == contract.plan)
    calculation = fault_lines(request)
    total = sum(line.amount for line in request.lines)
    total = subtract_excess(calculation, total, plan)
    total = floor_at_zero(calculation, total)
    total = cap_at_plan(calculation, total, plan)
    award = round(max(total, 0.0), 2)
    return Award(
        calculation=calculation,
        award=award,
        needs_sign_off=needs_sign_off(award, approval_limit),
    )
