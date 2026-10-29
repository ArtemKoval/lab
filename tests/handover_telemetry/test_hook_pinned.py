"""Pinned tests for the cc-logging hook: the exact record dict with a
stubbed clock, the exact log line, and the project dir resolution."""

import json

from handover_telemetry import hook


def _stub_clock(monkeypatch):
    monkeypatch.setattr(hook, "_STARTED", 10.0)
    monkeypatch.setattr(hook.time, "perf_counter", lambda: 10.123456)
    monkeypatch.setattr(hook.time, "time", lambda: 1767225600.9999)


def test_record_fields_and_timing_are_pinned(monkeypatch):
    _stub_clock(monkeypatch)
    got = hook._record(
        {
            "hook_event_name": "PreToolUse",
            "session_id": "s1",
            "tool_name": "Bash",
            "tool_use_id": "t1",
        }
    )
    assert got == {
        "ts": "2026-01-01T00:00:00.999Z",
        "event": "PreToolUse",
        "session_id": "s1",
        "tool": "Bash",
        "tool_use_id": "t1",
        "outcome": None,
        "hook_ms": 123.46,
        "redactions": {},
    }


def test_record_defaults_for_missing_fields(monkeypatch):
    _stub_clock(monkeypatch)
    got = hook._record({"session_id": "s2"})
    assert got == {
        "ts": "2026-01-01T00:00:00.999Z",
        "event": "",
        "session_id": "s2",
        "tool": None,
        "tool_use_id": None,
        "outcome": None,
        "hook_ms": 123.46,
        "redactions": {},
    }


def test_record_drops_the_decision_field(monkeypatch):
    _stub_clock(monkeypatch)
    got = hook._record(
        {
            "hook_event_name": "PermissionRequest",
            "session_id": "s1",
            "tool_name": "Bash",
            "decision": "deny",
        }
    )
    assert "decision" not in got


def test_post_error_outcome_is_error(monkeypatch):
    _stub_clock(monkeypatch)
    got = hook._record(
        {
            "hook_event_name": "PostToolUse",
            "session_id": "s1",
            "tool_response": {"is_error": True},
        }
    )
    assert got["outcome"] == "error"


def test_append_writes_one_sorted_line(tmp_path):
    path = tmp_path / "s1.jsonl"
    record = {
        "ts": "t",
        "event": "Stop",
        "session_id": "s1",
        "tool": None,
        "tool_use_id": None,
        "outcome": None,
        "hook_ms": 1.0,
        "redactions": {},
    }
    hook._append(path, record)
    assert path.read_text(encoding="utf-8") == (
        '{"event": "Stop", "hook_ms": 1.0, "outcome": null,'
        ' "redactions": {}, "session_id": "s1", "tool": null, "tool_use_id": null,'
        ' "ts": "t"}\n'
    )


def test_handle_event_targets_the_project_dir(monkeypatch, tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.chdir(work)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    hook.handle_event(json.dumps({"hook_event_name": "Stop", "session_id": "s1"}))
    assert (tmp_path / ".cc_logging" / "s1.jsonl").is_file()
    assert not (work / ".cc_logging").exists()


def test_handle_event_without_env_uses_the_cwd(monkeypatch, tmp_path):
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    monkeypatch.chdir(tmp_path)
    hook.handle_event(json.dumps({"hook_event_name": "Stop", "session_id": "s1"}))
    assert (tmp_path / ".cc_logging" / "s1.jsonl").is_file()


def test_handle_event_creates_missing_dirs(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path / "deep" / "root"))
    hook.handle_event(json.dumps({"hook_event_name": "Stop", "session_id": "s1"}))
    assert (tmp_path / "deep" / "root" / ".cc_logging" / "s1.jsonl").is_file()


def test_handle_event_appends_to_an_existing_log(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    hook.handle_event(json.dumps({"hook_event_name": "Stop", "session_id": "s1"}))
    hook.handle_event(json.dumps({"hook_event_name": "Stop", "session_id": "s1"}))
    lines = (tmp_path / ".cc_logging" / "s1.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2


def test_handle_event_without_a_session_writes_nothing(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    hook.handle_event(json.dumps({"hook_event_name": "Stop"}))
    assert not (tmp_path / ".cc_logging").exists()


def test_handle_event_with_garbage_writes_nothing(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    hook.handle_event("not json")
    assert not (tmp_path / ".cc_logging").exists()
