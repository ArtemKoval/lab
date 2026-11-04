"""The CLI of the peak-hours gate: check and status.

The `check` subcommand reads one hook event on stdin and decides. The
`status` subcommand reports the window state for a human. The exit
contract: 0 on allow, 2 on deny, and 0 with no output on any internal
error, so a gate fault never stops a session.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

from . import core

ENV_SEAM = "PEAK_HOURS_GATE_NOW"


def main(argv=None, stdin=None):
    parser = argparse.ArgumentParser(
        prog="peak_hours_gate",
        description="Static gate for the z.ai peak window.",
    )
    parser.add_argument("command", choices=["check", "status"])
    parser.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="print machine-readable output on stdout",
    )
    parser.add_argument(
        "--now",
        default=None,
        help="ISO 8601 UTC instant to decide against; default: the real clock",
    )
    args = parser.parse_args(argv)
    stream = sys.stdin if stdin is None else stdin
    try:
        return _run(args, stream)
    except Exception:
        # Fail open: an unusable clock or stream allows the call.
        return 0


def _run(args, stream):
    now = _resolve_now(args.now)
    if args.command == "status":
        return _status(now, args.as_json)
    return _check(now, args.as_json, stream)


def _resolve_now(flag_value):
    if flag_value:
        return _parse_instant(flag_value)
    seam = os.environ.get(ENV_SEAM)
    if seam:
        return _parse_instant(seam)
    return datetime.now(timezone.utc)


def _parse_instant(text):
    parsed = datetime.fromisoformat(text.strip())
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _check(now, as_json, stream):
    event = _read_event(stream)
    override = os.environ.get(core.OVERRIDE_ENV)
    code, message = core.decide(event, now, override)
    if as_json:
        payload = {
            "decision": "deny" if code == 2 else "allow",
            "reason": message,
            "tool": _tool_name(event),
        }
        print(json.dumps(payload))
    elif message:
        print(message, file=sys.stderr)
    return code


def _read_event(stream):
    """Read one hook event. Return None for any unusable stream or text."""
    try:
        return json.loads(stream.read())
    except (OSError, ValueError, TypeError):
        return None


def _tool_name(event):
    if isinstance(event, dict):
        name = event.get("tool_name")
        if isinstance(name, str):
            return name
    return ""


def _status(now, as_json):
    if as_json:
        payload = {
            "sgt": core.sgt(now).isoformat(),
            "in_window": core.is_peak(now),
            "boundary": core.describe(now),
        }
        print(json.dumps(payload))
    else:
        print(core.describe(now))
    return 0
