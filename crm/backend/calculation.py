"""Each case's latest calculation of its award, kept for the attempt it was made
in, which an approval in that attempt must match."""

from sqlalchemy import Connection, RowMapping, delete, insert, select

from backend.database import calculations, now
from backend.models import Calculation, Award


def keep_calculation(
    db: Connection, case_id: str, thread_id: str, award: Award
) -> None:
    """Keep a case's latest calculation, in place of any before it, on the thread
    of the attempt it was made in."""
    db.execute(delete(calculations).where(calculations.c.case_id == case_id))
    lines = [line.model_dump() for line in award.calculation]
    db.execute(
        insert(calculations).values(
            case_id=case_id,
            thread_id=thread_id,
            lines=lines,
            award=award.award,
            calculated_at=now(),
        )
    )


def attempts_calculation(db: Connection, case: RowMapping) -> Calculation | None:
    """Return the latest calculation on a case's current attempt, if any."""
    query = select(calculations).where(
        calculations.c.case_id == case["case_id"],
        calculations.c.thread_id == case["thread_id"],
    )
    row = db.execute(query).mappings().first()
    return Calculation(lines=row["lines"], award=row["award"]) if row else None
