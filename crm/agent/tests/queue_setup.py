"""Setting the test queue up, straight in the backend's tables."""

from sqlalchemy import update

from backend.database import cases, engine


def leave_waiting(*case_ids):
    """Leave every case but the ones named for a worker, out of the agent's way."""
    with engine().begin() as db:
        db.execute(update(cases).values(status="left_for_worker"))
        db.execute(
            update(cases).where(cases.c.case_id.in_(case_ids)).values(status="waiting")
        )
