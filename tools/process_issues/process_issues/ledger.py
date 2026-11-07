"""The write-ahead ledger for the loop writes.

The store is one append-only JSONL file beside the lock in the state
dir. The pure view functions take parsed records, and the I/O carries
the newline guard and the numbered skip notes.
"""

import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path

LEDGER_FILENAME = "ledger.jsonl"
EVENT_INTENT = "intent"
EVENT_CONFIRMED = "confirmed"
KINDS = ("comment", "label", "merge", "close")

REQUIRED_FIELDS = {
    EVENT_INTENT: ("id", "kind", "key", "at"),
    EVENT_CONFIRMED: ("id", "at"),
}

MARKER_PREFIX = "loop-"


class LedgerError(Exception):
    """The ledger store cannot be read."""


def ledger_path(state_dir):
    """Return the ledger file path inside the state dir."""
    return Path(state_dir) / LEDGER_FILENAME


def new_marker(existing_ids, now=None, rng=None):
    """Return a fresh marker id over the injected clock and random.

    The form is loop-<yyyymmddhhmm>-<4 hex>, and the writer
    regenerates on a collision with an existing id.
    """
    now = time.time() if now is None else now
    rng = random.random if rng is None else rng
    existing = set(existing_ids)
    while True:
        stamp = datetime.fromtimestamp(
            now, tz=timezone.utc
        ).strftime("%Y%m%d%H%M")
        suffix = format(int(rng() * 0x10000), "04x")
        marker = f"{MARKER_PREFIX}{stamp}-{suffix}"
        if marker not in existing:
            return marker
        now = now + 1


def append_record(path, record):
    """Append one JSONL record behind the newline guard.

    A crash mid-append leaves a partial line, and the guard starts the
    next append on a fresh line, so the tear cannot glue onto this
    record.
    """
    payload = (json.dumps(record) + "\n").encode("utf-8")
    try:
        existing = Path(path).read_bytes()
    except FileNotFoundError:
        existing = b""
    except OSError as exc:
        raise LedgerError(f"cannot read the ledger at {path}: {exc}") from exc
    prefix = b"\n" if existing and not existing.endswith(b"\n") else b""
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise LedgerError(
            f"cannot create the state dir at {Path(path).parent}: {exc}"
        ) from exc
    with open(path, "ab") as handle:
        handle.write(prefix + payload)


def read_records(path):
    """Return (records, skip_notes).

    A line that is not a valid event record is skipped with one
    numbered note, and the exit stays 0, because the ledger is an
    audit trail. Only an unreadable file is a failure.
    """
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return [], []
    except OSError as exc:
        raise LedgerError(f"cannot read the ledger at {path}: {exc}") from exc
    records = []
    notes = []
    for number, line in enumerate(raw.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except ValueError:
            notes.append(f"skipped ledger line {number}")
            continue
        fields = REQUIRED_FIELDS.get(
            record.get("event") if isinstance(record, dict) else None
        )
        if fields is None or not all(
            isinstance(record.get(name), str) and record.get(name)
            for name in fields
        ):
            notes.append(f"skipped ledger line {number}")
            continue
        records.append(record)
    return records, notes


def pending_view(records):
    """Return the unconfirmed intents with superseded flags.

    The rows stay in file order, oldest first. A row is superseded
    when a newer unconfirmed intent of the same kind and key exists,
    and the newest row of a group owns the decision.
    """
    confirmed = {
        row["id"] for row in records if row.get("event") == EVENT_CONFIRMED
    }
    intents = [
        row for row in records
        if row.get("event") == EVENT_INTENT and row.get("id") not in confirmed
    ]
    superseded = set()
    groups = set()
    for row in reversed(intents):
        group = (row.get("kind"), row.get("key"))
        if group in groups:
            superseded.add(row.get("id"))
        else:
            groups.add(group)
    return [
        {
            "id": row.get("id"),
            "kind": row.get("kind"),
            "key": row.get("key"),
            "at": row.get("at"),
            "superseded": row.get("id") in superseded,
        }
        for row in intents
    ]
