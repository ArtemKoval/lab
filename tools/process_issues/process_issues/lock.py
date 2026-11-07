"""Loop lock for the process-issues run: record I/O and the stale judgment.

The record pins the session anchor: the first harness process on the
parent chain of the CLI call. The stale judgment stays pure through
injected inputs: the liveness probe, the host, the boot id, and the
clock arrive as parameters.
"""

import json
import os
import socket
from datetime import datetime, timezone
from pathlib import Path

LOCK_SCHEMA_VERSION = 1
LOCK_DIRNAME = ".process_issues"
LOCK_FILENAME = "lock.json"
STALE_AGE_SECONDS = 24 * 3600

# The parent chain walk stops at the first process whose name matches
# one entry. The anchor is the stable process of the calling session.
HARNESS_PROC_NAMES = ("claude",)

RULE_CORRUPT = "corrupt"
RULE_VERSION = "version"
RULE_AGE = "age"
RULE_BOOT = "boot"
RULE_PID = "pid"
RULE_START = "start"

VERDICT_FREE = "free"
VERDICT_OWN = "own"
VERDICT_STALE = "stale"
VERDICT_FRESH = "fresh"


def resolve_state_dir(repo_root, git_runner):
    """Return the state dir under the primary checkout root.

    The primary root comes from the git common directory. A failed call
    falls back to the working root, which covers an old git and a
    non-git root.
    """
    code, out, _ = git_runner(
        ["git", "-C", str(repo_root),
         "rev-parse", "--path-format=absolute", "--git-common-dir"]
    )
    if code == 0 and out.strip():
        return Path(out.strip()).parent / LOCK_DIRNAME
    return Path(repo_root) / LOCK_DIRNAME


def lock_path(state_dir):
    """Return the lock file path inside the state dir."""
    return Path(state_dir) / LOCK_FILENAME


def read_record(path):
    """Return (exists, record, error).

    A present but unparsable file gives (True, None, None). A file the
    process cannot read gives an error message, because the loop must
    not silently scan around a record it cannot see.
    """
    try:
        raw = Path(path).read_bytes()
    except FileNotFoundError:
        return False, None, None
    except OSError as exc:
        return True, None, f"process_issues: cannot read the lock at {path}: {exc}"
    try:
        record = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return True, None, None
    if not isinstance(record, dict):
        return True, None, None
    return True, record, None


def stale_rule(record, *, probe, host, boot_id, now):
    """Return the first matched stale rule, or None when the lock is fresh.

    A record with no process id has no anchor on this host. It behaves
    like a foreign host: fresh while young, stale at the age rule.
    """
    if record is None:
        return RULE_CORRUPT
    if record.get("version") != LOCK_SCHEMA_VERSION:
        return RULE_VERSION
    acquired = _parse_time(record.get("acquired_at"))
    if acquired is None or now - acquired > STALE_AGE_SECONDS:
        return RULE_AGE
    if record.get("host") != host:
        return None
    if record.get("boot_id") != boot_id:
        return RULE_BOOT
    if record.get("pid") is None:
        return None
    return probe(record.get("pid"), record.get("pid_start"))


def verdict(exists, record, *, holder, probe, host, boot_id, now,
            caller_pid=None):
    """Return (verdict, rule) for one lock examination.

    The verdict is free with no file, stale under one matched rule, own
    when the holder label matches or the record pins the calling session
    anchor, and fresh otherwise.
    """
    if not exists:
        return VERDICT_FREE, None
    rule = stale_rule(record, probe=probe, host=host, boot_id=boot_id, now=now)
    if rule is not None:
        return VERDICT_STALE, rule
    if holder is not None and holder == record.get("holder"):
        return VERDICT_OWN, None
    if caller_pid is not None and record.get("pid") == caller_pid:
        return VERDICT_OWN, None
    return VERDICT_FRESH, None


def make_record(holder, *, pid, pid_start, host, boot_id, now):
    """Return the lock record dict for one acquire."""
    return {
        "version": LOCK_SCHEMA_VERSION,
        "holder": holder,
        "host": host,
        "boot_id": boot_id,
        "pid": pid,
        "pid_start": pid_start,
        "acquired_at": datetime.fromtimestamp(now, tz=timezone.utc).isoformat(),
    }


def acquire(state_dir, holder, *, probe, host, boot_id, now, pid=None,
            pid_start=None, caller_pid=None):
    """Take the lock. Return (code, note), with the note for stderr.

    A fresh foreign lock refuses with exit 2. A stale lock is cleared
    and taken behind one exclusive file create. The acquire of the lock
    in force is idempotent. Without an injected anchor, the record pins
    the session anchor of the calling process.
    """
    path = lock_path(state_dir)
    exists, record, error = read_record(path)
    if error is not None:
        return 2, error
    kind, rule = verdict(exists, record, holder=holder, probe=probe,
                         host=host, boot_id=boot_id, now=now,
                         caller_pid=caller_pid)
    if kind == VERDICT_FRESH:
        return 2, holder_message(record)
    if kind == VERDICT_OWN:
        return 0, ""
    note = ""
    if kind == VERDICT_STALE:
        code, note = _clear(path, rule, holder)
        if code != 0:
            return code, note
    return _create(state_dir, path, holder, probe=probe, host=host,
                   boot_id=boot_id, now=now, pid=pid, pid_start=pid_start,
                   note=note)


def _clear(path, rule, holder):
    """Remove one stale lock file. Return (code, note)."""
    try:
        Path(path).unlink()
    except FileNotFoundError:
        return 2, (
            f"process_issues: the stale lock at {path} vanished; "
            f"run acquire again"
        )
    except OSError as exc:
        return 2, f"process_issues: cannot clear the stale lock at {path}: {exc}"
    note = f"process_issues: cleared a stale lock ({rule}) and took it for {holder}"
    return 0, note


def _create(state_dir, path, holder, *, probe, host, boot_id, now, pid,
            pid_start, note):
    """Create the lock file behind one exclusive open. Return (code, note)."""
    if pid is None:
        pid, pid_start = session_anchor()
    elif pid_start is None:
        pid_start = start_time(pid)
    payload = json.dumps(
        make_record(holder, pid=pid, pid_start=pid_start, host=host,
                    boot_id=boot_id, now=now)
    )
    try:
        Path(state_dir).mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return 2, f"process_issues: cannot create the state dir at {state_dir}: {exc}"
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        _, other, _ = read_record(path)
        return 2, holder_message(other)
    except OSError as exc:
        return 2, f"process_issues: cannot create the lock at {path}: {exc}"
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(payload)
    return 0, note


def release(state_dir, holder=None, force=False):
    """Drop the lock. Return (code, note), with the note for stderr.

    No lock file is success. The file leaves only on an exact holder
    label match, or behind --force. The force path skips the read, so it
    clears a lock file that this process cannot even read.
    """
    path = lock_path(state_dir)
    if force:
        return _unlink(path)
    exists, record, error = read_record(path)
    if error is not None:
        return 2, error
    if not exists:
        return 0, ""
    if record is not None and holder is not None:
        if holder == record.get("holder"):
            return _unlink(path)
        return 2, holder_message(record)
    return 2, f"process_issues: the lock record at {path} does not parse; use --force"


def examine(state_dir, *, holder, probe, host, boot_id, now, caller_pid=None):
    """Examine the lock for a scan. Return (code, note).

    A fresh foreign lock refuses with exit 2. A stale lock gives exit 0
    with a report, and the scan proceeds. The examination never writes.
    """
    path = lock_path(state_dir)
    exists, record, error = read_record(path)
    if error is not None:
        return 2, error
    kind, rule = verdict(exists, record, holder=holder, probe=probe,
                         host=host, boot_id=boot_id, now=now,
                         caller_pid=caller_pid)
    if kind == VERDICT_FRESH:
        return 2, holder_message(record)
    if kind == VERDICT_STALE:
        return 0, (f"process_issues: the lock is stale ({rule}); "
                   f"the scan proceeds, and acquire clears it")
    return 0, ""


def holder_message(record):
    """Return the one-line stderr report for the lock in force."""
    values = record or {}
    return (
        f"process_issues: the lock is held by {values.get('holder')!r} "
        f"on {values.get('host')!r} (pid {values.get('pid')}); "
        f"release --force clears it"
    )


def session_anchor(pid=None, stat_reader=None):
    """Return (pid, start) of the stable process of the calling session.

    The walk follows the parent chain and stops at the first process
    whose name matches one harness name. No match gives (None, None),
    and the record then carries no process id.
    """
    if pid is None:
        pid = os.getpid()
    reader = stat_reader or _stat_fields
    seen = set()
    while pid and pid > 1 and pid not in seen:
        seen.add(pid)
        entry = reader(pid)
        if entry is None:
            return None, None
        comm, ppid, start = entry
        if comm in HARNESS_PROC_NAMES:
            return pid, start
        pid = ppid
    return None, None


def _stat_fields(pid):
    """Return (comm, ppid, start) of one process, or None."""
    try:
        with open(f"/proc/{pid}/stat", "rb") as handle:
            data = handle.read().decode("utf-8", "replace")
    except OSError:
        return None
    try:
        comm = data.split("(", 1)[1].rsplit(")", 1)[0]
        rest = data.rsplit(")", 1)[1].split()
        return comm, int(rest[1]), rest[19]
    except (IndexError, ValueError):
        return None


def start_time(pid):
    """Return the /proc start time of pid, or None."""
    entry = _stat_fields(pid)
    if entry is None:
        return None
    return entry[2]


def probe_live(pid, pid_start):
    """Return the stale rule for the recorded process, or None when it runs."""
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        return RULE_PID
    try:
        os.kill(pid, 0)
    except PermissionError:
        return None
    except OSError:
        return RULE_PID
    actual = start_time(pid)
    if actual is None:
        return RULE_START
    if pid_start is None or str(pid_start) != actual:
        return RULE_START
    return None


def this_host():
    """Return this host name for the lock record."""
    return socket.gethostname()


def this_boot_id():
    """Return this boot id, or None when the source is unreadable."""
    try:
        return Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    except OSError:
        return None


def _parse_time(value):
    """Return the epoch seconds of an ISO 8601 value, or None."""
    try:
        return datetime.fromisoformat(value).timestamp()
    except (TypeError, ValueError):
        return None


def _unlink(path):
    """Remove the lock file. Return (code, note). A missing file is success."""
    try:
        Path(path).unlink()
        return 0, ""
    except FileNotFoundError:
        return 0, ""
    except OSError as exc:
        return 2, f"process_issues: cannot remove the lock at {path}: {exc}"
