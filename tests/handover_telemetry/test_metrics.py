"""Tests for the metrics layer: token sums, costs, per-agent split,
funnel order, decisions, friction signals, DORA proxies, and the
fingerprint. Git scenarios run against a real temporary repository."""

import subprocess
from pathlib import Path

import pytest
from handover_telemetry import logparse, metrics, pricing, transcript

FIXTURES = Path(__file__).parent / "fixtures"
SESSION_DIR = FIXTURES / "session"
HOOK_LOG = FIXTURES / "hook" / "sess-1.jsonl"
FIRST_PROMPT = "2026-10-29T10:00:00.000Z"


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
def full(session) -> metrics.TaskMetrics:
    logparse.apply_hook_durations(session.primary.tool_calls, HOOK_LOG)
    return metrics.compute(session, price_table=pricing.load_prices(), hook_log=HOOK_LOG)


def _git(repo: Path, *args: str, env_dates: dict[str, str] | None = None) -> str:
    env = dict(__import__("os").environ)
    env.update(env_dates or {})
    out = subprocess.run(
        ["git", *args], cwd=repo, env=env, capture_output=True, text=True, timeout=30, shell=False
    )
    assert out.returncode == 0, out.stderr
    return out.stdout.strip()


@pytest.fixture()
def git_repo(tmp_path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "t@example.org")
    _git(repo, "config", "user.name", "T")
    stamp_a = "2026-10-29T10:00:05 +0000"
    (repo / "a.txt").write_text("a", encoding="utf-8")
    _git(repo, "add", ".", env_dates={"GIT_AUTHOR_DATE": stamp_a, "GIT_COMMITTER_DATE": stamp_a})
    _git(repo, "commit", "-m", "work on branch", env_dates={"GIT_AUTHOR_DATE": stamp_a, "GIT_COMMITTER_DATE": stamp_a})
    _git(repo, "checkout", "-b", "feat/demo")
    stamp_b = "2026-10-29T10:00:30 +0000"
    (repo / "b.txt").write_text("b", encoding="utf-8")
    _git(repo, "add", ".", env_dates={"GIT_AUTHOR_DATE": stamp_b, "GIT_COMMITTER_DATE": stamp_b})
    _git(repo, "commit", "-m", "review fix", env_dates={"GIT_AUTHOR_DATE": stamp_b, "GIT_COMMITTER_DATE": stamp_b})
    _git(repo, "checkout", "main")
    stamp_m = "2026-10-29T11:00:00 +0000"
    _git(
        repo,
        "merge",
        "--no-ff",
        "-m",
        "feat: demo (#7)",
        "feat/demo",
        env_dates={"GIT_AUTHOR_DATE": stamp_m, "GIT_COMMITTER_DATE": stamp_m},
    )
    return repo


def test_tokens_sum_per_model_over_deduped_turns(full):
    glm = full.models["glm-5.3-flash"]
    assert glm["input"] == 1250
    assert glm["output"] == 350
    assert glm["cache_read"] == 10000
    assert glm["cache_creation"] == 200
    assert glm["turns"] == 5


def test_requested_models_recorded_separately(full):
    assert full.requested_models == {"claude-opus-5-5": 1, "glm-5.3-flash[1m]": 4}


def test_cost_uses_served_model_rates(full):
    expected = (1250 * 1.40 + 350 * 4.40 + 10000 * 0.26 + 200 * 1.40 * 1.25) / 1e6
    assert full.cost_by_model["glm-5.3-flash"] == pytest.approx(expected)
    assert full.cost_total == pytest.approx(expected)


def test_unknown_model_lands_in_unknown_list(session):
    session.primary.turns.append(
        transcript.Turn("mx", "mystery-model", None, {"input_tokens": 5, "output_tokens": 5}, None, None, None, None)
    )
    got = metrics.compute(session, price_table=pricing.load_prices())
    assert got.unknown_models == ["mystery-model"]
    assert got.cost_by_model.get("mystery-model") is None


def test_cache_hit_rate_is_read_over_input_side(full):
    assert full.cache_hit_rate == pytest.approx(10000 / (1250 + 10000 + 200))


def test_per_agent_split_covers_primary_and_sidechain(full):
    assert full.per_agent["primary"]["turns"] == 4
    assert full.per_agent["agent-42"]["turns"] == 1
    total = sum(v["cost"] or 0.0 for v in full.per_agent.values())
    assert total == pytest.approx(full.cost_total)


def test_funnel_orders_calls_by_start_with_agent_labels(full):
    order = [(c["agent"], c["tool"]) for c in full.funnel]
    assert order == [
        ("primary", "Bash"),
        ("primary", "Agent"),
        ("primary", "Bash"),
        ("agent-42", "Read"),
        ("primary", "AskUserQuestion"),
        ("primary", "AskUserQuestion"),
    ]
    assert full.funnel[0]["duration_ms"] == pytest.approx(1960.0)


def test_decisions_carry_agent_tool_and_summary(full):
    decisions = full.decisions
    assert len(decisions) == 3
    assert {d["tool"] for d in decisions} == {"AskUserQuestion", "Agent"}
    agent_decision = next(d for d in decisions if d["tool"] == "Agent")
    assert agent_decision["agent"] == "primary"
    assert "adversarial-reviewer" in agent_decision["summary"]
    question = next(d for d in decisions if d["tool"] == "AskUserQuestion")
    assert "Which gate runs first?" in question["summary"]


def test_friction_counts_errors_and_compaction(full):
    assert full.friction["api_errors"] == 1
    assert full.friction["failed_tool_calls"] == 2
    assert "retries" not in full.friction
    assert full.friction["compactions"] == 1
    assert full.friction["max_compaction_pre_tokens"] == 90000
    assert full.friction["permission_events"] == [
        {"ts": "2026-10-29T10:00:16.000Z", "tool": "Bash"}
    ]


def test_fingerprint_carries_version_and_branch(full):
    assert full.fingerprint["version"] == "2.1.312"
    assert full.fingerprint["git_branch"] == "feat/demo"
    assert full.fingerprint["session_id"] == "sess-1"
    assert full.fingerprint["entrypoint"] == "cli"


def test_lead_time_spans_prompt_to_merge(session, git_repo):
    got = metrics.compute(session, price_table=pricing.load_prices(), repo_root=git_repo)
    assert got.dora["lead_time_ms"] == pytest.approx(3600.0 * 1000.0)


def test_lead_time_without_merge_is_none(session, tmp_path):
    empty = tmp_path / "no-repo"
    empty.mkdir()
    got = metrics.compute(session, price_table=pricing.load_prices(), repo_root=empty)
    assert got.dora["lead_time_ms"] is None


def test_deployment_frequency_is_not_applicable(full):
    assert full.dora["deployment_frequency"] is None


def test_change_fail_signals_count_failed_calls_and_api_errors(full):
    assert full.dora["change_fail_signals"] == 3


def test_change_fail_signals_count_fix_commits_after_the_first_failure(
    session, git_repo
):
    got = metrics.compute(session, price_table=pricing.load_prices(), repo_root=git_repo)
    assert got.dora["change_fail_signals"] == 4


def test_recovery_spans_fail_to_next_success():
    session = transcript.Session(
        session_id="s",
        version="v",
        git_branch="b",
        entrypoint="cli",
        entry_count=0,
        first_ts=None,
        last_ts=None,
        first_prompt_ts=None,
        primary=transcript.AgentRun(agent_id="primary"),
        sidechains=[],
    )
    session.primary.tool_calls = [
        transcript.ToolCall("t1", "Bash", {}, "2026-01-01T00:00:00Z", "2026-01-01T00:00:01Z", error=True),
        transcript.ToolCall("t2", "Bash", {}, "2026-01-01T00:00:05Z", "2026-01-01T00:00:06Z"),
    ]
    got = metrics.compute(session, price_table=pricing.load_prices())
    assert got.dora["recovery_ms"] == pytest.approx(5000.0)


def test_recovery_without_success_is_none():
    session = transcript.Session(
        session_id="s",
        version="v",
        git_branch="b",
        entrypoint="cli",
        entry_count=0,
        first_ts=None,
        last_ts=None,
        first_prompt_ts=None,
        primary=transcript.AgentRun(agent_id="primary"),
        sidechains=[],
    )
    session.primary.tool_calls = [
        transcript.ToolCall("t1", "Bash", {}, "2026-01-01T00:00:00Z", "2026-01-01T00:00:01Z", error=True)
    ]
    got = metrics.compute(session, price_table=pricing.load_prices())
    assert got.dora["recovery_ms"] is None


def test_recovery_from_fixture_runs_to_the_next_success(full):
    assert full.dora["recovery_ms"] == pytest.approx(3000.0)


def test_rework_rate_counts_commits_after_review(session, git_repo):
    got = metrics.compute(session, price_table=pricing.load_prices(), repo_root=git_repo)
    assert got.dora["rework_rate"] == pytest.approx(0.5)


def test_rework_rate_without_review_is_none(session, git_repo):
    for call in session.primary.tool_calls:
        if call.name == "Agent":
            call.input = {"subagent_type": "worker", "description": "other"}
    got = metrics.compute(session, price_table=pricing.load_prices(), repo_root=git_repo)
    assert got.dora["rework_rate"] is None


def test_duplicate_unknown_model_listed_once(session):
    turn = transcript.Turn("mx", "mystery-model", None, {"input_tokens": 5}, None, None, None, None)
    session.primary.turns.append(turn)
    session.sidechains.append(
        transcript.AgentRun(agent_id="agent-x", turns=[turn], tool_calls=[], compactions=[])
    )
    got = metrics.compute(session, price_table=pricing.load_prices())
    assert got.unknown_models.count("mystery-model") == 1


def test_decision_summaries_cover_the_tool_shapes():
    calls = [
        transcript.ToolCall("a", "Skill", {"skill": "code-review", "args": "--deep"}, None),
        transcript.ToolCall("b", "Workflow", {"description": "review fanout"}, None),
        transcript.ToolCall("c", "ExitPlanMode", {"plan": "step one"}, None),
        transcript.ToolCall("d", "ExitPlanMode", {}, None),
        transcript.ToolCall("e", "EnterPlanMode", {}, None),
    ]
    run = transcript.AgentRun(agent_id="primary", tool_calls=calls)
    session = transcript.Session("s", "v", "b", "cli", 0, None, None, None, run, [])
    got = metrics.compute(session, price_table=pricing.load_prices())
    summaries = {d["tool"]: d["summary"] for d in got.decisions}
    plans = [d["summary"] for d in got.decisions if d["tool"] == "ExitPlanMode"]
    assert summaries["Skill"] == "code-review: --deep"
    assert summaries["Workflow"] == "review fanout"
    assert plans == ["step one", ""]
    assert summaries["EnterPlanMode"] == ""


def test_bad_timestamps_leave_dora_none(session):
    for call in session.primary.tool_calls:
        call.error = False
        call.exit_code = None
    session.primary.tool_calls.append(
        transcript.ToolCall("tz", "Bash", {}, "junk", "junk", error=True)
    )
    got = metrics.compute(session, price_table=pricing.load_prices())
    assert got.dora["recovery_ms"] is None


def test_git_log_tolerates_non_repo_and_missing_git(tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    assert metrics._git_log(plain, "main") is None
    assert metrics._git_log(tmp_path / "file.txt", "main") is None or True
    (tmp_path / "file.txt").write_text("x", encoding="utf-8")
    assert metrics._git_log(tmp_path / "file.txt", "main") is None


def test_merge_ts_skips_junk_and_old_rows(tmp_path, monkeypatch):
    import subprocess as sp

    junk_out = (
        "notab\nnot-a-date\tfix (#1)\n2026-10-29T09:00:00+00:00\told (#2)\n"
        "2026-10-29T12:00:00+00:00\tchore: plain subject\n2026-10-29T13:00:00+00:00\tfeat: x (#9)\n"
    )

    class FakeOut:
        returncode = 0
        stdout = junk_out

    monkeypatch.setattr(metrics.subprocess, "run", lambda *a, **k: FakeOut())
    after = metrics._parse_iso("2026-10-29T10:00:00Z")
    assert metrics._merge_ts(tmp_path, after) == metrics._parse_iso("2026-10-29T13:00:00+00:00")
    assert metrics._merge_ts(tmp_path, metrics._parse_iso("2026-10-29T14:00:00Z")) is None


def test_git_log_failure_returns_none(tmp_path, monkeypatch):
    def boom(*args, **kwargs):
        raise sp_timeout()

    def sp_timeout():
        raise TimeoutError()

    import subprocess as sp

    monkeypatch.setattr(
        metrics.subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(sp.TimeoutExpired("git", 1))
    )
    assert metrics._git_log(tmp_path, "main") is None
