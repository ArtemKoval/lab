"""The CRM database, seeded from the business data in data/.

The same tables and queries serve Postgres on Supabase, when DATABASE_URL is set, and
SQLite otherwise, as in the tests.
"""

import os
from functools import cache
from pathlib import Path
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Engine,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    Table,
    Text,
    create_engine,
    insert,
    inspect,
    select,
)
from sqlalchemy.engine import URL, make_url
from sqlalchemy.pool import NullPool
from sqlalchemy.schema import CreateSchema

from domains import loader

ROOT = Path(__file__).resolve().parent.parent
DOCUMENTS = {"wording": "Contract wording", "manual": "Cases manual"}
SCHEMA = "crm"
CONNECTIONS = 4

metadata = MetaData()

settings = Table(
    "settings",
    metadata,
    Column("award_approval_limit", Float, nullable=False),
    Column("plans", JSON, nullable=False),
)
documents = Table(
    "documents",
    metadata,
    Column("name", Text, primary_key=True),
    Column("position", Integer, nullable=False),
    Column("title", Text, nullable=False),
    Column("text", Text, nullable=False),
)
workers = Table(
    "workers",
    metadata,
    Column("worker_id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("role", Text, nullable=False),
    Column("can_approve_over_limit", Boolean, nullable=False),
)
customers = Table(
    "customers",
    metadata,
    Column("customer_id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("record", JSON, nullable=False),
)
contracts = Table(
    "contracts",
    metadata,
    Column("contract_id", Text, primary_key=True),
    Column("record", JSON, nullable=False),
)
cases = Table(
    "cases",
    metadata,
    Column("case_id", Text, primary_key=True),
    Column("customer_id", Text, ForeignKey("customers.customer_id"), nullable=False),
    Column("record", JSON, nullable=False),
    Column("status", Text, nullable=False),
    Column("thread_id", Text),
    Column("attempts", Integer, nullable=False),
)
decisions = Table(
    "decisions",
    metadata,
    Column("case_id", Text, ForeignKey("cases.case_id"), primary_key=True),
    Column("decision", Text, nullable=False),
    Column("award", Float, nullable=False),
    Column("section", Text, nullable=False),
    Column("reason", Text, nullable=False),
    Column("decided_at", Text, nullable=False),
    Column("signed_off_by", Text),
    Column("signed_off_at", Text),
)
payments = Table(
    "payments",
    metadata,
    Column("case_id", Text, ForeignKey("cases.case_id"), primary_key=True),
    Column("amount", Float, nullable=False),
    Column("paid_at", Text, nullable=False),
)
steps = Table(
    "steps",
    metadata,
    Column("step_id", Integer, primary_key=True),
    Column("case_id", Text, ForeignKey("cases.case_id"), nullable=False),
    Column("thread_id", Text, nullable=False),
    Column("kind", Text, nullable=False),
    Column("content", Text, nullable=False),
    Column("created_at", Text, nullable=False),
)
runs = Table(
    "runs",
    metadata,
    Column("number", Integer, primary_key=True),
    Column("run_id", Text, nullable=False, unique=True),
    Column("cap", Integer, nullable=False),
    Column("status", Text, nullable=False),
    Column("started_at", Text, nullable=False),
    Column("finished_at", Text),
    Column("summary", Text),
)
todos = Table(
    "todos",
    metadata,
    Column("run_id", Text, ForeignKey("runs.run_id"), primary_key=True),
    Column("position", Integer, primary_key=True),
    Column("content", Text, nullable=False),
    Column("status", Text, nullable=False),
)

case_view = (
    select(
        cases.c.case_id,
        cases.c.record,
        cases.c.status,
        cases.c.thread_id,
        cases.c.attempts,
        customers.c.name.label("customer_name"),
        decisions.c.decision,
        decisions.c.award,
        decisions.c.section,
        decisions.c.reason,
        decisions.c.decided_at,
        decisions.c.signed_off_by,
        decisions.c.signed_off_at,
        payments.c.amount,
        payments.c.paid_at,
    )
    .join(customers, customers.c.customer_id == cases.c.customer_id)
    .outerjoin(decisions, decisions.c.case_id == cases.c.case_id)
    .outerjoin(payments, payments.c.case_id == cases.c.case_id)
)


def database_url() -> URL:
    """Return Postgres at DATABASE_URL, through psycopg and in our own schema, or
    SQLite at CRM_DB or crm.db."""
    if url := os.getenv("DATABASE_URL"):
        postgres = make_url(url).set(drivername="postgresql+psycopg")
        return postgres.update_query_dict({"options": f"-c search_path={SCHEMA}"})
    path = os.getenv("CRM_DB", str(ROOT / "crm.db"))
    return URL.create("sqlite", database=path)


def on_postgres(url: URL) -> bool:
    """Say whether a database is Postgres rather than SQLite."""
    return url.get_backend_name() == "postgresql"


@cache
def engine_for(url: URL) -> Engine:
    """Open a database: Postgres with at most CONNECTIONS connections, or SQLite with
    a connection for each request."""
    if on_postgres(url):
        return create_engine(
            url, pool_size=CONNECTIONS, max_overflow=0, pool_pre_ping=True
        )
    return create_engine(url, poolclass=NullPool)


def engine() -> Engine:
    """Return the backend's database."""
    return engine_for(database_url())


def location(db: Engine) -> str:
    """Say where a database is, for a person to read."""
    if on_postgres(db.url):
        return f"the {SCHEMA} schema on Postgres"
    return Path(str(db.url.database)).name


def is_seeded(db: Engine) -> bool:
    """Say whether the database has its tables."""
    return inspect(db).has_table("cases")


def load(name: str) -> Any:
    """Read one of the JSON files in the pack data folder."""
    return loader.pack().load_json(name)


def seed(db: Engine) -> dict[str, int]:
    """Build the tables afresh from the pack and count what they hold."""
    active = loader.pack()
    company = active.load_json("company.json")
    worker_rows = load("workers.json")
    customer_rows = load("customers.json")
    contract_rows = load("contracts.json")
    case_rows = load("cases.json")
    with db.begin() as connection:
        if on_postgres(db.url):
            connection.execute(CreateSchema(SCHEMA, if_not_exists=True))
        metadata.drop_all(connection)
        metadata.create_all(connection)
        connection.execute(
            insert(settings),
            {
                "award_approval_limit": active.settings["award_approval_limit"],
                "plans": load("plans.json"),
            },
        )
        connection.execute(
            insert(documents),
            [
                {
                    "name": name,
                    "position": position,
                    "title": title,
                    "text": active.read_doc(name),
                }
                for position, (name, title) in enumerate(DOCUMENTS.items())
            ],
        )
        connection.execute(
            insert(workers),
            [
                {
                    "worker_id": h["worker_id"],
                    "name": h["name"],
                    "role": h["role"],
                    "can_approve_over_limit": h["can_approve_over_limit"],
                }
                for h in worker_rows
            ],
        )
        connection.execute(
            insert(customers),
            [
                {"customer_id": c["customer_id"], "name": c["name"], "record": c}
                for c in customer_rows
            ],
        )
        connection.execute(
            insert(contracts),
            [{"contract_id": p["contract_id"], "record": p} for p in contract_rows],
        )
        connection.execute(
            insert(cases),
            [
                {
                    "case_id": c["case_id"],
                    "customer_id": c["customer_id"],
                    "record": c,
                    "status": "waiting",
                    "thread_id": None,
                    "attempts": 0,
                }
                for c in case_rows
            ],
        )
    return {
        "cases": len(case_rows),
        "contracts": len(contract_rows),
        "customers": len(customer_rows),
        "workers": len(worker_rows),
    }
