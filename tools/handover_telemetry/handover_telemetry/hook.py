"""The cc-logging hook: one redacted JSON line per session event.

The hook reads the event on standard input, selects a small field set,
scrubs every string through the shared redactor, and appends one line
to `<repo>/.cc_logging/<session-id>.jsonl`. It records its own
duration and always exits 0, so a hook failure never stops a session.
A missing session id writes nothing.
"""

import json
import os
import re
import sys
import time
from pathlib import Path

from .redact import Redactor

_STARTED = time.perf_counter()
_SAFE_ID = re.compile(r"[^A-Za-z0-9._-]")


def main(argv: list[str] | None = None) -> int:
    try:
        handle_event(sys.stdin.read())
    except Exception:  # noqa: BLE001 - the hook never fails a session
        return 0
    return 0


def _safe_session_id(raw: object) -> str:
    if not isinstance(raw, str):
        return ""
    return _SAFE_ID.sub("-", raw).replace("..", ".")


def handle_event(raw: str) -> None:
    data = _parse(raw)
    if not isinstance(data, dict):
        return
    session_id = _safe_session_id(data.get("session_id"))
    if not session_id:
        return
    record = _record(data)
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd())
    log_dir = root / ".cc_logging"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        _append(log_dir / f"{session_id}.jsonl", record)
    except OSError:
        return


def _parse(raw: str) -> object:
    try:
        return json.loads(raw)
    except ValueError:
        return None


def _record(data: dict) -> dict:
    record = {
        "ts": _now_iso(),
        "event": data.get("hook_event_name") or "",
        "session_id": data.get("session_id"),
        "tool": data.get("tool_name"),
        "tool_use_id": data.get("tool_use_id"),
        "outcome": _outcome(data),
        "hook_ms": round((time.perf_counter() - _STARTED) * 1000.0, 2),
    }
    scrubber = Redactor()
    clean = scrubber.scrub_value(record)
    clean["redactions"] = dict(scrubber.counts)
    return clean


def _outcome(data: dict) -> str | None:
    if data.get("hook_event_name") != "PostToolUse":
        return None
    response = data.get("tool_response")
    if not isinstance(response, dict):
        return None
    if "is_error" not in response and "success" not in response:
        return None
    if response.get("is_error") or response.get("success") is False:
        return "error"
    return "ok"


def _now_iso() -> str:
    stamp = time.time()
    seconds = int(stamp)
    millis = int((stamp - seconds) * 1000)
    base = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(seconds))
    return f"{base}.{millis:03d}Z"


def _append(path: Path, record: dict) -> None:
    # the locale default equals utf-8, so the encoding alternatives behave the same
    with path.open("a", encoding="utf-8") as handle:  # pragma: no mutate
        handle.write(json.dumps(record, sort_keys=True) + "\n")


if __name__ == "__main__":  # pragma: no cover - the shim calls -m
    raise SystemExit(main())
