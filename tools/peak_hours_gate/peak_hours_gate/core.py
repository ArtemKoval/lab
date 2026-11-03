"""Pure window math and the block-set decision for the peak-hours gate.

No I/O lives here. The clock enters as a parameter, the hook event as a
dict, and the override value as a string. The functions return plain
values, so tests need no patching and the CLI stays a thin shell.
"""

from datetime import datetime, time, timedelta, timezone

# The z.ai peak window: Monday to Friday, 14:00 to 18:00 SGT. The start
# is inclusive and the end is exclusive. SGT is UTC+8 with no DST.
SGT_OFFSET = timedelta(hours=8)
WINDOW_START = 14
WINDOW_END = 18
WEEKDAYS = range(5)  # Monday is 0.

BLOCKED_TOOLS = frozenset({"Task", "Agent", "Workflow", "WebSearch", "WebFetch"})
MCP_PREFIX = "mcp__"
BASH_LIVE_WORDS = ("optimize", "certify", "evals", "nightly")
BASH_PACKAGE_TOKENS = ("dspy_gate", "dspy-gate")
OVERRIDE_ENV = "ZAI_PEAK_HOURS_OVERRIDE"

_DENY_MESSAGE = (
    "peak-hours-gate: denied {tool} — the z.ai peak window is "
    "Monday to Friday, 14:00 to 18:00 SGT (UTC+8). "
    "Set {override}=1 in the session environment to bypass for an emergency."
)


def sgt(moment):
    """Return the SGT wall clock for one aware datetime."""
    return moment.astimezone(timezone.utc) + SGT_OFFSET


def is_peak(moment):
    """Return True when the instant sits in the window, in SGT terms."""
    local = sgt(moment)
    if local.weekday() not in WEEKDAYS:
        return False
    return WINDOW_START <= local.hour < WINDOW_END


def _bash_denies(command):
    """Return True when the command runs a dspy_gate live path."""
    tokens = command.split()
    for left, right in zip(tokens, tokens[1:]):
        if left in BASH_PACKAGE_TOKENS and right in BASH_LIVE_WORDS:
            return True
    return False


def decide(event, now, override):
    """Decide one hook event. Return (exit_code, stderr message).

    The only deny path is a positive in-window match on the block set.
    Every unusable input returns (0, "") so a gate fault never stops a
    session.
    """
    if not isinstance(event, dict):
        return 0, ""
    name = event.get("tool_name")
    if not isinstance(name, str) or not name:
        return 0, ""
    if override == "1":
        return 0, ""
    if not is_peak(now):
        return 0, ""
    return _deny_or_allow(name, event)


def _deny_or_allow(name, event):
    """Return the verdict for one usable event name in the window."""
    if name in BLOCKED_TOOLS or name.startswith(MCP_PREFIX):
        return 2, _deny_message(name)
    if name == "Bash":
        tool_input = event.get("tool_input")
        command = tool_input.get("command") if isinstance(tool_input, dict) else None
        if isinstance(command, str) and _bash_denies(command):
            return 2, _deny_message(name)
    return 0, ""


def _deny_message(tool):
    return _DENY_MESSAGE.format(tool=tool, override=OVERRIDE_ENV)


def describe(now):
    """Return the state line for the status subcommand."""
    local = sgt(now)
    if is_peak(now):
        close = datetime.combine(local.date(), time(WINDOW_END))
        boundary = "the window closes at " + close.strftime("%a %H:%M SGT")
        state = "in the peak window"
    else:
        boundary = _next_open(local)
        state = "outside the peak window"
    return state + ". " + boundary


def _next_open(local):
    """Return the next window open line on the SGT calendar."""
    day = local.date()
    if local.hour >= WINDOW_START or local.weekday() not in WEEKDAYS:
        day += timedelta(days=1)
    candidate = datetime.combine(day, time(WINDOW_START))
    while candidate.weekday() not in WEEKDAYS:
        day += timedelta(days=1)
        candidate = datetime.combine(day, time(WINDOW_START))
    return "the next window opens at " + candidate.strftime("%a %H:%M SGT")
