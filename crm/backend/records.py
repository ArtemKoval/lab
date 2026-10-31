"""What cases manual section 14 asks of a decision record: the request's checks,
which need nothing from the case, each refusing with a 422 whose message names
section 14."""

from fastapi import HTTPException

from backend.models import DecisionRequest

SECTION_14 = "Cases manual section 14: {missing}"
NO_REASON = "a decision record needs a reason in plain language"
NO_SECTION = "a decision record needs the section relied on"
NO_MAKER = "a decision record needs who or what made the decision"
NOTHING_RESOLVED = (
    "an approval needs the outcome the pack resolved for this attempt. "
    "Work it out with resolve_outcome"
)


def falls_short(missing: str) -> HTTPException:
    """Refuse a decision record with what it is missing, naming section 14."""
    return HTTPException(422, SECTION_14.format(missing=missing))


def check_request(request: DecisionRequest) -> None:
    """Refuse a request for a decision that leaves out what section 14 asks for."""
    for text, missing in (
        (request.reason, NO_REASON),
        (request.section, NO_SECTION),
        (request.decided_by, NO_MAKER),
    ):
        if not text.strip():
            raise falls_short(missing)
