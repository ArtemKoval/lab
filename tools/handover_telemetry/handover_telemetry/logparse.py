"""The reader for the cc-logging hook log and the pairing with the
transcript. A hook record is one JSON line with a small field set.
The pairing joins Pre and Post records on the tool use id, and the
hook duration replaces the duration derived from transcript
timestamps for the same call. A missing log degrades cleanly."""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .transcript import ToolCall


@dataclass
class HookRecord:
    ts: str | None
    event: str
    session_id: str | None
    tool: str | None
    tool_use_id: str | None
    hook_ms: float | None
    outcome: str | None
    redactions: dict


def load_hook_log(path: Path | None) -> list[HookRecord]:
    if path is None or not path.is_file():
        return []
    records = []
    # pragma: no mutate start - the locale default equals utf-8 here
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        # pragma: no mutate end - the locale default equals utf-8 here
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except ValueError:
            continue
        if isinstance(data, dict):
            records.append(_record_from(data))
    return records


def _record_from(data: dict) -> HookRecord:
    return HookRecord(
        ts=data.get("ts"),
        event=data.get("event") or "",
        session_id=data.get("session_id"),
        tool=data.get("tool"),
        tool_use_id=data.get("tool_use_id"),
        hook_ms=data.get("hook_ms"),
        outcome=data.get("outcome"),
        redactions=data.get("redactions") or {},
    )


def _ts_ms(stamp: str | None) -> float | None:
    if not stamp:
        return None
    try:
        moment = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        return None
    return moment.timestamp() * 1000.0


def pair_durations(records: list[HookRecord]) -> dict[str, float]:
    starts: dict[str, float] = {}
    durations: dict[str, float] = {}
    for record in records:
        key = record.tool_use_id
        if not key:
            continue
        if record.event == "PreToolUse":
            start = _ts_ms(record.ts)
            if start is not None:
                starts[key] = start
        elif record.event == "PostToolUse" and key in starts:
            end = _ts_ms(record.ts)
            if end is not None:
                durations[key] = end - starts[key]
    return durations


def derived_duration_ms(call: ToolCall) -> float | None:
    start = _ts_ms(call.start)
    end = _ts_ms(call.end)
    if start is None or end is None:
        return None
    return end - start


def apply_hook_durations(tool_calls: list[ToolCall], hook_log: Path | None) -> int:
    durations = pair_durations(load_hook_log(hook_log))
    replaced = 0
    for call in tool_calls:
        if call.id in durations:
            call.duration_ms = durations[call.id]
            replaced += 1
        else:
            call.duration_ms = derived_duration_ms(call)
    return replaced


def permission_events(records: list[HookRecord]) -> list[dict]:
    return [
        {"ts": r.ts, "tool": r.tool}
        for r in records
        if r.event == "PermissionRequest"
    ]


def event_counts(records: list[HookRecord]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        counts[record.event] = counts.get(record.event, 0) + 1
    return counts
