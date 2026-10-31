"""The OpsDesk pack's protocol: the four verbs the engine calls, and the
metric. The engine owns the pipeline and the writes; the pack owns what an
outcome means and what its side effect is. resolve estimates the effort to
escalate a case through the pack's rules. gate says whether the effort needs
the operations lead's sign-off. execute gives the escalation record, which
the engine writes. summarize gives the worker-facing line. No money moves
anywhere in this pack."""

from backend.models import Award, AwardRequest

from domains.opsdemo import rules


def resolve(case: dict, config: dict, request: AwardRequest) -> Award:
    """Estimate the effort for one case through the pack's rules."""
    return rules.work_out_award(case["contract"], config["plans"], request, config["approval_limit"])


def gate(outcome: dict, config: dict) -> bool:
    """Say whether an outcome's effort needs the lead's sign-off."""
    return rules.needs_sign_off(outcome["award"], config["approval_limit"])


def execute(case: dict, outcome: dict) -> dict:
    """Give the escalation record from the outcome. The engine writes it."""
    return {"queue": "platform", "hours": outcome["award"]}


def summarize(outcome: dict) -> str:
    """Give the worker-facing line for an outcome."""
    return f"{outcome['award']:g} engineer-hours to escalate"


def metric(payload: dict) -> float:
    """Give the number the scoring reads."""
    return float(payload["award"])
