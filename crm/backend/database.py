"""The CRM database, seeded from the business data in data/, and the plans
and the documents from the context layer's files in context/.

The same tables and queries serve Postgres on Supabase, when DATABASE_URL is set, and
SQLite otherwise, as in the tests.
"""

import os
from datetime import UTC, datetime
from functools import cache
from pathlib import Path
from typing import Any, NamedTuple

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Connection,
    Engine,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    Table,
    Text,
    UniqueConstraint,
    create_engine,
    insert,
    inspect,
    select,
)
from sqlalchemy.engine import URL, make_url
from sqlalchemy.pool import NullPool
from sqlalchemy.schema import CreateSchema

from backend import context_files
from backend.free_models import model_or_free, models_or_free
from backend.models import (
    EvaluationSet,
    ModelAllowed,
    SettingsValues,
    Status,
    Verdict,
)
from domains import loader

ROOT = Path(__file__).resolve().parent.parent
MANUAL = "manual"
DOCUMENTS = {"wording": "Contract wording", MANUAL: "Cases manual"}
# Version 1 is kept from the start, so the current version is the newest kept.
FIRST_VERSION = {
    "number": 1,
    "reason": "The case agent as the cases team built it",
    "proposed_by": "The cases team",
    "verdict": Verdict.KEPT,
    "verdict_reason": "the first version",
}
# The model version 1 of the case agent is on, with no reasoning, so a higher
# reasoning effort is an improvement to find, unless a student is on a free model.
FIRST_MODEL = ("openai/gpt-6-luna", "none")
FIRST_RECIPE = {
    "number": 1,
    "recipe": loader.pack().instruction("recipe"),
    "reason": "The lab's first recipe, which tries the models and reasoning efforts "
    "not yet tried, then adds a rule for each mistake",
    "proposed_by": "The cases team",
}
HELD_OUT_CASES = "held_out_cases.json"
SCHEMA = "crm"
CONNECTIONS = 4
CONNECTION_WAIT = 120
# Tables of earlier versions, dropped before the others, since on Postgres a foreign
# key of theirs would stop the tables they refer to being dropped.
RETIRED = ["todos"]

metadata = MetaData()

# The platform's settings, one row for each change; the newest row is in force.
settings = Table(
    "settings",
    metadata,
    Column("number", Integer, primary_key=True, autoincrement=False),
    Column("approval_limit", Float, nullable=False),
    Column("objectives", JSON, nullable=False),
    Column("noise", JSON, nullable=False),
    Column("tolerance", JSON, nullable=False),
    Column("spending_limit", Float, nullable=False),
    Column("agents", Integer, nullable=False),
    Column("changed_by", Text),
    Column("changed_at", Text, nullable=False),
)
award_rules = Table(
    "award_rules",
    metadata,
    Column("plans", JSON, nullable=False),
)
models_allowed = Table(
    "models_allowed",
    metadata,
    Column("model", Text, primary_key=True),
    Column("position", Integer, nullable=False),
    Column("reasoning_efforts", JSON, nullable=False),
    Column("input_price", Float, nullable=False),
    Column("output_price", Float, nullable=False),
)
documents = Table(
    "documents",
    metadata,
    Column("name", Text, primary_key=True),
    Column("position", Integer, nullable=False),
    Column("title", Text, nullable=False),
    Column("text", Text, nullable=False),
    # The version in the document's front matter, such as the manual's 2026.2.
    Column("version", Text, nullable=False),
)
workers = Table(
    "workers",
    metadata,
    Column("worker_id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("role", Text, nullable=False),
    Column("email", Text, nullable=False, unique=True),
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
    Column("evaluation_id", Text, ForeignKey("runs.run_id")),
    Column("copy_of", Text),
    # When the agent last said a resume was working on the case.
    Column("resume_heard_at", Text),
)
held_out_cases = Table(
    "held_out_cases",
    metadata,
    Column("case_id", Text, primary_key=True),
    Column("record", JSON, nullable=False),
)
worker_decisions = Table(
    "worker_decisions",
    metadata,
    Column("evaluation_set", Text, primary_key=True),
    Column("case_id", Text, primary_key=True),
    Column("decision", Text, nullable=False),
    Column("award", Float, nullable=False),
    Column("tiny", Boolean, nullable=False),
    Column("reason", Text, nullable=False),
    Column("reference", Text, nullable=False),
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
    # Who or what made the decision, and the cases manual's version in force.
    Column("decided_by", Text, nullable=False),
    Column("manual_version", Text, nullable=False),
    # An approval's calculation, its lines and its award, and none otherwise.
    Column("calculation", JSON),
    # The approval limit in force when the decision was recorded.
    Column("approval_limit", Float, nullable=False),
    Column("signed_off_by", Text),
    Column("signed_off_at", Text),
    # Why the Gateway refused to pay an approval, which then waits for sign-off.
    Column("gateway_refusal", Text),
)
# The decisions workers sent back to the agent, each with its note, who sent it
# back and when.
sent_back_decisions = Table(
    "sent_back_decisions",
    metadata,
    Column("sent_back_id", Integer, primary_key=True),
    Column("case_id", Text, ForeignKey("cases.case_id"), nullable=False),
    Column("decision", Text, nullable=False),
    Column("award", Float, nullable=False),
    Column("calculation", JSON),
    Column("section", Text, nullable=False),
    Column("reason", Text, nullable=False),
    Column("decided_by", Text, nullable=False),
    Column("decided_at", Text, nullable=False),
    Column("manual_version", Text, nullable=False),
    Column("gateway_refusal", Text),
    Column("note", Text, nullable=False),
    Column("sent_back_by", Text, nullable=False),
    Column("sent_back_at", Text, nullable=False),
)
# Each case's latest calculation of its award, on the thread of the attempt it was
# made in, which an approval in that attempt must match.
calculations = Table(
    "calculations",
    metadata,
    Column("case_id", Text, ForeignKey("cases.case_id"), primary_key=True),
    Column("thread_id", Text, nullable=False),
    Column("lines", JSON, nullable=False),
    Column("award", Float, nullable=False),
    Column("calculated_at", Text, nullable=False),
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
    # The context files a lookup came from, each with its source.
    Column("sources", JSON, nullable=False),
    Column("created_at", Text, nullable=False),
)
# The improver's rounds, each to the settings, the recipe and the version of the
# case agent in force when it started.
rounds = Table(
    "rounds",
    metadata,
    Column("number", Integer, primary_key=True),
    Column("round_id", Text, nullable=False, unique=True),
    Column("thread_id", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("settings", Integer, ForeignKey("settings.number"), nullable=False),
    Column("recipe", Integer, nullable=False),
    Column("starting_version", Integer, nullable=False),
    # The sets of the first evaluations the starting version still needed.
    Column("first_evaluations", JSON, nullable=False),
    Column("improver_model", Text, nullable=False),
    Column("improver_reasoning_effort", Text, nullable=False),
    Column("started_by", Text, nullable=False),
    Column("started_at", Text, nullable=False),
    Column("finished_at", Text),
    Column("stopped_by", Text),
    Column("stopped_because", Text),
    Column("held_out_before", JSON),
    Column("held_out_after", JSON),
    # When the app last heard of the round's work: as it started the round or
    # recorded a review, or from the agent's heartbeat.
    Column("heard_at", Text),
)
recipes = Table(
    "recipes",
    metadata,
    Column("number", Integer, primary_key=True, autoincrement=False),
    Column("recipe", Text, nullable=False),
    Column("reason", Text, nullable=False),
    Column("proposed_by", Text, nullable=False),
    Column("round_id", Text, ForeignKey("rounds.round_id")),
    Column("approved_by", Text),
    Column("approved_at", Text),
    Column("created_at", Text, nullable=False),
)
# The improver's proposals, each waiting for a worker until it is reviewed.
proposals = Table(
    "proposals",
    metadata,
    Column("proposal_id", Text, primary_key=True),
    Column("round_id", Text, ForeignKey("rounds.round_id"), nullable=False),
    Column("kind", Text, nullable=False),
    Column("proposal", JSON, nullable=False),
    Column("proposed_at", Text, nullable=False),
    Column("review", Text),
    Column("reviewed_by", Text),
    Column("reviewed_at", Text),
    Column("rejection_reason", Text),
)
improver_calls = Table(
    "improver_calls",
    metadata,
    Column("improver_call_id", Integer, primary_key=True),
    Column("round_id", Text, ForeignKey("rounds.round_id"), nullable=False),
    Column("input_tokens", Integer, nullable=False),
    Column("output_tokens", Integer, nullable=False),
    Column("cost", Float, nullable=False),
    Column("created_at", Text, nullable=False),
)
versions = Table(
    "versions",
    metadata,
    Column("number", Integer, primary_key=True, autoincrement=False),
    Column("instructions", Text, nullable=False),
    Column("model", Text, nullable=False),
    Column("reasoning_effort", Text, nullable=False),
    Column("reason", Text, nullable=False),
    Column("proposed_by", Text, nullable=False),
    # The version this one changes, which was current when it was proposed.
    Column("based_on", Integer, ForeignKey("versions.number")),
    Column("round_id", Text, ForeignKey("rounds.round_id")),
    Column("approved_by", Text),
    Column("approved_at", Text),
    Column("created_at", Text, nullable=False),
    Column("verdict", Text),
    Column("verdict_reason", Text),
)
runs = Table(
    "runs",
    metadata,
    Column("number", Integer, primary_key=True),
    Column("run_id", Text, nullable=False, unique=True),
    Column("kind", Text, nullable=False),
    Column("agents", Integer, nullable=False),
    Column("version", Integer, ForeignKey("versions.number"), nullable=False),
    Column("round_id", Text, ForeignKey("rounds.round_id")),
    Column("model", Text, nullable=False),
    Column("reasoning_effort", Text, nullable=False),
    Column("evaluation_set", Text),
    Column("tiny", Boolean),
    Column("status", Text, nullable=False),
    Column("started_at", Text, nullable=False),
    Column("finished_at", Text),
    Column("summary", JSON),
    Column("stopped_because", Text),
    # When the app last heard of the run's work: as it created the run, or from
    # the agent's heartbeat.
    Column("heard_at", Text),
)
# One row, which a start of the agent's work updates first in its transaction, so
# two starts at the same moment take turns.
locks = Table(
    "locks",
    metadata,
    Column("name", Text, primary_key=True),
    Column("taken_at", Text),
)
AGENTS_WORK = "the agent's work"
# The judge's grade of each copy in an evaluation, empty when it couldn't grade it.
grades = Table(
    "grades",
    metadata,
    Column("case_id", Text, ForeignKey("cases.case_id"), primary_key=True),
    Column("run_id", Text, ForeignKey("runs.run_id"), nullable=False),
    Column("score", Float),
    Column("letter", Text),
    Column("same_grounds", Float),
    Column("same_section", Float),
    Column("cost", Float, nullable=False),
    Column("graded_at", Text, nullable=False),
)
run_cases = Table(
    "run_cases",
    metadata,
    Column("run_id", Text, ForeignKey("runs.run_id"), primary_key=True),
    Column("position", Integer, primary_key=True),
    Column("case_id", Text, ForeignKey("cases.case_id"), nullable=False),
)
model_calls = Table(
    "model_calls",
    metadata,
    Column("model_call_id", Integer, primary_key=True),
    Column("case_id", Text, ForeignKey("cases.case_id"), nullable=False),
    Column("thread_id", Text, nullable=False),
    Column("run_id", Text, ForeignKey("runs.run_id")),
    Column("input_tokens", Integer, nullable=False),
    Column("output_tokens", Integer, nullable=False),
    Column("cost", Float, nullable=False),
    Column("created_at", Text, nullable=False),
)
work_times = Table(
    "work_times",
    metadata,
    Column("work_time_id", Integer, primary_key=True),
    Column("case_id", Text, ForeignKey("cases.case_id"), nullable=False),
    Column("thread_id", Text, nullable=False),
    Column("run_id", Text, ForeignKey("runs.run_id")),
    Column("started_at", Text, nullable=False),
    Column("seconds", Float, nullable=False),
)


# The Copilot's conversations, each its worker's, with how many turns it has, which
# a new turn moves on from n to n + 1 with a conditional update, so a conversation
# takes one message at a time.
conversations = Table(
    "conversations",
    metadata,
    Column("conversation_id", Text, primary_key=True),
    Column("worker_id", Text, ForeignKey("workers.worker_id"), nullable=False),
    Column("title", Text, nullable=False),
    Column("turns", Integer, nullable=False),
    Column("created_at", Text, nullable=False),
)
# Each message to the Copilot and its answer: where the turn stands, how it ended,
# and the card of a sign-off waiting for the worker's confirmation, with the held
# decision's decided_at, and the worker's answer.
copilot_turns = Table(
    "copilot_turns",
    metadata,
    Column("turn_id", Text, primary_key=True),
    Column(
        "conversation_id",
        Text,
        ForeignKey("conversations.conversation_id"),
        nullable=False,
    ),
    Column("number", Integer, nullable=False),
    Column("message", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("started_at", Text, nullable=False),
    Column("paused_at", Text),
    Column("answered_at", Text),
    Column("finished_at", Text),
    Column("answer", Text),
    Column("model_calls", Integer),
    Column("cost", Float),
    Column("failure", Text),
    Column("confirmation", JSON),
    Column("confirmation_answer", Text),
    Column("canceled_because", Text),
    UniqueConstraint("conversation_id", "number"),
)
# The cards of a turn: each tool the Copilot called, what was asked and what came
# back.
copilot_steps = Table(
    "copilot_steps",
    metadata,
    Column("step_id", Integer, primary_key=True),
    Column(
        "turn_id",
        Text,
        ForeignKey("copilot_turns.turn_id"),
        nullable=False,
        index=True,
    ),
    Column("tool", Text, nullable=False),
    Column("kind", Text, nullable=False),
    Column("input", Text, nullable=False),
    Column("asked", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("answer", Text),
    Column("reason", Text),
    Column("sources", JSON, nullable=False),
    Column("started_at", Text, nullable=False),
    Column("finished_at", Text),
)


class LabeledSet(NamedTuple):
    """A set of cases our workers have decided: the table its cases are kept in,
    and the eval file with the workers' decisions, which only seeding
    reads."""

    cases: Table
    decisions: str


LABELED_SETS = {
    EvaluationSet.EVALUATION: LabeledSet(cases, "decisions.json"),
    EvaluationSet.HELD_OUT: LabeledSet(held_out_cases, "held_out_decisions.json"),
}

case_view = (
    select(
        cases.c.case_id,
        cases.c.record,
        cases.c.status,
        cases.c.thread_id,
        cases.c.attempts,
        cases.c.evaluation_id,
        cases.c.copy_of,
        cases.c.resume_heard_at,
        customers.c.name.label("customer_name"),
        decisions.c.decision,
        decisions.c.award,
        decisions.c.section,
        decisions.c.reason,
        decisions.c.decided_at,
        decisions.c.decided_by,
        decisions.c.manual_version,
        decisions.c.calculation,
        decisions.c.approval_limit,
        decisions.c.signed_off_by,
        decisions.c.signed_off_at,
        decisions.c.gateway_refusal,
        payments.c.amount,
        payments.c.paid_at,
    )
    .join(customers, customers.c.customer_id == cases.c.customer_id)
    .outerjoin(decisions, decisions.c.case_id == cases.c.case_id)
    .outerjoin(payments, payments.c.case_id == cases.c.case_id)
)


def stamp(moment: datetime) -> str:
    """Write a moment in UTC to the second, as every record has it."""
    return moment.isoformat(timespec="seconds")


def now() -> str:
    """Return the current time in UTC, to the second."""
    return stamp(datetime.now(UTC))


def stamp_precisely(moment: datetime) -> str:
    """Write a moment in UTC to the millisecond, as the Copilot's turns and cards
    have it, since many of them take less than a second."""
    return moment.isoformat(timespec="milliseconds")


def now_precisely() -> str:
    """Return the current time in UTC, to the millisecond."""
    return stamp_precisely(datetime.now(UTC))


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


def on_lambda() -> bool:
    """Say whether the backend runs on AWS Lambda, which sets this for every
    function."""
    return "AWS_LAMBDA_FUNCTION_NAME" in os.environ


@cache
def engine_for(url: URL, for_lambda: bool) -> Engine:
    """Open a database: on Lambda, Postgres with a connection for each request and
    no prepared statements, for Supabase's transaction pooler, since each copy of
    the function would keep its own pool; elsewhere Postgres with at most
    CONNECTIONS connections, waiting up to CONNECTION_WAIT seconds for one, or
    SQLite with a connection for each request."""
    if on_postgres(url) and for_lambda:
        return create_engine(
            url, poolclass=NullPool, connect_args={"prepare_threshold": None}
        )
    if on_postgres(url):
        return create_engine(
            url,
            pool_size=CONNECTIONS,
            max_overflow=0,
            pool_timeout=CONNECTION_WAIT,
            pool_pre_ping=True,
        )
    return create_engine(url, poolclass=NullPool)


def engine() -> Engine:
    """Return the backend's database."""
    return engine_for(database_url(), on_lambda())


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


def queue_records(name: str) -> list[dict[str, Any]]:
    """Read the queue's records of one kind: those in data/ and the security team's
    in data/security/, whose worker's decision is never seeded."""
    return load(name) + load(f"security/{name}")


def waiting_case(record: dict[str, Any], **columns: Any) -> dict[str, Any]:
    """Return the row of a case waiting in the queue, never started, with any other
    columns given."""
    return {
        "case_id": record["case_id"],
        "customer_id": record["customer_id"],
        "record": record,
        "status": Status.WAITING,
        "thread_id": None,
        "attempts": 0,
    } | columns


def seed(db: Engine) -> dict[str, int]:
    """Build the tables afresh from the pack and count what they hold."""
    active = loader.pack()
    company = active.load_json("company.json")
    worker_rows = load("workers.json")
    customer_rows = queue_records("customers.json")
    contract_rows = queue_records("contracts.json")
    case_rows = queue_records("cases.json")
    with db.begin() as connection:
        if on_postgres(db.url):
            connection.execute(CreateSchema(SCHEMA, if_not_exists=True))
        for name in RETIRED:
            Table(name, MetaData()).drop(connection, checkfirst=True)
        metadata.drop_all(connection)
        metadata.create_all(connection)
        seed_settings(connection, company["award_approval_limit"])
        connection.execute(insert(award_rules).values(plans=context_files.plans()))
        seed_models_allowed(connection)
        seed_documents(connection)
        connection.execute(
            insert(workers),
            [
                {
                    "worker_id": h["worker_id"],
                    "name": h["name"],
                    "role": h["role"],
                    "email": h["email"],
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
        connection.execute(insert(cases), [waiting_case(c) for c in case_rows])
        seed_first_version(connection)
        connection.execute(insert(recipes).values(**FIRST_RECIPE, created_at=now()))
        connection.execute(insert(locks).values(name=AGENTS_WORK))
        labeled = seed_evaluations(connection)
    return {
        "cases": len(case_rows),
        "contracts": len(contract_rows),
        "customers": len(customer_rows),
        "workers": len(worker_rows),
    } | labeled


def seed_documents(connection: Connection) -> None:
    """Store the contract wording and the cases manual from the context layer's
    files, each with its version."""
    rows = []
    for position, (name, title) in enumerate(DOCUMENTS.items()):
        text, version = context_files.document(name)
        rows.append(
            {
                "name": name,
                "position": position,
                "title": title,
                "text": text,
                "version": version,
            }
        )
    connection.execute(insert(documents), rows)


def seed_settings(connection: Connection, approval_limit: float) -> None:
    """Store the first settings: the approval limit, and the rest from
    data/improvement.json, checked as the settings page checks a change."""
    values = SettingsValues(approval_limit=approval_limit, **load("improvement.json"))
    connection.execute(
        insert(settings).values(number=1, **values.model_dump(), changed_at=now())
    )


def seed_models_allowed(connection: Connection) -> None:
    """Store the models the case agent may use, from data/models.json, or the free
    model alone for students on free models."""
    listed = [ModelAllowed(**model) for model in load("models.json")]
    connection.execute(
        insert(models_allowed),
        [
            model.model_dump() | {"position": position}
            for position, model in enumerate(models_or_free(listed))
        ],
    )


def seed_first_version(connection: Connection) -> None:
    """Make version 1 of the case agent's configuration, from its instructions file,
    on GPT-6 Luna with no reasoning, or the free model for students on free
    models."""
    model, reasoning_effort = model_or_free(*FIRST_MODEL)
    connection.execute(
        insert(versions).values(
            **FIRST_VERSION,
            instructions=loader.pack().instruction("case"),
            model=model,
            reasoning_effort=reasoning_effort,
            created_at=now(),
        )
    )


def seed_evaluations(connection: Connection) -> dict[str, int]:
    """Store the held-out cases, out of the queue, and the workers' decisions on
    both labeled sets, and count them."""
    held_out = loader.pack().load_eval(HELD_OUT_CASES)
    connection.execute(
        insert(held_out_cases),
        [{"case_id": c["case_id"], "record": c} for c in held_out],
    )
    rows = [
        {
            "evaluation_set": evaluation_set,
            "case_id": d["case_id"],
            "decision": d["decision"],
            "award": d["award"],
            "tiny": d["tiny"],
            "reason": d["reason"],
            "reference": d["reference"],
        }
        for evaluation_set, labeled in LABELED_SETS.items()
        for d in loader.pack().load_eval(labeled.decisions)
    ]
    connection.execute(insert(worker_decisions), rows)
    return {"held_out_cases": len(held_out), "worker_decisions": len(rows)}
