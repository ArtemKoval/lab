"""Pinned tests for the hook log reader: the exact HookRecord fields,
the nondict filter, the pairing edge stamps, and the derived duration."""

from handover_telemetry import logparse, transcript


def _write(path, lines):
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_record_fields_are_pinned(tmp_path):
    path = _write(
        tmp_path / "log.jsonl",
        [
            '{"ts": "2026-01-01T00:00:01Z", "event": "PostToolUse", "session_id": "s1",'
            ' "tool": "Bash", "tool_use_id": "t1", "hook_ms": 3, "outcome": "exit_1",'
            ' "decision": "deny", "redactions": {"home_path": 2}}',
            '{"session_id": "s9"}',
        ],
    )
    assert logparse.load_hook_log(path) == [
        logparse.HookRecord(
            ts="2026-01-01T00:00:01Z",
            event="PostToolUse",
            session_id="s1",
            tool="Bash",
            tool_use_id="t1",
            hook_ms=3,
            outcome="exit_1",
            decision="deny",
            redactions={"home_path": 2},
        ),
        logparse.HookRecord(
            ts=None,
            event="",
            session_id="s9",
            tool=None,
            tool_use_id=None,
            hook_ms=None,
            outcome=None,
            decision=None,
            redactions={},
        ),
    ]


def test_nondict_json_line_is_skipped(tmp_path):
    path = _write(tmp_path / "mix.jsonl", ["[1]", '{"event": "Stop"}'])
    records = logparse.load_hook_log(path)
    assert len(records) == 1
    assert records[0].event == "Stop"


def test_junk_line_between_records_keeps_the_rest(tmp_path):
    path = _write(
        tmp_path / "mid.jsonl", ['{"event": "A"}', "not json", '{"event": "B"}']
    )
    records = logparse.load_hook_log(path)
    assert [r.event for r in records] == ["A", "B"]


def test_bad_bytes_are_replaced_not_fatal(tmp_path):
    path = tmp_path / "bytes.jsonl"
    path.write_bytes(b'{"event": "A"}\n\xff broken\n{"event": "B"}\n')
    records = logparse.load_hook_log(path)
    assert [r.event for r in records] == ["A", "B"]


def test_a_keyless_record_does_not_stop_the_pairing():
    records = [
        logparse.HookRecord("t", "Stop", None, None, None, None, None, None, {}),
        logparse.HookRecord(
            "2026-01-01T00:00:01Z", "PreToolUse", None, None, "t1", None, None, None, {}
        ),
        logparse.HookRecord(
            "2026-01-01T00:00:03Z", "PostToolUse", None, None, "t1", None, None, None, {}
        ),
    ]
    assert logparse.pair_durations(records) == {"t1": 2000.0}


def test_pair_duration_with_bad_pre_stamp_uses_the_zero_base():
    records = [
        logparse.HookRecord("junk", "PreToolUse", None, None, "t1", None, None, None, {}),
        logparse.HookRecord(
            "2026-01-01T00:00:10Z", "PostToolUse", None, None, "t1", None, None, None, {}
        ),
    ]
    assert logparse.pair_durations(records) == {"t1": 1767225610000.0}


def test_lowercase_z_stamp_never_parses():
    records = [
        logparse.HookRecord(
            "2026-01-01T00:00:00Z", "PreToolUse", None, None, "t1", None, None, None, {}
        ),
        logparse.HookRecord(
            "2026-01-01T00:00:10z", "PostToolUse", None, None, "t1", None, None, None, {}
        ),
    ]
    assert logparse.pair_durations(records) == {}


def test_a_second_pre_stamp_replaces_the_first():
    records = [
        logparse.HookRecord(
            "2026-01-01T00:00:01Z", "PreToolUse", None, None, "t1", None, None, None, {}
        ),
        logparse.HookRecord(
            "2026-01-01T00:00:05Z", "PreToolUse", None, None, "t1", None, None, None, {}
        ),
        logparse.HookRecord(
            "2026-01-01T00:00:07Z", "PostToolUse", None, None, "t1", None, None, None, {}
        ),
    ]
    assert logparse.pair_durations(records) == {"t1": 2000.0}


def test_derived_duration_is_exact_milliseconds():
    call = transcript.ToolCall(
        "t", "Bash", {}, "2026-01-01T00:00:00Z", "2026-01-01T00:00:02Z"
    )
    assert logparse.derived_duration_ms(call) == 2000.0


def test_permission_events_of_nothing_is_empty():
    assert logparse.permission_events([]) == []
