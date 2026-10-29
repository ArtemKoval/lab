"""Pinned tests for the transcript parser: the exact Turn shape, the
dedup key with its fallback, the error and prompt counters, the slug
rule, the loader filters, and the small comparison helpers."""

from pathlib import Path

import pytest

from golden_data import SESSION_DIR

from handover_telemetry import transcript


@pytest.fixture()
def session(tmp_path) -> transcript.Session:
    main = tmp_path / "main.jsonl"
    main.write_text((SESSION_DIR / "main.jsonl").read_text(encoding="utf-8"), encoding="utf-8")
    sub = tmp_path / "sess-1" / "subagents"
    sub.mkdir(parents=True)
    (sub / "agent-42.jsonl").write_text(
        (SESSION_DIR / "sess-1" / "subagents" / "agent-42.jsonl").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return transcript.parse_session(main)


def _write_lines(path: Path, lines: list[str]) -> Path:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _assistant(line_id: str, **extra: str) -> str:
    entry = {
        "type": "assistant",
        "sessionId": "s1",
        "timestamp": "2026-01-01T00:00:01Z",
        "message": {"id": line_id, "model": "m1", "usage": {}, "content": []},
    }
    entry.update(extra)
    import json as jsonlib

    return jsonlib.dumps(entry)


def test_first_turn_shape_is_pinned(session):
    turn = session.primary.turns[0]
    assert turn == transcript.Turn(
        message_id="msg_1",
        model="glm-5.3-flash",
        requested_model="glm-5.3-flash[1m]",
        usage={
            "input_tokens": 100,
            "cache_creation_input_tokens": 200,
            "cache_read_input_tokens": 1000,
            "output_tokens": 50,
            "output_tokens_details": {"thinking_tokens": 10},
        },
        ts="2026-10-29T10:00:05.000Z",
        effort="high",
        thinking_ms=1200,
        request_id="req-1",
    )


def test_dedup_falls_back_to_the_request_ref(tmp_path):
    lines = [
        _assistant("m1", requestId="r1"),
        _assistant("m1", requestRef="r1"),
    ]
    path = _write_lines(tmp_path / "refs.jsonl", lines)
    got = transcript.parse_session(path)
    assert len(got.primary.turns) == 1


def test_dedup_without_request_ids_still_collapses(tmp_path):
    lines = [_assistant("m1"), _assistant("m1")]
    path = _write_lines(tmp_path / "noref.jsonl", lines)
    got = transcript.parse_session(path)
    assert len(got.primary.turns) == 1


def test_dedup_key_prefers_the_request_id_over_the_ref(tmp_path):
    lines = [
        _assistant("m1", requestId="r1", requestRef="r9"),
        _assistant("m1", requestId="r1"),
    ]
    path = _write_lines(tmp_path / "both.jsonl", lines)
    got = transcript.parse_session(path)
    assert len(got.primary.turns) == 1


def test_turns_without_a_message_id_are_never_deduped(tmp_path):
    entry = {
        "type": "assistant",
        "sessionId": "s1",
        "timestamp": "2026-01-01T00:00:01Z",
        "message": {"model": "m", "usage": {}, "content": []},
    }
    import json as jsonlib

    line = jsonlib.dumps(entry)
    path = _write_lines(tmp_path / "noid.jsonl", [line, line])
    got = transcript.parse_session(path)
    assert len(got.primary.turns) == 2


def test_two_api_errors_count_twice(tmp_path):
    lines = [
        '{"type": "assistant", "sessionId": "s1", "isApiErrorMessage": true,'
        ' "timestamp": "2026-01-01T00:00:01Z", "message": {"id": "e1", "model": "m", "usage": {}, "content": []}}',
        '{"type": "assistant", "sessionId": "s1", "isApiErrorMessage": true,'
        ' "timestamp": "2026-01-01T00:00:02Z", "message": {"id": "e2", "model": "m", "usage": {}, "content": []}}',
    ]
    path = _write_lines(tmp_path / "errs.jsonl", lines)
    got = transcript.parse_session(path)
    assert got.primary.api_errors == 2
    assert got.primary.turns == []


def test_synthetic_model_is_excluded_without_an_error_flag(tmp_path):
    entry = {
        "type": "assistant",
        "sessionId": "s1",
        "timestamp": "2026-01-01T00:00:01Z",
        "message": {
            "id": "s1m",
            "model": "<synthetic>",
            "usage": {},
            "content": [],
        },
    }
    import json as jsonlib

    path = _write_lines(tmp_path / "synth.jsonl", [jsonlib.dumps(entry)])
    got = transcript.parse_session(path)
    assert got.primary.api_errors == 1
    assert got.primary.turns == []


def test_error_flag_excludes_a_normal_model(tmp_path):
    entry = {
        "type": "assistant",
        "sessionId": "s1",
        "isApiErrorMessage": True,
        "timestamp": "2026-01-01T00:00:01Z",
        "message": {"id": "e1", "model": "glm-5.3-flash", "usage": {}, "content": []},
    }
    import json as jsonlib

    path = _write_lines(tmp_path / "flag.jsonl", [jsonlib.dumps(entry)])
    got = transcript.parse_session(path)
    assert got.primary.api_errors == 1
    assert got.primary.turns == []


def test_two_prompts_count_two(tmp_path):
    lines = [
        '{"type": "user", "sessionId": "s1", "isMeta": false, "timestamp": "2026-01-01T00:00:01Z",'
        ' "message": {"role": "user", "content": "first"}}',
        '{"type": "user", "sessionId": "s1", "isMeta": false, "timestamp": "2026-01-01T00:00:05Z",'
        ' "message": {"role": "user", "content": "second"}}',
    ]
    path = _write_lines(tmp_path / "prompts.jsonl", lines)
    got = transcript.parse_session(path)
    assert got.primary.prompt_count == 2
    assert got.first_prompt_ts == "2026-01-01T00:00:01Z"


def test_a_user_entry_without_content_is_not_a_prompt(tmp_path):
    lines = [
        '{"type": "user", "sessionId": "s1", "isMeta": false, "timestamp": "2026-01-01T00:00:01Z",'
        ' "message": {"role": "user"}}',
    ]
    path = _write_lines(tmp_path / "nocontent.jsonl", lines)
    got = transcript.parse_session(path)
    assert got.primary.prompt_count == 0


def test_a_system_entry_without_the_boundary_is_not_a_compaction(tmp_path):
    lines = [
        '{"type": "system", "subtype": "hook_result", "sessionId": "s1",'
        ' "timestamp": "2026-01-01T00:00:01Z"}',
    ]
    path = _write_lines(tmp_path / "system.jsonl", lines)
    got = transcript.parse_session(path)
    assert got.primary.compactions == []


def test_tool_use_defaults_are_empty(tmp_path):
    entry = {
        "type": "assistant",
        "sessionId": "s1",
        "timestamp": "2026-01-01T00:00:01Z",
        "message": {"id": "m1", "model": "m", "usage": {}, "content": [{"type": "tool_use"}]},
    }
    import json as jsonlib

    path = _write_lines(tmp_path / "bare.jsonl", [jsonlib.dumps(entry)])
    got = transcript.parse_session(path)
    call = got.primary.tool_calls[0]
    assert call.id == ""
    assert call.name == ""
    assert call.input == {}
    assert call.start == "2026-01-01T00:00:01Z"


def test_earliest_and_latest_pick_the_extremes():
    assert transcript._earliest(None, "b") == "b"
    assert transcript._earliest("a", "b") == "a"
    assert transcript._earliest("b", "a") == "a"
    assert transcript._earliest("a", None) == "a"
    assert transcript._latest(None, "a") == "a"
    assert transcript._latest("a", "b") == "b"
    assert transcript._latest("b", "a") == "b"
    assert transcript._latest("a", None) == "a"


def test_activity_span_survives_out_of_order_entries(tmp_path):
    lines = [
        '{"type": "user", "sessionId": "s1", "isMeta": false, "timestamp": "2026-01-01T00:00:05Z",'
        ' "message": {"role": "user", "content": "later prompt"}}',
        '{"type": "user", "sessionId": "s1", "isMeta": false, "timestamp": "2026-01-01T00:00:01Z",'
        ' "message": {"role": "user", "content": "early prompt"}}',
    ]
    path = _write_lines(tmp_path / "ooo.jsonl", lines)
    got = transcript.parse_session(path)
    assert got.first_ts == "2026-01-01T00:00:01Z"
    assert got.last_ts == "2026-01-01T00:00:05Z"
    assert got.first_prompt_ts == "2026-01-01T00:00:05Z"


def test_is_text_block_requires_the_text_type():
    assert transcript._is_text_block({"type": "text"}) is True
    assert transcript._is_text_block({"type": "tool_use"}) is False
    assert transcript._is_text_block("text") is False
    assert transcript._is_text_block(None) is False


def test_is_transcript_needs_a_jsonl_file(tmp_path):
    real = tmp_path / "real.jsonl"
    real.write_text("", encoding="utf-8")
    assert transcript._is_transcript(real) is True
    plain = tmp_path / "plain.txt"
    plain.write_text("", encoding="utf-8")
    assert transcript._is_transcript(plain) is False
    folder = tmp_path / "folder.jsonl"
    folder.mkdir()
    assert transcript._is_transcript(folder) is False


def test_slug_keeps_safe_characters(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    slug = transcript.project_dir_for(Path("/aa/BB.ccc-dd"))
    assert slug.name == "-aa-BB.ccc-dd"


def test_load_entries_orders_and_filters(tmp_path):
    path = tmp_path / "mixed.jsonl"
    path.write_text(
        '{"a": 1}\n\nnot json\n[1, 2]\n  {"c": 3}  \n', encoding="utf-8"
    )
    assert transcript.load_entries(path) == [{"a": 1}, [1, 2], {"c": 3}]


def test_load_entries_replaces_bad_bytes(tmp_path):
    path = tmp_path / "bytes.jsonl"
    path.write_bytes(b'{"a": 1}\n\xff broken\n{"b": 2}\n')
    assert transcript.load_entries(path) == [{"a": 1}, {"b": 2}]


def test_sidechain_agent_id_overrides_then_keeps(tmp_path):
    lines = [
        '{"type": "user", "agentId": "agent-9", "sessionId": "s1", "timestamp": "2026-01-01T00:00:01Z",'
        ' "message": {"role": "user", "content": "start"}}',
        '{"type": "user", "sessionId": "s1", "timestamp": "2026-01-01T00:00:02Z",'
        ' "message": {"role": "user", "content": "more"}}',
    ]
    path = _write_lines(tmp_path / "zz9.jsonl", lines)
    run = transcript._parse_sidechain_file(path)
    assert run.agent_id == "agent-9"
    assert run.prompt_count == 2


def test_sidechain_without_agent_id_keeps_the_stem(tmp_path):
    path = _write_lines(tmp_path / "zz-9.jsonl", ['{"type": "mode"}'])
    run = transcript._parse_sidechain_file(path)
    assert run.agent_id == "zz-9"
