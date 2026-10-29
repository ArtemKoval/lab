"""Tests for the cc-logging hook: one line per event, write-time
redaction, self timing, and the always exit 0 contract."""

import io
import json
import sys
from pathlib import Path

from handover_telemetry import hook, logparse


def _event(data: dict) -> io.StringIO:
    return io.StringIO(json.dumps(data))


def _run(monkeypatch, data: dict, root: Path) -> int:
    monkeypatch.setattr(sys, "stdin", _event(data))
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(root))
    return hook.main([])


def test_event_appends_one_line(monkeypatch, tmp_path):
    code = _run(
        monkeypatch,
        {"hook_event_name": "PreToolUse", "session_id": "s1", "tool_name": "Bash", "tool_use_id": "t1"},
        tmp_path,
    )
    assert code == 0
    lines = (tmp_path / ".cc_logging" / "s1.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["event"] == "PreToolUse"
    assert record["tool"] == "Bash"
    assert record["tool_use_id"] == "t1"


def test_second_event_appends(monkeypatch, tmp_path):
    first = {"hook_event_name": "PreToolUse", "session_id": "s1", "tool_name": "Bash", "tool_use_id": "t1"}
    second = {"hook_event_name": "PostToolUse", "session_id": "s1", "tool_name": "Bash", "tool_use_id": "t1"}
    _run(monkeypatch, first, tmp_path)
    _run(monkeypatch, second, tmp_path)
    lines = (tmp_path / ".cc_logging" / "s1.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    records = logparse.load_hook_log(tmp_path / ".cc_logging" / "s1.jsonl")
    assert logparse.pair_durations(records)


def test_secret_in_a_field_is_redacted(monkeypatch, tmp_path):
    code = _run(
        monkeypatch,
        {"hook_event_name": "PreToolUse", "session_id": "s1", "tool_name": "gho_AAAABBBBCCCCDDDDEEEEFFFFGGGGHHH1"},
        tmp_path,
    )
    assert code == 0
    text = (tmp_path / ".cc_logging" / "s1.jsonl").read_text(encoding="utf-8")
    assert "gho_AAAABBBB" not in text
    record = json.loads(text.splitlines()[0])
    assert record["redactions"].get("token") == 1


def test_hook_self_duration_recorded(monkeypatch, tmp_path):
    _run(monkeypatch, {"hook_event_name": "Stop", "session_id": "s1"}, tmp_path)
    record = json.loads(
        (tmp_path / ".cc_logging" / "s1.jsonl").read_text(encoding="utf-8").splitlines()[0]
    )
    assert isinstance(record["hook_ms"], (int, float))
    assert record["hook_ms"] >= 0


def test_missing_session_id_writes_nothing(monkeypatch, tmp_path):
    code = _run(monkeypatch, {"hook_event_name": "Stop"}, tmp_path)
    assert code == 0
    assert not (tmp_path / ".cc_logging").exists()


def test_a_traversal_session_id_stays_inside_the_log_dir(monkeypatch, tmp_path):
    code = _run(
        monkeypatch, {"hook_event_name": "Stop", "session_id": "../../evil"}, tmp_path
    )
    assert code == 0
    assert sorted(p.name for p in tmp_path.iterdir()) == [".cc_logging"]
    assert sorted(p.name for p in (tmp_path / ".cc_logging").iterdir()) == [
        ".-.-evil.jsonl"
    ]


def test_the_session_id_is_sanitized_for_the_log_name():
    assert hook._safe_session_id("../../evil") == ".-.-evil"
    assert hook._safe_session_id("s1") == "s1"
    assert hook._safe_session_id("a..b") == "a.b"
    assert hook._safe_session_id("") == ""
    assert hook._safe_session_id(None) == ""
    assert hook._safe_session_id(7) == ""


def test_garbage_stdin_exits_zero(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "stdin", io.StringIO("not json"))
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    assert hook.main([]) == 0


def test_empty_stdin_exits_zero(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    assert hook.main([]) == 0


def test_broken_root_exits_zero(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "stdin", _event({"hook_event_name": "Stop", "session_id": "s1"}))
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path / "no-such"))
    assert hook.main([]) == 0


def test_permission_event_drops_the_decision(monkeypatch, tmp_path):
    _run(
        monkeypatch,
        {"hook_event_name": "PermissionRequest", "session_id": "s1", "tool_name": "Bash", "decision": "deny"},
        tmp_path,
    )
    record = json.loads(
        (tmp_path / ".cc_logging" / "s1.jsonl").read_text(encoding="utf-8").splitlines()[0]
    )
    assert "decision" not in record


def test_post_event_derives_outcome(monkeypatch, tmp_path):
    _run(
        monkeypatch,
        {
            "hook_event_name": "PostToolUse",
            "session_id": "s1",
            "tool_name": "Bash",
            "tool_use_id": "t1",
            "tool_response": {"is_error": False},
        },
        tmp_path,
    )
    record = json.loads(
        (tmp_path / ".cc_logging" / "s1.jsonl").read_text(encoding="utf-8").splitlines()[0]
    )
    assert record["outcome"] == "ok"


def test_handle_event_crash_still_exits_zero(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "stdin", _event({"hook_event_name": "Stop", "session_id": "s1"}))
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    monkeypatch.setattr(hook, "handle_event", lambda raw: (_ for _ in ()).throw(RuntimeError("boom")))
    assert hook.main([]) == 0


def test_append_failure_is_swallowed(monkeypatch, tmp_path):
    def boom(path, record):
        raise OSError("disk gone")

    monkeypatch.setattr(hook, "_append", boom)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    monkeypatch.setattr(sys, "stdin", _event({"hook_event_name": "Stop", "session_id": "s1"}))
    assert hook.main([]) == 0


def test_post_event_error_outcome(monkeypatch, tmp_path):
    _run(
        monkeypatch,
        {
            "hook_event_name": "PostToolUse",
            "session_id": "s1",
            "tool_name": "Bash",
            "tool_use_id": "t1",
            "tool_response": {"is_error": True},
        },
        tmp_path,
    )
    record = json.loads(
        (tmp_path / ".cc_logging" / "s1.jsonl").read_text(encoding="utf-8").splitlines()[0]
    )
    assert record["outcome"] == "error"


def test_post_event_success_false_is_an_error(monkeypatch, tmp_path):
    _run(
        monkeypatch,
        {
            "hook_event_name": "PostToolUse",
            "session_id": "s1",
            "tool_name": "Bash",
            "tool_use_id": "t1",
            "tool_response": {"success": False},
        },
        tmp_path,
    )
    record = json.loads(
        (tmp_path / ".cc_logging" / "s1.jsonl").read_text(encoding="utf-8").splitlines()[0]
    )
    assert record["outcome"] == "error"


def test_post_event_success_true_is_ok(monkeypatch, tmp_path):
    _run(
        monkeypatch,
        {
            "hook_event_name": "PostToolUse",
            "session_id": "s1",
            "tool_name": "Bash",
            "tool_use_id": "t1",
            "tool_response": {"success": True},
        },
        tmp_path,
    )
    record = json.loads(
        (tmp_path / ".cc_logging" / "s1.jsonl").read_text(encoding="utf-8").splitlines()[0]
    )
    assert record["outcome"] == "ok"


def test_post_event_without_outcome_fields_is_none(monkeypatch, tmp_path):
    _run(
        monkeypatch,
        {
            "hook_event_name": "PostToolUse",
            "session_id": "s1",
            "tool_name": "Bash",
            "tool_use_id": "t1",
        },
        tmp_path,
    )
    record = json.loads(
        (tmp_path / ".cc_logging" / "s1.jsonl").read_text(encoding="utf-8").splitlines()[0]
    )
    assert record["outcome"] is None


def test_post_event_with_an_empty_response_is_none(monkeypatch, tmp_path):
    _run(
        monkeypatch,
        {
            "hook_event_name": "PostToolUse",
            "session_id": "s1",
            "tool_name": "Bash",
            "tool_use_id": "t1",
            "tool_response": {},
        },
        tmp_path,
    )
    record = json.loads(
        (tmp_path / ".cc_logging" / "s1.jsonl").read_text(encoding="utf-8").splitlines()[0]
    )
    assert record["outcome"] is None
