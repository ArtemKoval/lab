"""Cases as the API shows them, built from rows of the case view."""

from sqlalchemy import RowMapping

from backend.models import Case, CaseSummary, Decision, Payment


def to_summary(row: RowMapping) -> CaseSummary:
    """Build a case's line in the queue from its row."""
    return CaseSummary(
        **row["record"]
        | {
            "status": row["status"],
            "customer_name": row["customer_name"],
            "decision": row["decision"],
            "award": row["award"],
        }
    )


def to_case(row: RowMapping) -> Case:
    """Build a case in full, with its decision and payment, from its row."""
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
        }
    )
