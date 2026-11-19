"""The Northgate pack's protocol: the five verbs the engine calls.

The engine owns the pipeline and the writes, and the pack owns what an
outcome means and what its side effect is. resolve works the loan term out
through the pack's rules. gate says whether the term needs the lead
librarian's sign-off. execute gives the loan record for an approved
request, which the engine writes. summarize gives the worker-facing line,
and metric gives the number the scoring reads. No money moves anywhere in
this pack.
"""

from backend.models import Award, AwardRequest
from domains.library import rules


def resolve(case: dict, config: dict, request: AwardRequest) -> Award:
    """Work the loan term for one case out through the pack's rules."""
    return rules.work_out_award(
        case["contract"], config["plans"], request, config["approval_limit"]
    )


def gate(outcome: dict, config: dict) -> bool:
    """Say whether an outcome's loan term needs the lead's sign-off."""
    return rules.needs_sign_off(outcome["award"], config["approval_limit"])


def execute(case: dict, outcome: dict) -> dict:
    """Give the loan record from the outcome. The engine writes it."""
    items = case["record"]["items"]
    return {"title": items[0]["description"], "days": outcome["award"]}


def summarize(outcome: dict) -> str:
    """Give the worker-facing line for an outcome."""
    return f"{outcome['award']:g}-day loan issued"


def metric(payload: dict) -> float:
    """Give the number the scoring reads."""
    return float(payload["award"])
