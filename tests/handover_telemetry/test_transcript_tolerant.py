"""Tolerance tests for the transcript parser: junk lines, missing
fields, and odd content blocks never break the parse."""

from pathlib import Path

from handover_telemetry import transcript


def _write(path: Path, lines: list[str]) -> Path:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_blank_and_nondict_lines_are_counted_but_ignored(tmp_path):
    path = _write(tmp_path / "junk.jsonl", ['{"type": "mode"}', "", "[1, 2]", "oops", '{"type": "user"}'])
    session = transcript.parse_session(path)
    assert session.entry_count == 3
    assert session.primary.turns == []


def test_sidechain_entry_without_agentid_keeps_stem(tmp_path):
    main = _write(
        tmp_path / "s1.jsonl",
        [
            '{"type": "user", "sessionId": "s1", "timestamp": "2026-01-01T00:00:00Z"}',
            '{"type": "assistant", "isSidechain": true, "timestamp": "2026-01-01T00:00:01Z"}',
        ],
    )
    sub = tmp_path / "s1" / "subagents"
    sub.mkdir(parents=True)
    _write(
        sub / "agent-9.jsonl",
        ['{"type": "mode"}', "[1, 2]", '{"type": "assistant", "message": {"id": "m", "model": "x", "usage": {}}}'],
    )
    session = transcript.parse_session(main)
    assert session.sidechains[0].agent_id == "agent-9"
    assert session.sidechains[0].turns[0].message_id == "m"
    assert session.primary.turns == []


def test_sidechain_prompt_does_not_touch_session(tmp_path):
    main = _write(
        tmp_path / "s1.jsonl",
        ['{"type": "user", "sessionId": "s1", "timestamp": "2026-01-01T00:00:00Z", "message": {"content": "go"}}'],
    )
    sub = tmp_path / "s1" / "subagents"
    sub.mkdir(parents=True)
    _write(sub / "agent-3.jsonl", ['{"type": "user", "message": {"content": "inner prompt"}}'])
    session = transcript.parse_session(main)
    assert session.first_prompt_ts == "2026-01-01T00:00:00Z"
    assert session.sidechains[0].prompt_count == 1


def test_text_block_content_counts_as_prompt(tmp_path):
    main = _write(
        tmp_path / "blocks.jsonl",
        [
            '{"type": "user", "sessionId": "s1", "timestamp": "2026-01-01T00:00:00Z", "isMeta": false,'
            ' "message": {"content": [{"type": "text", "text": "hello"}, {"type": "other"}]}}'
        ],
    )
    session = transcript.parse_session(main)
    assert session.primary.prompt_count == 1
    assert session.first_prompt_ts == "2026-01-01T00:00:00Z"


def test_first_exit_code_wins_and_later_results_update_end(tmp_path):
    main = _write(
        tmp_path / "twice.jsonl",
        [
            '{"type": "assistant", "sessionId": "s1", "timestamp": "2026-01-01T00:00:01Z", "message": {"id": "m1",'
            ' "model": "x", "usage": {}, "content": [{"type": "tool_use", "id": "t1", "name": "Bash", "input": {}}]}}',
            '{"type": "user", "timestamp": "2026-01-01T00:00:02Z", "message": {"content":'
            ' [{"type": "tool_result", "tool_use_id": "t1", "is_error": false}]}, "toolUseResult": {"exitCode": 1}}',
            '{"type": "user", "timestamp": "2026-01-01T00:00:03Z", "message": {"content":'
            ' [{"type": "tool_result", "tool_use_id": "t1", "is_error": false}]}, "toolUseResult": {"exitCode": 0}}',
        ],
    )
    session = transcript.parse_session(main)
    call = session.primary.tool_calls[0]
    assert call.exit_code == 1
    assert call.end == "2026-01-01T00:00:03Z"


def test_unknown_entry_type_is_skipped(tmp_path):
    main = _write(
        tmp_path / "future.jsonl",
        [
            '{"type": "brand-new-thing", "sessionId": "s1", "timestamp": "2026-01-01T00:00:00Z"}',
            '{"type": "user", "sessionId": "s1", "timestamp": "2026-01-01T00:00:01Z", "message": {"content": "go"}}',
        ],
    )
    session = transcript.parse_session(main)
    assert session.entry_count == 2
    assert session.primary.turns == []
    assert session.first_prompt_ts == "2026-01-01T00:00:01Z"


def test_success_false_marks_the_call_failed(tmp_path):
    main = _write(
        tmp_path / "succ.jsonl",
        [
            '{"type": "assistant", "sessionId": "s1", "timestamp": "2026-01-01T00:00:01Z", "message": {"id": "m1",'
            ' "model": "x", "usage": {}, "content": [{"type": "tool_use", "id": "t1", "name": "Bash", "input": {}}]}}',
            '{"type": "user", "timestamp": "2026-01-01T00:00:02Z", "message": {"content":'
            ' [{"type": "tool_result", "tool_use_id": "t1", "is_error": false}]}, "toolUseResult": {"success": false}}',
        ],
    )
    session = transcript.parse_session(main)
    assert session.primary.tool_calls[0].error is True
