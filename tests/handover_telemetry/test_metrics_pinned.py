"""Pinned tests for the metrics layer: the per-agent ledger, the
decision summary shapes and their limits, the git command pin, the
merge and rework boundaries, the funnel order with blank starts, and
the usage defaults."""

from datetime import datetime

import pytest

from golden_data import HOOK_LOG, SESSION_DIR

from handover_telemetry import logparse, metrics, pricing, transcript


class _Out:
    def __init__(self, returncode, stdout):
        self.returncode = returncode
        self.stdout = stdout


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


@pytest.fixture()
def full(session):
    logparse.apply_hook_durations(session.primary.tool_calls, HOOK_LOG)
    return metrics.compute(session, price_table=pricing.load_prices(), hook_log=HOOK_LOG)


def _call(name: str, input: dict) -> transcript.ToolCall:
    return transcript.ToolCall(id="t", name=name, input=input, start=None)


def test_per_agent_ledger_is_pinned(full):
    assert set(full.per_agent) == {"primary", "agent-42"}
    primary = full.per_agent["primary"]
    assert primary["turns"] == 4
    assert primary["tool_calls"] == 5
    assert primary["cost"] == pytest.approx(0.005012)
    sub = full.per_agent["agent-42"]
    assert sub["turns"] == 1
    assert sub["tool_calls"] == 1
    assert sub["cost"] == pytest.approx(0.001228)


def test_missing_usage_fields_stay_zero(session):
    session.primary.turns.append(
        transcript.Turn("mz", "glm-5.3-flash", None, {"output_tokens": 5}, None, None, None, None)
    )
    got = metrics.compute(session, price_table=pricing.load_prices())
    stats = got.models["glm-5.3-flash"]
    assert stats["input"] == 1250
    assert stats["output"] == 355
    assert stats["cache_read"] == 10000
    assert stats["cache_creation"] == 200


def test_cache_hit_rate_sums_across_models(session):
    session.primary.turns.append(
        transcript.Turn(
            "m2",
            "second-model",
            None,
            {"input_tokens": 1000, "cache_read_input_tokens": 1000},
            None,
            None,
            None,
            None,
        )
    )
    got = metrics.compute(session, price_table=pricing.load_prices())
    assert got.cache_hit_rate == pytest.approx(11000 / 13450)


def test_empty_usage_stays_zero(session):
    session.primary.turns.append(
        transcript.Turn("mz", "glm-5.3-flash", None, {}, None, None, None, None)
    )
    got = metrics.compute(session, price_table=pricing.load_prices())
    stats = got.models["glm-5.3-flash"]
    assert stats == {
        "input": 1250,
        "output": 350,
        "cache_read": 10000,
        "cache_creation": 200,
        "turns": 6,
    }


def test_a_turn_without_a_model_lands_in_unknown(session):
    session.primary.turns = [transcript.Turn("mz", None, None, {}, None, None, None, None)]
    session.sidechains = []
    got = metrics.compute(session, price_table=pricing.load_prices())
    assert list(got.models) == ["unknown"]
    assert got.unknown_models == ["unknown"]
    assert got.cache_hit_rate is None


def test_decision_summary_joins_the_questions():
    call = _call("AskUserQuestion", {"questions": [{"question": "Q1"}, {"question": "Q2"}]})
    assert metrics._decision_summary(call) == "Q1 | Q2"


def test_decision_summary_skips_nondict_questions():
    call = _call("AskUserQuestion", {"questions": ["junk", {"question": "Q1"}]})
    assert metrics._decision_summary(call) == "Q1"


def test_decision_summary_defaults_the_question_text():
    call = _call("AskUserQuestion", {"questions": [{"other": 1}]})
    assert metrics._decision_summary(call) == ""


def test_decision_summary_truncates_questions_at_the_limit():
    call = _call("AskUserQuestion", {"questions": [{"question": "x" * 70}, {"question": "y" * 70}]})
    got = metrics._decision_summary(call)
    assert got == "x" * 70 + " | " + "y" * 47
    assert len(got) == 120


def test_agent_summary_pairs_kind_and_description():
    call = _call("Agent", {"subagent_type": "reviewer", "description": "look"})
    assert metrics._decision_summary(call) == "reviewer: look"


def test_agent_summary_defaults_the_kind():
    assert metrics._decision_summary(_call("Agent", {})) == "?: "


def test_agent_summary_defaults_the_description():
    assert metrics._decision_summary(_call("Agent", {"subagent_type": "r"})) == "r: "


def test_agent_summary_truncates_at_the_limit():
    call = _call("Agent", {"subagent_type": "r", "description": "y" * 130})
    got = metrics._decision_summary(call)
    assert len(got) == 120
    assert got == "r: " + "y" * 117


def test_skill_summary_defaults_the_skill():
    assert metrics._decision_summary(_call("Skill", {})) == "?: "


def test_skill_summary_defaults_the_args():
    assert metrics._decision_summary(_call("Skill", {"skill": "ub"})) == "ub: "


def test_workflow_summary_falls_back_to_the_name():
    assert metrics._decision_summary(_call("Workflow", {"name": "wf"})) == "wf"


def test_workflow_summary_without_description_or_name_is_empty():
    assert metrics._decision_summary(_call("Workflow", {})) == ""


def test_question_texts_default_to_no_questions():
    assert metrics._decision_summary(_call("AskUserQuestion", {})) == ""


def test_question_texts_guard_against_null():
    assert metrics._question_texts({"questions": None}) == []
    assert metrics._decision_summary(_call("AskUserQuestion", {"questions": None})) == ""


def test_workflow_summary_truncates_at_the_limit():
    got = metrics._decision_summary(_call("Workflow", {"description": "z" * 130}))
    assert got == "z" * 120


def test_unknown_tool_summary_is_empty():
    assert metrics._decision_summary(_call("Bash", {"command": "ls"})) == ""


def test_exit_plan_mode_without_a_plan_is_empty():
    assert metrics._decision_summary(_call("ExitPlanMode", {})) == ""


def test_git_log_pins_the_command_and_the_parse(monkeypatch, tmp_path):
    calls = []

    def fake_run(argv, **kwargs):
        calls.append((list(argv), dict(kwargs)))
        return _Out(
            0,
            "2026-01-01T00:00:00+00:00\tfeat: one (#3)\n"
            "junk-no-tab\n"
            "2026-01-02T00:00:00+00:00\ta\tb\n"
            "2026-01-03T00:00:00+00:00\t  padded subject\n",
        )

    monkeypatch.setattr(metrics.subprocess, "run", fake_run)
    rows = metrics._git_log(tmp_path, "main")
    assert rows == [
        ("2026-01-01T00:00:00+00:00", "feat: one (#3)"),
        ("2026-01-02T00:00:00+00:00", "a\tb"),
        ("2026-01-03T00:00:00+00:00", "  padded subject"),
    ]
    assert calls == [
        (
            ["git", "log", "--format=%cI%x09%s", "-n", "200", "main"],
            {
                "cwd": tmp_path,
                "capture_output": True,
                "text": True,
                "timeout": 30,
                "shell": False,
            },
        )
    ]


def test_git_log_nonzero_exit_is_none(monkeypatch, tmp_path):
    monkeypatch.setattr(metrics.subprocess, "run", lambda *a, **k: _Out(1, "x"))
    assert metrics._git_log(tmp_path, "main") is None


def test_git_log_os_error_is_none(monkeypatch, tmp_path):
    def boom(*args, **kwargs):
        raise OSError("no git")

    monkeypatch.setattr(metrics.subprocess, "run", boom)
    assert metrics._git_log(tmp_path, "main") is None


def test_merge_ts_picks_the_row_at_the_after_boundary(monkeypatch, tmp_path):
    rows = [
        ("junk", "feat: junk stamp (#9)"),
        ("2026-01-01T00:00:00+00:00", "old: before (#1)"),
        ("2026-01-02T00:00:00+00:00", "feat: at-boundary (#5)"),
        ("2026-01-03T00:00:00+00:00", "feat: later (#8)"),
    ]
    monkeypatch.setattr(metrics, "_git_log", lambda repo, ref: rows)
    after = datetime.fromisoformat("2026-01-02T00:00:00+00:00")
    assert metrics._merge_ts(tmp_path, after) == datetime.fromisoformat(
        "2026-01-02T00:00:00+00:00"
    )


def test_merge_ts_needs_both_the_paren_and_the_mark(monkeypatch, tmp_path):
    rows = [
        ("junk", "feat: junk stamp (#9)"),
        ("2026-01-01T00:00:00+00:00", "old: before (#1)"),
        ("2026-01-02T00:00:00+00:00", "(#5) opener text"),
        ("2026-01-03T00:00:00+00:00", "feat: later (#8)  "),
        ("2026-01-04T00:00:00+00:00", "closer paren only)"),
    ]
    monkeypatch.setattr(metrics, "_git_log", lambda repo, ref: rows)
    after = datetime.fromisoformat("2026-01-02T00:00:00+00:00")
    assert metrics._merge_ts(tmp_path, after) == datetime.fromisoformat(
        "2026-01-03T00:00:00+00:00"
    )


def test_merge_ts_without_a_repo_never_queries_git(monkeypatch, tmp_path):
    calls = []

    def fake_git_log(repo, ref):
        calls.append((repo, ref))
        return [("2026-01-03T00:00:00+00:00", "feat: x (#1)")]

    monkeypatch.setattr(metrics, "_git_log", fake_git_log)
    after = datetime.fromisoformat("2026-01-02T00:00:00+00:00")
    assert metrics._merge_ts(None, after) is None
    assert calls == []


def test_merge_ts_with_only_old_merges_is_none(monkeypatch, tmp_path):
    rows = [("2026-01-01T00:00:00+00:00", "feat: old (#1)")]
    monkeypatch.setattr(metrics, "_git_log", lambda repo, ref: rows)
    after = datetime.fromisoformat("2026-01-02T00:00:00+00:00")
    assert metrics._merge_ts(tmp_path, after) is None


def test_merge_ts_with_no_rows_is_none(monkeypatch, tmp_path):
    monkeypatch.setattr(metrics, "_git_log", lambda repo, ref: None)
    assert metrics._merge_ts(tmp_path, None) is None


def test_branch_commits_need_a_repo_and_a_branch(monkeypatch, tmp_path):
    seen = []

    def fake_git_log(repo, ref):
        seen.append((repo, ref))
        return [("2026-01-01T00:00:00+00:00", "s"), ("junk", "s2")]

    monkeypatch.setattr(metrics, "_git_log", fake_git_log)
    assert metrics._branch_commits(None, "main") == []
    assert metrics._branch_commits(tmp_path, None) == []
    got = metrics._branch_commits(tmp_path, "feat")
    assert got == [datetime.fromisoformat("2026-01-01T00:00:00+00:00")]
    assert seen == [(tmp_path, "feat")]


def test_branch_commits_tolerate_a_failed_log(monkeypatch, tmp_path):
    monkeypatch.setattr(metrics, "_git_log", lambda repo, ref: None)
    assert metrics._branch_commits(tmp_path, "feat") == []


def _fix_rows() -> list[tuple[str, str]]:
    return [
        ("2026-01-01T00:00:00+00:00", "early fix before any failure"),
        ("2026-01-02T00:00:00+00:00", "work on the suite"),
        ("2026-01-03T00:00:00+00:00", "review fix"),
        ("junk", "fix with a junk stamp"),
        ("2026-01-04T00:00:00+00:00", "Fix the flaky gate"),
    ]


BOUNDARY = datetime.fromisoformat("2026-01-02T12:00:00+00:00")


def test_fix_commits_count_subjects_with_fix_at_or_after_the_boundary(monkeypatch, tmp_path):
    monkeypatch.setattr(metrics, "_git_log", lambda repo, ref: _fix_rows())
    got = metrics._fix_commits_after(tmp_path, "feat/demo", BOUNDARY)
    assert got == 2


def test_fix_commits_before_the_boundary_do_not_count(monkeypatch, tmp_path):
    rows = [("2026-01-01T00:00:00+00:00", "quick fix")]
    monkeypatch.setattr(metrics, "_git_log", lambda repo, ref: rows)
    assert metrics._fix_commits_after(tmp_path, "feat/demo", BOUNDARY) == 0


def test_fix_commits_at_the_boundary_count(monkeypatch, tmp_path):
    rows = [("2026-01-02T12:00:00+00:00", "fix the gate")]
    monkeypatch.setattr(metrics, "_git_log", lambda repo, ref: rows)
    assert metrics._fix_commits_after(tmp_path, "feat/demo", BOUNDARY) == 1


def test_fix_commits_match_the_subject_without_case(monkeypatch, tmp_path):
    rows = [("2026-01-03T00:00:00+00:00", "FIX the gate now")]
    monkeypatch.setattr(metrics, "_git_log", lambda repo, ref: rows)
    assert metrics._fix_commits_after(tmp_path, "feat/demo", BOUNDARY) == 1


def test_fix_commits_without_a_boundary_count_zero(monkeypatch, tmp_path):
    monkeypatch.setattr(metrics, "_git_log", lambda repo, ref: _fix_rows())
    assert metrics._fix_commits_after(tmp_path, "feat/demo", None) == 0


def test_fix_commits_without_a_repo_or_a_branch_count_zero(monkeypatch, tmp_path):
    monkeypatch.setattr(metrics, "_git_log", lambda repo, ref: _fix_rows())
    assert metrics._fix_commits_after(None, "feat/demo", BOUNDARY) == 0
    assert metrics._fix_commits_after(tmp_path, None, BOUNDARY) == 0


def test_fix_commits_tolerate_a_failed_log(monkeypatch, tmp_path):
    monkeypatch.setattr(metrics, "_git_log", lambda repo, ref: None)
    assert metrics._fix_commits_after(tmp_path, "feat/demo", BOUNDARY) == 0


def test_fix_commits_with_no_rows_count_zero(monkeypatch, tmp_path):
    monkeypatch.setattr(metrics, "_git_log", lambda repo, ref: [])
    assert metrics._fix_commits_after(tmp_path, "feat/demo", BOUNDARY) == 0


def test_first_failed_start_picks_the_earliest_failed_call_start():
    runs = [
        transcript.AgentRun(
            agent_id="primary",
            tool_calls=[
                transcript.ToolCall("t0", "Read", {}, "2026-01-01T00:00:01Z"),
                transcript.ToolCall("t1", "Bash", {}, "2026-01-01T00:00:05Z", error=True),
                transcript.ToolCall("t2", "Read", {}, "2026-01-01T00:00:02Z", error=True),
            ],
        )
    ]
    got = metrics._first_failed_start(runs)
    assert got == datetime.fromisoformat("2026-01-01T00:00:02+00:00")


def test_first_failed_start_with_no_failures_is_none():
    runs = [transcript.AgentRun(agent_id="primary")]
    assert metrics._first_failed_start(runs) is None


def _review_decisions(stamp: str) -> list[dict]:
    return [{"agent": "primary", "tool": "Agent", "summary": "review fix", "ts": stamp}]


def test_rework_rate_counts_commits_strictly_after_the_review(monkeypatch):
    commits = [
        datetime.fromisoformat("2026-01-01T00:00:00+00:00"),
        datetime.fromisoformat("2026-01-02T00:00:00+00:00"),
        datetime.fromisoformat("2026-01-03T00:00:00+00:00"),
    ]
    monkeypatch.setattr(metrics, "_branch_commits", lambda repo, branch: commits)
    review = "2026-01-02T00:00:00+00:00"
    assert metrics._rework_rate(_review_decisions(review), None, "feat") == pytest.approx(1 / 3)


def test_rework_rate_at_the_review_boundary_counts_zero(monkeypatch):
    commits = [
        datetime.fromisoformat("2026-01-01T00:00:00+00:00"),
        datetime.fromisoformat("2026-01-02T00:00:00+00:00"),
    ]
    monkeypatch.setattr(metrics, "_branch_commits", lambda repo, branch: commits)
    review = "2026-01-02T00:00:00+00:00"
    assert metrics._rework_rate(_review_decisions(review), None, "feat") == 0.0


def test_rework_rate_without_a_review_decision_is_none(monkeypatch):
    commits = [datetime.fromisoformat("2026-01-01T00:00:00+00:00")]
    monkeypatch.setattr(metrics, "_branch_commits", lambda repo, branch: commits)
    assert metrics._rework_rate([], None, "feat") is None


def test_rework_rate_with_a_junk_stamp_is_none(monkeypatch):
    commits = [datetime.fromisoformat("2026-01-01T00:00:00+00:00")]
    monkeypatch.setattr(metrics, "_branch_commits", lambda repo, branch: commits)
    assert metrics._rework_rate(_review_decisions("junk"), None, "feat") is None


def test_rework_rate_without_commits_is_none(monkeypatch):
    monkeypatch.setattr(metrics, "_branch_commits", lambda repo, branch: [])
    review = "2026-01-02T00:00:00+00:00"
    assert metrics._rework_rate(_review_decisions(review), None, "feat") is None


def test_funnel_orders_a_blank_start_first():
    runs = [
        transcript.AgentRun(
            agent_id="primary",
            tool_calls=[
                transcript.ToolCall("t1", "Bash", {}, "2026-01-02T00:00:00Z"),
                transcript.ToolCall("t2", "Read", {}, None),
            ],
        )
    ]
    got = metrics._funnel(runs)
    assert [c["tool"] for c in got] == ["Read", "Bash"]


def test_recovery_at_the_boundary_is_zero():
    runs = [
        transcript.AgentRun(
            agent_id="primary",
            tool_calls=[
                transcript.ToolCall("t1", "Bash", {}, "2026-01-01T00:00:00Z", "2026-01-01T00:00:01Z", error=True),
                transcript.ToolCall("t2", "Read", {}, "2026-01-01T00:00:00Z", "2026-01-01T00:00:01Z"),
            ],
        )
    ]
    assert metrics._recovery_ms(runs) == 0.0


def test_recovery_picks_the_earliest_success():
    runs = [
        transcript.AgentRun(
            agent_id="primary",
            tool_calls=[
                transcript.ToolCall("t1", "Bash", {}, "2026-01-01T00:00:00Z", "2026-01-01T00:00:01Z", error=True),
                transcript.ToolCall("t2", "Read", {}, "2026-01-01T00:00:00Z", "2026-01-01T00:00:02Z"),
                transcript.ToolCall("t3", "Edit", {}, "2026-01-01T00:00:00Z", "2026-01-01T00:00:03Z"),
            ],
        )
    ]
    assert metrics._recovery_ms(runs) == 1000.0


def test_earliest_failed_end_picks_the_earliest():
    runs = [
        transcript.AgentRun(
            agent_id="primary",
            tool_calls=[
                transcript.ToolCall("t1", "Bash", {}, "2026-01-01T00:00:00Z", "2026-01-01T00:00:05Z", error=True),
                transcript.ToolCall("t2", "Read", {}, "2026-01-01T00:00:00Z", "2026-01-01T00:00:02Z", error=True),
            ],
        )
    ]
    failed = metrics._earliest_failed_end(runs)
    assert failed == datetime.fromisoformat("2026-01-01T00:00:02+00:00")


def test_parse_iso_keeps_the_utc_offset():
    assert metrics._parse_iso("2026-01-01T00:00:00+02:00") == datetime.fromisoformat(
        "2026-01-01T00:00:00+02:00"
    )


def test_parse_iso_of_junk_is_none():
    assert metrics._parse_iso("junk") is None


def test_parse_iso_of_lowercase_z_is_none():
    assert metrics._parse_iso("2026-01-01T00:00:00z") is None


def test_git_repo_merge_before_the_prompt_gives_no_lead(session, tmp_path, monkeypatch):
    import subprocess

    repo = tmp_path / "repo"
    repo.mkdir()

    def git(*args: str, date: str) -> str:
        env = dict(__import__("os").environ)
        env.update(
            {
                "GIT_AUTHOR_DATE": date,
                "GIT_COMMITTER_DATE": date,
                "GIT_AUTHOR_NAME": "T",
                "GIT_AUTHOR_EMAIL": "t@example.org",
                "GIT_COMMITTER_NAME": "T",
                "GIT_COMMITTER_EMAIL": "t@example.org",
            }
        )
        out = subprocess.run(
            ["git", *args], cwd=repo, env=env, capture_output=True, text=True, timeout=30
        )
        assert out.returncode == 0, out.stderr

    git("init", "-b", "main", date="2026-01-01T08:00:00 +0000")
    (repo / "a.txt").write_text("a", encoding="utf-8")
    git("add", ".", date="2026-01-01T08:00:00 +0000")
    git("commit", "-m", "init", date="2026-01-01T08:00:00 +0000")
    git("checkout", "-b", "feat/a", date="2026-01-01T09:30:00 +0000")
    (repo / "b.txt").write_text("b", encoding="utf-8")
    git("add", ".", date="2026-01-01T09:30:00 +0000")
    git("commit", "-m", "work", date="2026-01-01T09:30:00 +0000")
    git("checkout", "main", date="2026-01-01T10:30:00 +0000")
    git("merge", "--no-ff", "-m", "feat: a (#1)", "feat/a", date="2026-01-01T10:30:00 +0000")

    session.first_prompt_ts = "2026-01-01T11:00:00.000Z"
    got = metrics.compute(session, price_table=pricing.load_prices(), repo_root=repo)
    assert got.dora["lead_time_ms"] is None
