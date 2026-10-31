"""What needs a worker, worked out in code from the queue: the awards held for
sign-off with their amounts, the cases referred, the cases left for a worker,
and any case sent back that the agent hasn't taken up."""

from typing import Any

from agent.app_terms import REFER, Status


def needs_a_worker(queue: list[dict[str, Any]]) -> dict[str, Any]:
    """What in the queue needs a worker."""
    return {
        "held_for_sign_off": [
            {"case_id": c["case_id"], "outcome": c["outcome"]}
            for c in queue
            if c["status"] == Status.WAITING_FOR_SIGN_OFF
        ],
        "referred": [
            c["case_id"]
            for c in queue
            if c["status"] == Status.DECIDED and c["decision"] == REFER
        ],
        "left_for_a_worker": [
            c["case_id"] for c in queue if c["status"] == Status.LEFT_FOR_WORKER
        ],
        "sent_back_not_taken_up": [
            c["case_id"] for c in queue if c["status"] == Status.SENT_BACK
        ],
    }
