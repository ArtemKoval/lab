"""Pin the PreToolUse peak-hours gate hook: settings wiring, the
matcher set, and the live deny and allow paths. Mirrors
test_spec_ste_hook."""

import json
import os
import re
import stat
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / ".claude" / "hooks" / "peak-hours-gate.sh"
SETTINGS = REPO_ROOT / ".claude" / "settings.json"
MATCHER = "Task|Agent|Workflow|WebSearch|WebFetch|Bash|mcp__.*"

IN_WINDOW_NOW = "2026-11-03T07:00:00Z"  # 15:00 SGT Tuesday
OUT_WINDOW_NOW = "2026-11-03T11:00:00Z"  # 19:00 SGT Tuesday


def _run_hook(event, env_extra=None):
    env = dict(os.environ)
    # A host export of the override or the clock seam must not flip the
    # pinned verdicts.
    env.pop("ZAI_PEAK_HOURS_OVERRIDE", None)
    env.pop("PEAK_HOURS_GATE_NOW", None)
    env["CLAUDE_PROJECT_DIR"] = str(REPO_ROOT)
    env.update(env_extra or {})
    return subprocess.run(
        [str(SCRIPT)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
        check=False,
    )


def _hook_entry():
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    for group in settings["hooks"]["PreToolUse"]:
        if group.get("matcher") == MATCHER:
            return group["hooks"][0]
    return None


def test_script_exists_and_is_executable():
    assert SCRIPT.is_file()
    mode = os.stat(SCRIPT).st_mode
    assert mode & stat.S_IXUSR, "the hook script must carry the executable bit"


def test_settings_wire_the_gate_hook():
    entry = _hook_entry()
    assert entry is not None, "no PreToolUse group matches the gate matcher"
    assert entry["type"] == "command"
    assert entry["command"].endswith('.claude/hooks/peak-hours-gate.sh"')
    assert "$CLAUDE_PROJECT_DIR" in entry["command"]
    assert isinstance(entry["timeout"], int) and 0 < entry["timeout"] <= 10
    assert entry.get("async") is not True


def test_settings_keep_the_prior_hooks():
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    matchers = [group.get("matcher") for group in settings["hooks"]["PreToolUse"]]
    assert "Write|Edit" in matchers, "the spec STE group must stay wired"
    session_groups = [
        group
        for group in settings["hooks"]["SessionStart"]
        if group.get("matcher") == "startup|clear|compact"
    ]
    assert session_groups, "the charter hook must stay wired"


def test_matcher_covers_the_block_set():
    for name in (
        "Task",
        "Agent",
        "Workflow",
        "WebSearch",
        "WebFetch",
        "Bash",
        "mcp__zai-routing-audit__usage_report",
        "mcp__dspy-gate__gate_status",
    ):
        assert re.fullmatch(MATCHER, name), name


def test_matcher_excludes_the_allow_tools():
    for name in ("Read", "Write", "Edit", "Glob", "Grep", "SendMessage"):
        assert not re.fullmatch(MATCHER, name), name


def test_a_block_set_call_denies_in_window():
    result = _run_hook(
        {"tool_name": "Task"}, {"PEAK_HOURS_GATE_NOW": IN_WINDOW_NOW}
    )
    assert result.returncode == 2
    assert "ZAI_PEAK_HOURS_OVERRIDE" in result.stderr


def test_a_block_set_call_allows_outside_window():
    result = _run_hook(
        {"tool_name": "Task"}, {"PEAK_HOURS_GATE_NOW": OUT_WINDOW_NOW}
    )
    assert result.returncode == 0
    assert result.stderr == ""


def test_a_bash_live_path_denies_in_window():
    event = {"tool_name": "Bash", "tool_input": {"command": "python -m dspy_gate optimize x"}}
    result = _run_hook(event, {"PEAK_HOURS_GATE_NOW": IN_WINDOW_NOW})
    assert result.returncode == 2


def test_an_ordinary_bash_allows_in_window():
    event = {"tool_name": "Bash", "tool_input": {"command": "git status"}}
    result = _run_hook(event, {"PEAK_HOURS_GATE_NOW": IN_WINDOW_NOW})
    assert result.returncode == 0
    assert result.stderr == ""
