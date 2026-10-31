"""The FastFix pack's protocol: the four verbs the engine calls.

The engine owns the pipeline and the writes; the pack owns what an outcome
means and what its side effect is. resolve works an approval's service
credit out through the pack's rules. gate says whether a credit needs a
lead's sign-off. execute gives the credit-issue record for an approved
case, which the engine writes. summarize gives the worker-facing line.
"""

from backend.models import Award, AwardRequest

from domains.helpdesk import rules


def resolve(case: dict, config: dict, request: AwardRequest) -> Award:
    """Work the service credit for one case out through the pack's rules."""
    return rules.work_out_award(case["contract"], config["plans"], request, config["approval_limit"])


def gate(outcome: dict, config: dict) -> bool:
    """Say whether an outcome's credit needs a lead's sign-off."""
    return rules.needs_sign_off(outcome["award"], config["approval_limit"])


def execute(case: dict, outcome: dict | None) -> dict:
    """Give the credit-issue record for an approved case. The engine writes it."""
    return {"amount": case["award"]}


def summarize(outcome: dict) -> str:
    """Give the worker-facing line for an outcome."""
    return f"{outcome['award']:,.2f} of service credit issued"


def metric(payload: dict) -> float:
    """Give the number the scoring reads."""
    return float(payload["award"])
