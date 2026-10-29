"""The tolerant reader for Claude Code session transcripts.

The transcript format is internal to Claude Code and drifts between
versions, so this module reads only shallow stable fields, skips
unknown entry types, and treats missing fields as absent. Usage
deduplicates on the message id, because one API turn writes several
entries. Entries with the synthetic error model never become turns.
Subagent files parse as separate agent runs.
"""

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

_SYNTHETIC_MODEL = "<synthetic>"


@dataclass
class Turn:
    message_id: str | None
    model: str | None
    requested_model: str | None
    usage: dict
    ts: str | None
    effort: str | None
    thinking_ms: int | None
    request_id: str | None


@dataclass
class ToolCall:
    id: str
    name: str
    input: dict
    start: str | None
    end: str | None = None
    error: bool = False
    exit_code: int | None = None
    duration_ms: float | None = None


@dataclass
class AgentRun:
    agent_id: str
    turns: list[Turn] = field(default_factory=list)
    tool_calls: list[ToolCall] = field(default_factory=list)
    compactions: list[dict] = field(default_factory=list)
    prompt_count: int = 0
    api_errors: int = 0
    _seen: set = field(default_factory=set)


@dataclass
class Session:
    session_id: str | None
    version: str | None
    git_branch: str | None
    entrypoint: str | None
    entry_count: int
    first_ts: str | None
    last_ts: str | None
    first_prompt_ts: str | None
    primary: AgentRun
    sidechains: list[AgentRun]


def projects_root() -> Path:
    config_dir = os.environ.get("CLAUDE_CONFIG_DIR")
    base = Path(config_dir) if config_dir else Path.home() / ".claude"
    return base / "projects"


def project_dir_for(repo_cwd: Path) -> Path:
    slug = re.sub(r"[^A-Za-z0-9._-]", "-", str(repo_cwd))
    return projects_root() / slug


def newest_transcript(project_dir: Path) -> Path | None:
    if not project_dir.is_dir():
        return None
    candidates = [p for p in project_dir.iterdir() if _is_transcript(p)]
    if not candidates:
        return None
    return max(candidates, key=_mtime)


def _is_transcript(path: Path) -> bool:
    return path.is_file() and path.suffix == ".jsonl"


def _mtime(path: Path) -> float:
    return path.stat().st_mtime


def sidechain_files(project_dir: Path, session_id: str) -> list[Path]:
    base = project_dir / session_id / "subagents"
    if not base.is_dir():
        return []
    return sorted(base.rglob("*.jsonl"))


def load_entries(path: Path) -> list[dict]:
    entries = []
    # pragma: no mutate start - the locale default equals utf-8 here
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        # pragma: no mutate end - the locale default equals utf-8 here
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except ValueError:
            continue
    return entries


def parse_session(main_path: Path) -> Session:
    entries = load_entries(main_path)
    session = Session(
        session_id=None,
        version=None,
        git_branch=None,
        entrypoint=None,
        entry_count=len(entries),
        first_ts=None,
        last_ts=None,
        first_prompt_ts=None,
        primary=AgentRun(agent_id="primary"),
        sidechains=[],
    )
    for entry in entries:
        _consume(session, entry)
    # pragma: no mutate start - an absent session id finds no sidechain files
    for path in sidechain_files(main_path.parent, session.session_id or ""):
        # pragma: no mutate end - an absent session id finds no sidechain files
        session.sidechains.append(_parse_sidechain_file(path))
    return session


def _consume(session: Session, entry: dict) -> None:
    if not isinstance(entry, dict):
        return
    _fold_identity(session, entry)
    ts = entry.get("timestamp")
    session.first_ts = _earliest(session.first_ts, ts)
    session.last_ts = _latest(session.last_ts, ts)
    if entry.get("isSidechain") is True:
        return
    _consume_kind(session, entry)


def _fold_identity(session: Session, entry: dict) -> None:
    session.session_id = session.session_id or entry.get("sessionId")
    session.version = session.version or entry.get("version")
    session.git_branch = session.git_branch or entry.get("gitBranch")
    session.entrypoint = session.entrypoint or entry.get("entrypoint")


def _consume_kind(session: Session, entry: dict) -> None:
    kind = entry.get("type")
    if kind == "assistant":
        _consume_assistant(session.primary, entry)
    elif kind == "user":
        _consume_user(session.primary, entry, session)
    elif kind == "system" and entry.get("subtype") == "compact_boundary":
        _consume_compaction(session.primary, entry)


def _earliest(current: str | None, candidate: str | None) -> str | None:
    if candidate is None:
        return current
    # pragma: no mutate block - an equal candidate returns the same value
    return candidate if current is None or candidate < current else current


def _latest(current: str | None, candidate: str | None) -> str | None:
    if candidate is None:
        return current
    # pragma: no mutate block - an equal candidate returns the same value
    return candidate if current is None or candidate > current else current


def _consume_assistant(run: AgentRun, entry: dict) -> None:
    message = entry.get("message") or {}
    if entry.get("isApiErrorMessage") or message.get("model") == _SYNTHETIC_MODEL:
        run.api_errors += 1
        return
    key = (message.get("id"), entry.get("requestId") or entry.get("requestRef"))
    # the dedup key guards the turn only; one API message writes several
    # entries, and a later entry can carry the tool_use block
    if key[0] is None or key not in run._seen:
        run._seen.add(key)
        run.turns.append(_turn_from(entry, message, key[1]))
    for block in message.get("content") or []:
        _consume_tool_use(run, block, entry)


def _turn_from(entry: dict, message: dict, request_id: str | None) -> Turn:
    return Turn(
        message_id=message.get("id"),
        model=message.get("model"),
        requested_model=entry.get("requestedModel"),
        usage=message.get("usage") or {},
        ts=entry.get("timestamp"),
        effort=entry.get("effort"),
        thinking_ms=entry.get("thinkingDurationMs"),
        request_id=request_id,
    )


def _consume_tool_use(run: AgentRun, block: object, entry: dict) -> None:
    if not isinstance(block, dict) or block.get("type") != "tool_use":
        return
    run.tool_calls.append(
        ToolCall(
            id=block.get("id") or "",
            name=block.get("name") or "",
            input=block.get("input") or {},
            start=entry.get("timestamp"),
        )
    )


def _consume_user(run: AgentRun, entry: dict, session: Session | None) -> None:
    results = _result_blocks(entry)
    if results:
        _close_tool_calls(run, results, entry)
        return
    content = (entry.get("message") or {}).get("content")
    if entry.get("isMeta") is not True and _is_prompt_content(content):
        run.prompt_count += 1
        if session is not None and session.first_prompt_ts is None:
            session.first_prompt_ts = entry.get("timestamp")


def _result_blocks(entry: dict) -> dict:
    content = (entry.get("message") or {}).get("content")
    if not isinstance(content, list):
        return {}
    results = {}
    for block in content:
        if isinstance(block, dict) and block.get("type") == "tool_result":
            results[block.get("tool_use_id")] = block
    return results


def _is_prompt_content(content: object) -> bool:
    if isinstance(content, str):
        return True
    if isinstance(content, list):
        return any(_is_text_block(block) for block in content)
    return False


def _is_text_block(block: object) -> bool:
    return isinstance(block, dict) and block.get("type") == "text"


def _close_tool_calls(run: AgentRun, results: dict, entry: dict) -> None:
    for call in run.tool_calls:
        block = results.get(call.id)
        if block is None:
            continue
        call.end = entry.get("timestamp")
        call.error = block.get("is_error") is True or _result_failed(entry)
    used = entry.get("toolUseResult")
    if isinstance(used, dict) and isinstance(used.get("exitCode"), int):
        for call in run.tool_calls:
            if call.id in results and call.exit_code is None:
                call.exit_code = used["exitCode"]


def _result_failed(entry: dict) -> bool:
    used = entry.get("toolUseResult")
    return isinstance(used, dict) and used.get("success") is False


def _consume_compaction(run: AgentRun, entry: dict) -> None:
    meta = entry.get("compactMetadata") or {}
    run.compactions.append(
        {
            "trigger": meta.get("trigger"),
            "pre_tokens": meta.get("preTokens"),
            "ts": entry.get("timestamp"),
        }
    )


def _parse_sidechain_file(path: Path) -> AgentRun:
    run = AgentRun(agent_id=path.stem)
    for entry in load_entries(path):
        if not isinstance(entry, dict):
            continue
        run.agent_id = entry.get("agentId") or run.agent_id
        kind = entry.get("type")
        if kind == "assistant":
            _consume_assistant(run, entry)
        elif kind == "user":
            _consume_user(run, entry, None)
    return run
