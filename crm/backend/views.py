"""Cases as the API shows them, built from rows of the case view."""

from sqlalchemy import RowMapping

from backend.agent_work import heard_lately
from backend.models import (
    Case,
    CaseSummary,
    Decision,
    Payment,
    SentBackDecision,
    Status,
)


def to_summary(row: RowMapping) -> CaseSummary:
    """Build a case's line in the queue from its row, saying whether a resume is
    working on it: one in progress that the agent spoke of lately."""
    resuming = row["status"] == Status.IN_PROGRESS and heard_lately(
        row["resume_heard_at"]
    )
    return CaseSummary(
        **row["record"]
        | {
            "status": row["status"],
            "customer_name": row["customer_name"],
            "decision": row["decision"],
            "award": row["award"],
            "resuming": resuming,
        }
    )


def to_case(row: RowMapping, sent_back: list[SentBackDecision]) -> Case:
    """Build a case in full, with its decision and payment, from its row, and the
    decisions workers sent back on it."""
    decision = None
    if row["decision"] is not None:
        decision = Decision(**{field: row[field] for field in Decision.model_fields})
    payment = None
    if row["paid_at"] is not None:
        payment = Payment(**{field: row[field] for field in Payment.model_fields})
    return Case(
        **row["record"]
        | {
            "status": row["status"],
            "customer_name": row["customer_name"],
            "thread_id": row["thread_id"],
            "attempts": row["attempts"],
            "evaluation_id": row["evaluation_id"],
            "copy_of": row["copy_of"],
            "decision": decision,
            "payment": payment,
            "sent_back_decisions": sent_back,
        }
    )
