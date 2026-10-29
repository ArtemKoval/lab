"""Tests for the hook log reader and the pairing with transcript
tool calls: durations replace derived values, permission events
surface, and a missing log degrades cleanly."""

from pathlib import Path

import pytest
from handover_telemetry import logparse, transcript

FIXTURES = Path(__file__).parent / "fixtures"
SESSION_DIR = FIXTURES / "session"
HOOK_LOG = FIXTURES / "hook" / "sess-1.jsonl"


@pytest.fixture()
def session(tmp_path) -> transcript.Session:
    main = tmp_path / "main.jsonl"
    main.write_text((SESSION_DIR / "main.jsonl").read_text(encoding="utf-8"), encoding="utf-8")
    return transcript.parse_session(main)


def test_load_hook_log_reads_all_records():
    records = logparse.load_hook_log(HOOK_LOG)
    assert len(records) == 6
    assert records[0].event == "PreToolUse"


def test_load_hook_log_skips_malformed_lines(tmp_path):
    path = tmp_path / "bad.jsonl"
    path.write_text('{"event": "Stop"}\nnot json\n', encoding="utf-8")
    records = logparse.load_hook_log(path)
    assert len(records) == 1


def test_load_hook_log_missing_file_yields_nothing(tmp_path):
    assert logparse.load_hook_log(tmp_path / "none.jsonl") == []


def test_pair_durations_computes_pre_to_post_span():
    records = logparse.load_hook_log(HOOK_LOG)
    durations = logparse.pair_durations(records)
    assert durations["toolu_1"] == pytest.approx(1960.0)
    assert durations["toolu_2"] == pytest.approx(1000.0)


def test_pair_durations_ignores_post_without_pre():
    records = logparse.load_hook_log(HOOK_LOG)
    records = [r for r in records if r.tool_use_id != "toolu_1" or r.event != "PreToolUse"]
    durations = logparse.pair_durations(records)
    assert "toolu_1" not in durations


def test_hook_duration_replaces_derived_duration(session):
    calls = {c.id: c for c in session.primary.tool_calls}
    replaced = logparse.apply_hook_durations(session.primary.tool_calls, HOOK_LOG)
    assert calls["toolu_1"].duration_ms == pytest.approx(1960.0)
    assert replaced == 2


def test_derived_duration_fills_the_gap(session):
    calls = {c.id: c for c in session.primary.tool_calls}
    logparse.apply_hook_durations(session.primary.tool_calls, HOOK_LOG)
    assert calls["toolu_2"].duration_ms == pytest.approx(1000.0)


def test_unpaired_call_keeps_none_duration(session):
    calls = {c.id: c for c in session.primary.tool_calls}
    logparse.apply_hook_durations(session.primary.tool_calls, HOOK_LOG)
    assert calls["toolu_4"].duration_ms is None


def test_missing_log_degrades_to_derived_durations(session):
    calls = {c.id: c for c in session.primary.tool_calls}
    logparse.apply_hook_durations(session.primary.tool_calls, None)
    assert calls["toolu_1"].duration_ms == pytest.approx(2000.0)
    assert calls["toolu_4"].duration_ms is None


def test_permission_events_surface():
    records = logparse.load_hook_log(HOOK_LOG)
    events = logparse.permission_events(records)
    assert events == [{"ts": "2026-10-29T10:00:16.000Z", "tool": "Bash"}]


def test_event_counts_summarize_the_run():
    counts = logparse.event_counts(logparse.load_hook_log(HOOK_LOG))
    assert counts == {"PreToolUse": 2, "PostToolUse": 2, "PermissionRequest": 1, "Stop": 1}


def test_event_counts_of_nothing_is_empty():
    assert logparse.event_counts([]) == {}


def test_blank_and_nondict_lines_are_skipped(tmp_path):
    path = tmp_path / "junk.jsonl"
    path.write_text('\n{"event": "Stop"}\n[1]\n', encoding="utf-8")
    assert len(logparse.load_hook_log(path)) == 1


def test_bad_timestamp_yields_no_derived_duration(session):
    calls = session.primary.tool_calls
    calls[0].start = "not-a-time"
    assert logparse.derived_duration_ms(calls[0]) is None


def test_missing_start_yields_no_derived_duration(session):
    calls = session.primary.tool_calls
    calls[0].start = None
    assert logparse.derived_duration_ms(calls[0]) is None


def test_post_with_bad_timestamp_yields_no_duration():
    records = [
        logparse.HookRecord("2026-01-01T00:00:00Z", "PreToolUse", "s", "Bash", "t1", 1, None, {}),
        logparse.HookRecord("bad", "PostToolUse", "s", "Bash", "t1", 1, None, {}),
    ]
    assert logparse.pair_durations(records) == {}


def test_a_bad_pre_stamp_keeps_the_derived_duration(session, tmp_path):
    log = tmp_path / "bad-pre.jsonl"
    log.write_text(
        '{"ts": "junk", "event": "PreToolUse", "tool_use_id": "toolu_1"}\n'
        '{"ts": "2026-01-01T00:00:09Z", "event": "PostToolUse", "tool_use_id": "toolu_1"}\n',
        encoding="utf-8",
    )
    calls = {c.id: c for c in session.primary.tool_calls}
    logparse.apply_hook_durations(session.primary.tool_calls, log)
    assert calls["toolu_1"].duration_ms == pytest.approx(2000.0)
