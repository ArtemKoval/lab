"""The derivation layer: one session turns into task metrics.

Everything here is offline. The DORA proxies come from the transcript
plus local git only, and every proxy without source data stays None so
the renderer can mark it honestly. Cost attribution always uses the
served model of the turn, never the requested one.
"""

import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from . import logparse
from .pricing import PriceTable
from .transcript import Session, ToolCall

_DECISION_TOOLS = {
    "AskUserQuestion",
    "ExitPlanMode",
    "Agent",
    "Skill",
    "Workflow",
    "EnterPlanMode",
}
_SUMMARY_LIMIT = 120
_REVIEW_MARK = "review"


@dataclass
class TaskMetrics:
    models: dict = field(default_factory=dict)
    requested_models: dict = field(default_factory=dict)
    cost_by_model: dict = field(default_factory=dict)
    cost_total: float | None = None
    unknown_models: list[str] = field(default_factory=list)
    cache_hit_rate: float | None = None
    per_agent: dict = field(default_factory=dict)
    funnel: list = field(default_factory=list)
    decisions: list = field(default_factory=list)
    friction: dict = field(default_factory=dict)
    fingerprint: dict = field(default_factory=dict)
    dora: dict = field(default_factory=dict)


def compute(
    session: Session,
    price_table: PriceTable,
    repo_root: Path | None = None,
    hook_log: Path | None = None,
) -> TaskMetrics:
    runs = [session.primary, *session.sidechains]
    got = TaskMetrics()
    for run in runs:
        _fold_run(got, run, price_table)
    got.cache_hit_rate = _cache_hit_rate(got.models)
    got.cost_total = _total_cost(got.cost_by_model)
    got.funnel = _funnel(runs)
    got.decisions = _decisions(runs)
    got.friction = _friction(session, runs, hook_log)  # pragma: no mutate: unused arg
    got.fingerprint = {
        "version": session.version,
        "entrypoint": session.entrypoint,
        "session_id": session.session_id,
        "git_branch": session.git_branch,
    }
    got.dora = _dora(session, got, repo_root)
    return got


def _fold_run(got: TaskMetrics, run, price_table: PriceTable) -> None:
    label = run.agent_id
    # pragma: no mutate start - the turns and tool_calls defaults are overwritten
    agent = got.per_agent.setdefault(label, {"turns": 0, "tool_calls": 0, "cost": 0.0})
    # pragma: no mutate end - the turns and tool_calls defaults are overwritten
    agent["turns"] = len(run.turns)
    agent["tool_calls"] = len(run.tool_calls)
    for turn in run.turns:
        _fold_turn(got, turn, price_table, agent)


def _fold_turn(got: TaskMetrics, turn, price_table: PriceTable, agent: dict) -> None:
    model = turn.model or "unknown"
    stats = got.models.setdefault(
        model,
        {"input": 0, "output": 0, "cache_read": 0, "cache_creation": 0, "turns": 0},
    )
    usage = turn.usage or {}
    stats["input"] += usage.get("input_tokens") or 0
    stats["output"] += usage.get("output_tokens") or 0
    stats["cache_read"] += usage.get("cache_read_input_tokens") or 0
    creation = usage.get("cache_creation_input_tokens") or 0
    stats["cache_creation"] += creation
    stats["turns"] += 1
    if turn.requested_model:
        count = got.requested_models.get(turn.requested_model, 0)
        got.requested_models[turn.requested_model] = count + 1
    cost = price_table.cost_for_usage(model, usage)
    if cost is None:
        if model not in got.unknown_models:
            got.unknown_models.append(model)
    else:
        got.cost_by_model[model] = got.cost_by_model.get(model, 0.0) + cost
        agent["cost"] += cost


def _cache_hit_rate(models: dict) -> float | None:
    read = sum(m["cache_read"] for m in models.values())
    side = _input_side(models)
    if side == 0:
        return None
    return read / side


def _input_side(models: dict) -> int:
    total = 0
    for stats in models.values():
        total += stats["input"] + stats["cache_read"] + stats["cache_creation"]
    return total


def _total_cost(cost_by_model: dict) -> float | None:
    if not cost_by_model:
        return None
    return sum(cost_by_model.values())


def _funnel(runs: list) -> list:
    calls = []
    for run in runs:
        for call in run.tool_calls:
            calls.append((call.start or "", run.agent_id, call))
    calls.sort(key=lambda item: item[0])
    return [
        {
            "agent": label,
            "tool": call.name,
            "start": call.start,
            "duration_ms": call.duration_ms,
            "error": call.error,
            "exit_code": call.exit_code,
        }
        for _, label, call in calls
    ]


def _decisions(runs: list) -> list:
    found = []
    for run in runs:
        for call in run.tool_calls:
            if call.name in _DECISION_TOOLS:
                found.append(
                    {
                        "agent": run.agent_id,
                        "tool": call.name,
                        "summary": _decision_summary(call),
                        "ts": call.start,
                    }
                )
    return found


def _decision_summary(call: ToolCall) -> str:
    args = call.input or {}
    if call.name == "AskUserQuestion":
        questions = _question_texts(args)
        return " | ".join(questions)[:_SUMMARY_LIMIT]
    if call.name == "Agent":
        kind = args.get("subagent_type", "?")
        return _summary_pair(kind, str(args.get("description", "")))
    if call.name == "Skill":
        skill = args.get("skill", "?")
        return _summary_pair(skill, str(args.get("args", "")))
    if call.name == "Workflow":
        return str(args.get("description", args.get("name", "")))[:_SUMMARY_LIMIT]
    if call.name == "ExitPlanMode":
        plan = args.get("plan")
        return str(plan)[:_SUMMARY_LIMIT] if plan else ""
    return ""


def _question_texts(args: dict) -> list[str]:
    return [
        question.get("question", "")
        for question in args.get("questions") or []
        if isinstance(question, dict)
    ]


def _summary_pair(head: str, tail: str) -> str:
    return f"{head}: {tail}"[:_SUMMARY_LIMIT]


def _pre_token_peaks(runs: list) -> list:
    return [c["pre_tokens"] for run in runs for c in run.compactions if c["pre_tokens"]]


def _friction(session: Session, runs: list, hook_log: Path | None) -> dict:
    records = logparse.load_hook_log(hook_log)
    failed = sum(1 for run in runs for call in run.tool_calls if _call_failed(call))
    pre_tokens = _pre_token_peaks(runs)
    return {
        "api_errors": sum(run.api_errors for run in runs),
        "failed_tool_calls": failed,
        "compactions": sum(len(run.compactions) for run in runs),
        "max_compaction_pre_tokens": max(pre_tokens) if pre_tokens else None,
        "permission_events": logparse.permission_events(records),
    }


def _call_failed(call: ToolCall) -> bool:
    return call.error or (call.exit_code is not None and call.exit_code != 0)


def _parse_iso(stamp: str | None) -> datetime | None:
    if not stamp:
        return None
    try:
        return datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        return None


def _git_log(repo_root: Path, ref: str) -> list[tuple[str, str]] | None:
    try:
        out = subprocess.run(
            ["git", "log", "--format=%cI%x09%s", "-n", "200", ref],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=30,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0:
        return None
    rows = []
    for line in out.stdout.splitlines():
        parts = line.split("\t", 1)
        if len(parts) == 2:
            rows.append((parts[0], parts[1]))
    return rows


def _merge_ts(repo_root: Path, after: datetime | None) -> datetime | None:
    rows = _git_log(repo_root, "main") if repo_root else None
    if not rows:
        return None
    for stamp, subject in rows:
        moment = _parse_iso(stamp)
        if moment is None:
            continue
        if after is not None and moment < after:
            continue
        if subject.rstrip().endswith(")") and "(#" in subject:
            return moment
    return None


def _branch_commits(repo_root: Path, branch: str | None) -> list[datetime]:
    if not repo_root or not branch:
        return []
    rows = _git_log(repo_root, branch)
    if rows is None:
        return []
    return [m for m in (_parse_iso(stamp) for stamp, _ in rows) if m is not None]


def _first_failed_start(runs: list) -> datetime | None:
    moments = []
    for run in runs:
        for call in run.tool_calls:
            if not _call_failed(call):
                continue
            moment = _parse_iso(call.start)
            if moment is not None:
                moments.append(moment)
    return min(moments) if moments else None


def _fix_commits_after(
    repo_root: Path | None,
    branch: str | None,
    after: datetime | None,
) -> int:
    if not repo_root or not branch or after is None:
        return 0
    rows = _git_log(repo_root, branch)
    if not rows:
        return 0
    count = 0
    for stamp, subject in rows:
        moment = _parse_iso(stamp)
        if moment is None or moment < after:
            continue
        if "fix" in subject.lower():
            count += 1
    return count


def _dora(session: Session, got: TaskMetrics, repo_root: Path | None) -> dict:
    first_prompt = _parse_iso(session.first_prompt_ts)
    merge = _merge_ts(repo_root, first_prompt)
    lead = None
    if first_prompt is not None and merge is not None:
        lead = (merge - first_prompt).total_seconds() * 1000.0
    runs = [session.primary, *session.sidechains]
    signals = (
        got.friction["failed_tool_calls"]
        + got.friction["api_errors"]
        + _fix_commits_after(repo_root, session.git_branch, _first_failed_start(runs))
    )
    return {
        "lead_time_ms": lead,
        "deployment_frequency": None,
        "change_fail_signals": signals,
        "recovery_ms": _recovery_ms(runs),
        "rework_rate": _rework_rate(got.decisions, repo_root, session.git_branch),
    }


def _recovery_ms(runs: list) -> float | None:
    failed_end = _earliest_failed_end(runs)
    if failed_end is None:
        return None
    fixed = _earliest_success_end(runs, failed_end)
    if fixed is None:
        return None
    return (fixed - failed_end).total_seconds() * 1000.0


def _earliest_failed_end(runs: list) -> datetime | None:
    failed_end = None
    for run in runs:
        for call in run.tool_calls:
            if _call_failed(call):
                end = _parse_iso(call.end)
                if end is not None and (failed_end is None or end < failed_end):
                    failed_end = end
    return failed_end


def _earliest_success_end(runs: list, failed_end: datetime) -> datetime | None:
    fixed = None
    for run in runs:
        for call in run.tool_calls:
            if _call_failed(call):
                continue
            moment = _parse_iso(call.end)
            if moment is not None and moment >= failed_end:
                fixed = moment if fixed is None or moment < fixed else fixed
    return fixed


def _rework_rate(
    decisions: list,
    repo_root: Path | None,
    branch: str | None,
) -> float | None:
    review = next((d["ts"] for d in decisions if _REVIEW_MARK in str(d).lower()), None)
    review_moment = _parse_iso(review)
    commits = _branch_commits(repo_root, branch)
    if review_moment is None or not commits:
        return None
    after = sum(1 for moment in commits if moment > review_moment)
    return after / len(commits)
