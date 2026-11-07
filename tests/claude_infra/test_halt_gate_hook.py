"""Pin the PreToolUse halt-gate hook: settings wiring, the matcher set,
and the live deny and allow paths. Mirrors test_peak_hours_hook."""

import json
import os
import stat
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / ".claude" / "hooks" / "halt-gate.sh"
SETTINGS = REPO_ROOT / ".claude" / "settings.json"
MATCHER = "Task|Agent|Workflow|WebSearch|WebFetch|Bash|mcp__.*"
COMMAND_SUFFIX = '.claude/hooks/halt-gate.sh"'
DENY_TEXT = "halt-gate: denied"


def _run_hook(halt_body=None, env_extra=None):
    if halt_body is not None:
        (REPO_ROOT / ".claude" / "halt").write_text(halt_body, encoding="utf-8")
    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = str(REPO_ROOT)
    env.update(env_extra or {})
    try:
        return subprocess.run(
            [str(SCRIPT)],
            input=json.dumps({"tool_name": "Task"}),
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
            check=False,
        )
    finally:
        halt_file = REPO_ROOT / ".claude" / "halt"
        if halt_file.exists():
            halt_file.unlink()


def test_script_exists_and_is_executable():
    assert SCRIPT.is_file()
    mode = os.stat(SCRIPT).st_mode
    assert mode & stat.S_IXUSR, "the hook script must carry the executable bit"


def test_settings_wire_the_halt_gate_after_the_peak_gate():
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    groups = [
        group
        for group in settings["hooks"]["PreToolUse"]
        if group.get("matcher") == MATCHER
    ]
    entries = [
        group["hooks"][0]
        for group in groups
        if "halt-gate.sh" in group["hooks"][0]["command"]
    ]
    assert len(entries) == 1
    entry = entries[0]
    assert entry["type"] == "command"
    assert entry["command"].endswith(COMMAND_SUFFIX)
    assert "$CLAUDE_PROJECT_DIR" in entry["command"]
    assert isinstance(entry["timeout"], int) and 0 < entry["timeout"] <= 10
    assert entry.get("async") is not True
    peak_positions = [
        index
        for index, group in enumerate(groups)
        if "peak-hours-gate.sh" in group["hooks"][0]["command"]
    ]
    halt_positions = [
        index
        for index, group in enumerate(groups)
        if "halt-gate.sh" in group["hooks"][0]["command"]
    ]
    assert peak_positions and halt_positions
    assert min(halt_positions) > max(peak_positions), (
        "the halt group must sit after the peak group, whose contract test "
        "reads the first group with the matcher"
    )


def test_the_gitignore_carries_the_halt_file():
    text = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "/.claude/halt" in text


def test_a_halt_file_denies_with_the_reason():
    result = _run_hook("operator requested a stop\n")
    assert result.returncode == 2
    assert DENY_TEXT in result.stderr
    assert "operator requested a stop" in result.stderr
    assert "Remove the file to resume" in result.stderr


def test_a_long_reason_is_cut():
    result = _run_hook("x" * 500 + "\n")
    assert result.returncode == 2
    assert "x" * 200 in result.stderr
    assert "x" * 201 not in result.stderr


def test_an_empty_halt_file_denies_with_the_fallback_reason():
    result = _run_hook("\n")
    assert result.returncode == 2
    assert DENY_TEXT in result.stderr
    assert "no readable reason" in result.stderr


def test_no_halt_file_allows():
    result = _run_hook(None)
    assert result.returncode == 0
    assert result.stderr == ""


def test_no_resolvable_root_allows(tmp_path):
    bare = tmp_path / "elsewhere"
    bare.mkdir()
    copied = bare / "hook.sh"
    copied.write_text(SCRIPT.read_text(encoding="utf-8"))
    copied.chmod(0o755)
    env = dict(os.environ)
    env.pop("CLAUDE_PROJECT_DIR", None)
    result = subprocess.run(
        [str(copied)],
        input=json.dumps({"tool_name": "Task"}),
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0
    assert result.stderr == ""
