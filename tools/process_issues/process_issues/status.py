"""Status rows for the process-issues loop: the pure level table.

The rows examine the loop in a fixed order, and the first matched row
decides the exit. The facts arrive injected, and None marks a row with
no signal or a row the examination did not reach.
"""

LEVEL_RUNNING = "running"
LEVEL_HALT = "halt"
LEVEL_AUTH = "auth"
LEVEL_ISSUE_LIST = "issue-list"
LEVEL_BLOCKED = "blocked"
LEVEL_STALE = "stale"
LEVEL_IDLE = "idle"
LEVEL_LOCK = "lock"

CODE_RUNNING = 0
CODE_STOPPED = 1
CODE_COMPONENT = 2
CODE_SETUP = 3

LOCK_STATE_BY_VERDICT = {
    "fresh": "held",
    "own": "held",
    "stale": "stale",
    "free": "absent",
}

HALT_FALLBACK = "the halt file stands"
AUTH_REASON = "setup: the gh token is missing or the gh call failed"
IDLE_REASON = "idle: no lock file stands"


def decide(halt=None, auth_error=None, list_error=None, blocked=None,
           lock_row=None):
    """Return (level, code, reason) for the first matched row.

    The row order is the halt file, the auth probe, the issue list,
    the blocked issues, and the lock. A None fact carries no signal,
    and the first non-None fact wins.
    """
    if halt is not None:
        return LEVEL_HALT, CODE_STOPPED, halt
    if auth_error is not None:
        return LEVEL_AUTH, CODE_SETUP, auth_error
    if list_error is not None:
        return LEVEL_ISSUE_LIST, CODE_COMPONENT, list_error
    if blocked is not None:
        return LEVEL_BLOCKED, CODE_COMPONENT, blocked_reason(blocked)
    if lock_row is not None:
        return lock_row
    return LEVEL_IDLE, CODE_STOPPED, IDLE_REASON


def halt_reason(first_line):
    """Return the reason from the halt file first line."""
    line = (first_line or "").strip()
    if not line:
        return HALT_FALLBACK
    return line


def blocked_reason(entries):
    """Return the one-line reason for the blocked entries."""
    numbers = ", ".join(f"#{number}" for number, _title in entries)
    return f"blocked issues need the operator: {numbers}"


def lock_row(error=None, verdict_kind=None, rule=None):
    """Map one lock examination to its status row triple."""
    if error is not None:
        return LEVEL_LOCK, CODE_COMPONENT, error
    if verdict_kind == "fresh" or verdict_kind == "own":
        return LEVEL_RUNNING, CODE_RUNNING, ""
    if verdict_kind == "stale":
        return LEVEL_STALE, CODE_STOPPED, f"stale lock: {rule}"
    return LEVEL_IDLE, CODE_STOPPED, IDLE_REASON


def lock_summary(verdict_kind, holder, rule):
    """Return the lock summary object for the status payload."""
    if verdict_kind is None:
        return None
    state = LOCK_STATE_BY_VERDICT.get(verdict_kind, "unreadable")
    return {"state": state, "holder": holder, "rule": rule}
