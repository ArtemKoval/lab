"""What the backend has recorded, read and written straight in its tables."""

from sqlalchemy import Table, func, select

from backend.calculation import keep_calculation
from backend.database import cases, engine
from backend.models import CalculationStep, Award


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
