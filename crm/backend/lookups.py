"""Finding a case, a run, a version, the settings and the models allowed, and the
messages for what isn't found or can't be answered, which more than one of the
backend's modules need."""

from collections.abc import Callable
from typing import Any

from fastapi import HTTPException
from sqlalchemy import Connection, RowMapping, func, select

from backend.database import (
    case_view,
    cases,
    customers,
    models_allowed,
    rounds,
    runs,
    settings,
    versions,
)
from backend.models import ModelAllowed, Settings, Verdict

RUN_NOT_FOUND = "Run {run_id} not found"
CASE_NOT_FOUND = "Case {case_id} not found"
VERSION_NOT_FOUND = "Version {value} not found"
CUSTOMER_NOT_FOUND = "Customer {customer_id} not found"
NOT_WAITING_FOR_SIGN_OFF = "Case {case_id} is not waiting for sign-off"
A_COPY = "Case {case_id} is a copy in an evaluation and can't be {answered}"


def find_case(db: Connection, case_id: str) -> RowMapping:
    """Return one case's row, or raise a 404."""
    query = case_view.where(cases.c.case_id == case_id)
    row = db.execute(query).mappings().first()
    if row is None:
        raise HTTPException(404, CASE_NOT_FOUND.format(case_id=case_id))
    return row


def customer_record(db: Connection, customer_id: str) -> dict[str, Any]:
    """Return one customer's record, or raise a 404."""
    query = select(customers.c.record).where(customers.c.customer_id == customer_id)
    record = db.execute(query).scalar_one_or_none()
    if record is None:
        raise HTTPException(404, CUSTOMER_NOT_FOUND.format(customer_id=customer_id))
    return record


def run_row(db: Connection, run_id: str) -> RowMapping:
    """Return one run's row, or raise a 404."""
    row = db.execute(select(runs).where(runs.c.run_id == run_id)).mappings().first()
    if row is None:
        raise HTTPException(404, RUN_NOT_FOUND.format(run_id=run_id))
    return row


def round_numbers(db: Connection, round_ids: list[str | None]) -> dict[str, int]:
    """Return the numbers of the rounds with these ids, by id, in one query."""
    query = select(rounds.c.round_id, rounds.c.number).where(
        rounds.c.round_id.in_(round_ids)
    )
    return {round_id: number for round_id, number in db.execute(query)}


def round_number(db: Connection, round_id: str | None) -> int | None:
    """Return the number of the round with this id, or none for no round."""
    if round_id is None:
        return None
    return round_numbers(db, [round_id])[round_id]


def row_fetcher(
    table: Any, column: Any, not_found: str
) -> Callable[[Connection, Any], RowMapping]:
    """Make a lookup of the one row of the table where the column holds the value,
    or a 404 with the message."""

    def fetch(db: Connection, value: Any) -> RowMapping:
        query = select(table).where(column == value)
        row = db.execute(query).mappings().first()
        if row is None:
            raise HTTPException(404, not_found.format(value=value))
        return row

    return fetch


version_row = row_fetcher(versions, versions.c.number, VERSION_NOT_FOUND)


def current_version_number(db: Connection) -> int:
    """Return the current version: the newest one the business's rule kept, which
    is version 1 until a round keeps another."""
    query = select(func.max(versions.c.number)).where(
        versions.c.verdict == Verdict.KEPT
    )
    return db.execute(query).scalar_one()


def current_settings(db: Connection) -> Settings:
    """Return the settings in force: the newest change."""
    newest = select(func.max(settings.c.number)).scalar_subquery()
    query = select(settings).where(settings.c.number == newest)
    return Settings(**db.execute(query).mappings().one())


def allowed_models(db: Connection) -> list[ModelAllowed]:
    """Return the models the case agent may use, with their reasoning efforts and
    prices."""
    query = select(models_allowed).order_by(models_allowed.c.position)
    return [ModelAllowed(**row) for row in db.execute(query).mappings()]


def settings_number(db: Connection, number: int) -> Settings:
    """Return the settings as one change left them, such as a round's."""
    query = select(settings).where(settings.c.number == number)
    return Settings(**db.execute(query).mappings().one())
