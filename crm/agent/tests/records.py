"""What the test backend has recorded on cases and runs."""

from sqlalchemy import select

from backend.database import engine, model_calls, work_times


def case_of(client, case_id):
    return client.get(f"/api/cases/{case_id}").json()


def steps_of(client, case_id):
    return client.get(f"/api/cases/{case_id}/steps").json()


def evaluations(client):
    return client.get("/api/evaluations").json()


def rows_of(table, case_id):
    """The rows of a case in one of the backend's tables, in the order recorded."""
    query = select(table).where(table.c.case_id == case_id)
    with engine().connect() as db:
        rows = db.execute(query.order_by(*table.primary_key)).mappings()
        return [dict(row) for row in rows]


def model_calls_of(case_id):
    return rows_of(model_calls, case_id)


def work_times_of(case_id):
    return rows_of(work_times, case_id)
