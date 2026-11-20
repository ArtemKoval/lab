"""The AutoFix pack's protocol: the five verbs the engine calls.

The engine owns the pipeline and the writes, and the pack owns what an
outcome means and what its side effect is. resolve works the authorization
out through the pack's rules. gate says whether the authorization needs the
service manager's sign-off. execute gives the authorization record for an
approved job, which the engine writes, with the case reference and the
amount. summarize gives the worker-facing line, and metric gives the number
the scoring reads. The desk names the chosen garage in the decision reason,
per ADR 0020.
"""

from backend.models import Award, AwardRequest
from domains.garage import rules


def resolve(case: dict, config: dict, request: AwardRequest) -> Award:
    """Work the authorization for one job out through the pack's rules."""
    args = case["contract"], config["plans"], request, config["approval_limit"]
    return rules.work_out_award(*args)


def gate(outcome: dict, config: dict) -> bool:
    """Say whether an outcome's authorization needs the service manager."""
    return rules.needs_sign_off(outcome["award"], config["approval_limit"])


def execute(case: dict, outcome: dict) -> dict:
    """Give the authorization record from the outcome. The engine writes it."""
    return {
        "case_id": case["record"]["case_id"],
        "amount": outcome["award"],
    }


def summarize(outcome: dict) -> str:
    """Give the worker-facing line for an outcome."""
    return f"repair authorized for {outcome['award']:,.2f} pounds"


def metric(payload: dict) -> float:
    """Give the number the scoring reads."""
    return float(payload["award"])
