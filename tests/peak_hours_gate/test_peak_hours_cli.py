"""Tests for the CLI surface: check, status, --json, --now, env seam.

The tests drive main() the way the shim drives it: one event on stdin,
flags on the command line, and the exit code as the verdict.
"""

import io
import json

from peak_hours_gate import cli

IN_WINDOW_NOW = "2026-11-03T07:00:00Z"  # 15:00 SGT Tuesday
OUT_WINDOW_NOW = "2026-11-03T11:00:00Z"  # 19:00 SGT Tuesday


def _run(argv, stdin_text="", env_value=None):
    stream = io.StringIO(stdin_text)
    err = io.StringIO()
    out = io.StringIO()
    import sys

    old = (sys.stdin, sys.stderr, sys.stdout)
    sys.stdin, sys.stderr, sys.stdout = stream, err, out
    try:
        code = cli.main(argv)
    finally:
        sys.stdin, sys.stderr, sys.stdout = old
    return code, out.getvalue(), err.getvalue()


def test_check_denies_in_window():
    event = json.dumps({"tool_name": "Task"})
    code, _, err = _run(["check", "--now", IN_WINDOW_NOW], event)
    assert code == 2
    assert "14:00" in err
    assert "ZAI_PEAK_HOURS_OVERRIDE" in err


def test_check_allows_outside_window_and_stays_silent():
    event = json.dumps({"tool_name": "Task"})
    code, out, err = _run(["check", "--now", OUT_WINDOW_NOW], event)
    assert code == 0
    assert out == ""
    assert err == ""


def test_check_json_output_parses():
    event = json.dumps({"tool_name": "mcp__x__y"})
    code, out, _ = _run(["check", "--json", "--now", IN_WINDOW_NOW], event)
    assert code == 2
    payload = json.loads(out)
    assert payload["decision"] == "deny"
    assert payload["reason"]
    assert payload["tool"] == "mcp__x__y"


def test_check_env_seam_sets_the_clock(monkeypatch):
    monkeypatch.setenv("PEAK_HOURS_GATE_NOW", IN_WINDOW_NOW)
    event = json.dumps({"tool_name": "Workflow"})
    code, _, _ = _run(["check"], event)
    assert code == 2


def test_check_malformed_stdin_fails_open():
    code, out, err = _run(["check", "--now", IN_WINDOW_NOW], "not json")
    assert code == 0
    assert out == ""
    assert err == ""


def test_check_empty_event_fails_open():
    code, _, _ = _run(["check", "--now", IN_WINDOW_NOW], "{}")
    assert code == 0


def test_check_naive_now_reads_as_utc():
    event = json.dumps({"tool_name": "Task"})
    code, _, _ = _run(["check", "--now", "2026-11-03T07:00:00"], event)
    assert code == 2


def test_check_bad_now_fails_open():
    event = json.dumps({"tool_name": "Task"})
    code, _, _ = _run(["check", "--now", "not-a-date"], event)
    assert code == 0


def test_check_real_clock_runs(monkeypatch):
    monkeypatch.delenv("PEAK_HOURS_GATE_NOW", raising=False)
    event = json.dumps({"tool_name": "Read"})
    code, _, _ = _run(["check"], event)
    assert code == 0


def test_check_empty_stdin_fails_open():
    code, out, err = _run(["check", "--now", IN_WINDOW_NOW], "")
    assert code == 0
    assert out == ""
    assert err == ""


def test_check_unreadable_stream_fails_open():
    class Broken:
        def read(self):
            raise OSError("no stream")

    import sys

    old = sys.stdin
    sys.stdin = Broken()
    try:
        code = cli.main(["check", "--now", IN_WINDOW_NOW])
    finally:
        sys.stdin = old
    assert code == 0


def test_check_json_malformed_event_names_no_tool():
    code, out, _ = _run(["check", "--json", "--now", IN_WINDOW_NOW], "not json")
    assert code == 0
    payload = json.loads(out)
    assert payload["tool"] == ""
    assert payload["decision"] == "allow"


def test_check_json_non_string_tool_names_no_tool():
    event = json.dumps({"tool_name": 5})
    code, out, _ = _run(["check", "--json", "--now", IN_WINDOW_NOW], event)
    assert code == 0
    payload = json.loads(out)
    assert payload["tool"] == ""
    assert payload["decision"] == "allow"


def test_status_reports_state_and_boundary():
    code, out, err = _run(["status", "--now", IN_WINDOW_NOW])
    assert code == 0
    assert "in the peak window" in out
    assert "18:00" in out


def test_status_json_parses():
    code, out, _ = _run(["status", "--json", "--now", IN_WINDOW_NOW])
    assert code == 0
    payload = json.loads(out)
    assert payload["in_window"] is True
    assert payload["boundary"]
    assert payload["sgt"]


def test_status_outside_window_names_next_open():
    code, out, _ = _run(["status", "--now", OUT_WINDOW_NOW])
    assert code == 0
    assert "outside the peak window" in out
    assert "opens at" in out
