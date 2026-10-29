"""The CRM database, seeded from the active domain pack."""

import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path

from domains import loader

ROOT = Path(__file__).resolve().parent.parent
DOCUMENTS = {"wording": "Contract wording", "manual": "Cases manual"}

SCHEMA = """
CREATE TABLE settings (
    award_approval_limit REAL NOT NULL
);
CREATE TABLE documents (
    name TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    text TEXT NOT NULL
);
CREATE TABLE workers (
    worker_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    can_approve_over_limit INTEGER NOT NULL
);
CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    record TEXT NOT NULL
);
CREATE TABLE contracts (
    contract_id TEXT PRIMARY KEY,
    record TEXT NOT NULL
);
CREATE TABLE cases (
    case_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers,
    record TEXT NOT NULL,
    status TEXT NOT NULL,
    thread_id TEXT,
    attempts INTEGER NOT NULL
);
CREATE TABLE decisions (
    case_id TEXT PRIMARY KEY REFERENCES cases,
    decision TEXT NOT NULL,
    award REAL NOT NULL,
    section TEXT NOT NULL,
    reason TEXT NOT NULL,
    decided_at TEXT NOT NULL
);
CREATE TABLE payments (
    case_id TEXT PRIMARY KEY REFERENCES cases,
    amount REAL NOT NULL,
    paid_at TEXT NOT NULL,
    signed_off_by TEXT
);
CREATE TABLE steps (
    step_id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id TEXT NOT NULL REFERENCES cases,
    thread_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE runs (
    run_id TEXT PRIMARY KEY,
    cap INTEGER NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    summary TEXT
);
CREATE TABLE todos (
    run_id TEXT NOT NULL REFERENCES runs,
    position INTEGER NOT NULL,
    content TEXT NOT NULL,
    status TEXT NOT NULL,
    PRIMARY KEY (run_id, position)
);
CREATE VIEW case_view AS
SELECT
    cases.case_id, cases.record, cases.status, cases.thread_id,
    cases.attempts,
    customers.name AS customer_name,
    decisions.decision, decisions.award, decisions.section, decisions.reason,
    decisions.decided_at,
    payments.amount, payments.paid_at, payments.signed_off_by
FROM cases
JOIN customers USING (customer_id)
LEFT JOIN decisions USING (case_id)
LEFT JOIN payments USING (case_id);
"""


def database_path() -> Path:
    """Return the database file from CRM_DB, or crm.db at the root."""
    return Path(os.getenv("CRM_DB", str(ROOT / "crm.db")))


def connect() -> sqlite3.Connection:
    """Open the database, with rows that can be read by column name."""
    connection = sqlite3.connect(database_path(), check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection


def seed(path: Path) -> dict[str, int]:
    """Build a fresh database at path from the pack and count what it holds."""
    active = loader.pack()
    seed_files = active.manifest.get("seed", {})
    workers = active.load_json(seed_files.get("workers", "workers.json"))
    customers = active.load_json(seed_files.get("customers", "customers.json"))
    contracts = active.load_json(seed_files.get("contracts", "contracts.json"))
    cases = active.load_json(seed_files.get("cases", "cases.json"))
    path.unlink(missing_ok=True)
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.executescript(SCHEMA)
        connection.execute(
            "INSERT INTO settings VALUES (?)",
            (active.settings["award_approval_limit"],),
        )
        connection.executemany(
            "INSERT INTO documents VALUES (?, ?, ?)",
            [(name, title, active.read_doc(name)) for name, title in DOCUMENTS.items()],
        )
        connection.executemany(
            "INSERT INTO workers VALUES (?, ?, ?, ?)",
            [
                (h["worker_id"], h["name"], h["role"], h["can_approve_over_limit"])
                for h in workers
            ],
        )
        connection.executemany(
            "INSERT INTO customers VALUES (?, ?, ?)",
            [(c["customer_id"], c["name"], json.dumps(c)) for c in customers],
        )
        connection.executemany(
            "INSERT INTO contracts VALUES (?, ?)",
            [(p["contract_id"], json.dumps(p)) for p in contracts],
        )
        connection.executemany(
            "INSERT INTO cases VALUES (?, ?, ?, 'waiting', NULL, 0)",
            [(c["case_id"], c["customer_id"], json.dumps(c)) for c in cases],
        )
    return {
        "cases": len(cases),
        "contracts": len(contracts),
        "customers": len(customers),
        "workers": len(workers),
    }
