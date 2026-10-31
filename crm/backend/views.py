"""Cases as the API shows them, built from rows of the case view."""

from sqlalchemy import RowMapping

from backend.agent_work import heard_lately
from backend.models import (
    Case,
    CaseSummary,
    Decision,
    EffectRun,
    SentBackDecision,
    Status,
)
from domains import loader


def outcome_line(payload: dict | None) -> str | None:
    """The pack's own line on a resolved outcome, through its summarize, or
    nothing when there is none."""
    if payload is None:
        return None
    return loader.pack().protocol_module().summarize(payload)


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
            "outcome": outcome_line(row["payload"]),
            "resuming": resuming,
        }
    )


def to_case(
    row: RowMapping,
    sent_back: list[SentBackDecision],
    effect: EffectRun | None = None,
) -> Case:
    """Build a case in full, with its decision and its effect's run, from its
    row, the decisions workers sent back on it, and the run."""
    decision = None
    if row["decision"] is not None:
        decision = Decision(**{field: row[field] for field in Decision.model_fields})
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
            "effect": effect,
            "sent_back_decisions": sent_back,
        }
    )
