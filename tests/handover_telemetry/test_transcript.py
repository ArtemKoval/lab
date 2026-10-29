"""Tests for the transcript parser: discovery, tolerance, dedup,
synthetic exclusion, pairing, compaction, and sidechain split. The
fixtures mirror real Claude Code shapes with synthetic secrets."""

from pathlib import Path

import pytest
from handover_telemetry import transcript

FIXTURES = Path(__file__).parent / "fixtures"
SESSION_DIR = FIXTURES / "session"


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


def test_load_entries_skips_malformed_lines(session):
    assert session.entry_count == 14


def test_usage_dedup_counts_one_turn_per_message_id(session):
    turns = [t for t in session.primary.turns if t.message_id == "msg_1"]
    assert len(turns) == 1


def test_synthetic_error_stays_out_of_turns(session):
    assert "msg_err" not in {t.message_id for t in session.primary.turns}
    assert session.primary.api_errors == 1


def test_turn_keeps_both_model_names(session):
    turn = next(t for t in session.primary.turns if t.message_id == "msg_2")
    assert turn.model == "glm-5.3-flash"
    assert turn.requested_model == "claude-opus-5-5"


def test_turn_keeps_usage_and_thinking(session):
    turn = next(t for t in session.primary.turns if t.message_id == "msg_1")
    assert turn.usage["output_tokens"] == 50
    assert turn.thinking_ms == 1200
    assert turn.effort == "high"


def test_tool_call_pairs_with_its_result(session):
    call = next(c for c in session.primary.tool_calls if c.id == "toolu_1")
    assert call.name == "Bash"
    assert call.start is not None
    assert call.end is not None
    assert call.error is False
    assert call.exit_code == 1


def test_tool_use_in_a_second_entry_of_the_same_message_is_recorded(session):
    calls = {c.id: c for c in session.primary.tool_calls}
    assert "toolu_5" in calls
    assert calls["toolu_5"].name == "Bash"
    assert calls["toolu_5"].start == "2026-10-29T10:00:09.100Z"
    assert calls["toolu_5"].end == "2026-10-29T10:00:10.100Z"
    assert calls["toolu_5"].error is False


def test_failed_tool_call_carries_error_flag(session):
    run = session.sidechains[0]
    assert run.tool_calls[0].error is True


def test_unpaired_tool_call_keeps_end_none(session):
    calls = {c.id: c for c in session.primary.tool_calls}
    assert calls["toolu_4"].end is None


def test_compaction_recorded_with_trigger_and_pre_tokens(session):
    assert session.primary.compactions == [
        {"trigger": "auto", "pre_tokens": 90000, "ts": "2026-10-29T10:00:15.000Z"}
    ]


def test_prompt_times_kept_and_prompt_text_omitted(session):
    assert session.first_prompt_ts == "2026-10-29T10:00:00.000Z"
    assert session.primary.prompt_count == 1
    dumped = repr(session)
    assert "sk-live-synthetic" not in dumped


def test_activity_span_covers_first_to_last(session):
    assert session.first_ts == "2026-10-29T10:00:00.000Z"
    assert session.last_ts == "2026-10-29T10:00:20.000Z"


def test_fingerprint_fields_kept(session):
    assert session.version == "2.1.312"
    assert session.git_branch == "feat/demo"
    assert session.session_id == "sess-1"
    assert session.entrypoint == "cli"


def test_sidechain_parses_as_separate_agent(session):
    assert len(session.sidechains) == 1
    run = session.sidechains[0]
    assert run.agent_id == "agent-42"
    assert run.tool_calls[0].name == "Read"
    assert run.turns[0].usage["output_tokens"] == 120


def test_newest_transcript_ignores_subdirectories(tmp_path):
    (tmp_path / "a.jsonl").write_text("{}\n", encoding="utf-8")
    older = tmp_path / "b.jsonl"
    older.write_text("{}\n", encoding="utf-8")
    import os

    past = older.stat().st_mtime - 100
    os.utime(older, (past, past))
    assert transcript.newest_transcript(tmp_path).name == "a.jsonl"


def test_newest_transcript_returns_none_when_empty(tmp_path):
    assert transcript.newest_transcript(tmp_path) is None


def test_sidechain_glob_finds_nested_agents(tmp_path):
    sub = tmp_path / "sess-1" / "subagents" / "workflows" / "wf_1"
    sub.mkdir(parents=True)
    (sub / "agent-7.jsonl").write_text("{}\n", encoding="utf-8")
    found = transcript.sidechain_files(tmp_path, "sess-1")
    assert found == [sub / "agent-7.jsonl"]


def test_projects_root_honors_config_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    assert transcript.projects_root() == tmp_path / "projects"


def test_projects_root_defaults_to_home(monkeypatch):
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    assert transcript.projects_root() == Path.home() / ".claude" / "projects"


def test_project_dir_slug_encodes_path():
    assert transcript.project_dir_for(Path("/home/repos/lab/fde")).name.endswith("-home-repos-lab-fde")


def test_parse_session_reads_sidechains_from_disk(session):
    assert session.sidechains[0].agent_id == "agent-42"


def test_empty_file_parses_to_empty_session(tmp_path):
    empty = tmp_path / "empty.jsonl"
    empty.write_text("", encoding="utf-8")
    record = transcript.parse_session(empty)
    assert record.primary.turns == []
    assert record.entry_count == 0
    assert record.first_ts is None


def test_newest_transcript_missing_dir_is_none(tmp_path):
    assert transcript.newest_transcript(tmp_path / "absent") is None
