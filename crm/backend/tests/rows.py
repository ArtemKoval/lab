"""What the backend has recorded, read and written straight in its tables."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import Table, func, select, update

from backend.calculation import keep_calculation
from backend.database import (
    case_view,
    cases,
    engine,
    metadata,
    rounds,
    runs,
    stamp,
)
from backend.models import Award, CalculationStep


def count(table: Table) -> int:
    """How many rows a table holds."""
    with engine().connect() as db:
        return db.execute(select(func.count()).select_from(table)).scalar_one()


def calculated(case_id: str, award: float) -> None:
    """Keep a calculation of a award for a started case's current attempt, as
    calculate_award keeps one."""
    with engine().begin() as db:
        query = select(cases.c.thread_id).where(cases.c.case_id == case_id)
        thread_id = db.execute(query).scalar_one()
        steps = [CalculationStep(step="The covered costs", amount=award)]
        worked_out = Award(calculation=steps, award=award, needs_sign_off=False)
        keep_calculation(db, case_id, thread_id, worked_out)


def heard(table: Table, key: str, value: str, ago: timedelta, column="heard_at"):
    """Set when the app last heard of a piece of the agent's work."""
    moment = stamp(datetime.now(UTC) - ago)
    with engine().begin() as db:
        db.execute(update(table).where(table.c[key] == value).values({column: moment}))


def resume_heard(case_id: str, ago: timedelta) -> None:
    """Set when the agent last said a resume was working on a case."""
    heard(cases, "case_id", case_id, ago, "resume_heard_at")


def run_heard(run_id: str, ago: timedelta) -> None:
    heard(runs, "run_id", run_id, ago)


def round_heard(round_id: str, ago: timedelta) -> None:
    heard(rounds, "round_id", round_id, ago)


def committed_case(case_id: str):
    """A case's row as another connection reads it: what has been committed."""
    with engine().connect() as db:
        query = case_view.where(cases.c.case_id == case_id)
        return db.execute(query).mappings().one()


def newest(table: Table, key: str) -> str:
    """The id of the newest run or round, which the app created as a worker asked."""
    with engine().connect() as db:
        query = select(table.c[key]).order_by(table.c.number.desc()).limit(1)
        return db.execute(query).scalar_one()


def newest_run() -> str:
    return newest(runs, "run_id")


def newest_round() -> str:
    return newest(rounds, "round_id")


def everything_recorded():
    """Every row of every table, to show that a request changed nothing."""
    with engine().connect() as db:
        return {
            table.name: [dict(row) for row in db.execute(select(table)).mappings()]
            for table in metadata.sorted_tables
        }
