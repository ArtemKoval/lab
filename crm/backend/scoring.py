"""The lab's measures of the agent's work against the workers' decisions: whether an
answer is right, what a mistake costs, and an evaluation's measures."""

from typing import NamedTuple

from backend.models import DecisionKind, Measures, ScoredCase

WRONGFUL_DECLINE = 1500
NEEDLESS_REFERRAL = 50
# A award within a dollar of the worker's is right.
AWARD_TOLERANCE = 1


class Answer(NamedTuple):
    """A decision on a case and its award, the agent's or a worker's."""

    decision: DecisionKind
    award: float


def answer_of(decision: DecisionKind | None, award: float | None) -> Answer:
    """Return the agent's answer on a case, with a case it didn't decide counted
    as a referral."""
    if decision is None:
        return Answer(DecisionKind.REFER, 0)
    return Answer(decision, award or 0)


def is_right(answer: Answer, expected: Answer) -> bool:
    """Say whether the decision matches the worker's and the award is within a
    dollar."""
    return (
        answer.decision == expected.decision
        and abs(answer.award - expected.award) <= AWARD_TOLERANCE
    )


def mistake_cost(answer: Answer, expected: Answer) -> float:
    """Return what the agent's answer costs CRM against the worker's: a
    wrongful decline, a wrongful approval's award whether or not it was paid, a
    needless referral, or the difference on a right approval."""
    if answer.decision == expected.decision:
        if answer.decision == DecisionKind.APPROVE:
            return abs(answer.award - expected.award)
        return 0
    if answer.decision == DecisionKind.DECLINE:
        return WRONGFUL_DECLINE
    if answer.decision == DecisionKind.APPROVE:
        return answer.award
    return NEEDLESS_REFERRAL


def measures(
    cases: list[ScoredCase], model_cost: float, run_seconds: float | None
) -> Measures:
    """Score an evaluation from its cases, its model cost and its time."""
    count = len(cases)
    agreed = [
        answer_of(c.decision, c.award).decision == c.worker_decision for c in cases
    ]
    referred = [
        answer_of(c.decision, c.award).decision == DecisionKind.REFER for c in cases
    ]
    return Measures(
        decision_accuracy=sum(agreed) / count,
        accuracy=sum(c.right for c in cases) / count,
        cost_of_mistakes=sum(c.mistake_cost for c in cases),
        straight_through=sum(not r for r in referred) / count,
        model_cost_per_case=model_cost / count,
        seconds_per_case=sum(c.seconds for c in cases) / count,
        run_seconds=run_seconds,
    )
