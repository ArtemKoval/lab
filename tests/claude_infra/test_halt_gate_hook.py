"""Pin the PreToolUse halt-gate hook: settings wiring, the matcher set,
and the live deny and allow paths. Mirrors test_peak_hours_hook. The
live tests run against temporary roots, never against the operator's
own halt file."""

import json
import os
import stat
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / ".claude" / "hooks" / "halt-gate.sh"
SETTINGS = REPO_ROOT / ".claude" / "settings.json"
MATCHER = "Task|Agent|Workflow|WebSearch|WebFetch|Bash|mcp__.*"
COMMAND_SUFFIX = '.claude/hooks/halt-gate.sh"'
DENY_TEXT = "halt-gate: denied"


def _run_at(root, halt_body=None, mode=None):
    """Run the copied hook against one temporary root."""
    hooks_dir = root / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    script = hooks_dir / "halt-gate.sh"
    if not script.exists():
        script.write_text(SCRIPT.read_text(encoding="utf-8"))
        script.chmod(0o755)
    if halt_body is not None:
        halt_file = root / ".claude" / "halt"
        halt_file.write_text(halt_body, encoding="utf-8")
        if mode is not None:
            halt_file.chmod(mode)
    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = str(root)
    return subprocess.run(
        [str(script)],
        input=json.dumps({"tool_name": "Task"}),
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
        check=False,
    )


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
    entry = groups[halt_positions[0]]["hooks"][0]
    assert entry["type"] == "command"
    assert entry["command"].endswith(COMMAND_SUFFIX)
    assert "$CLAUDE_PROJECT_DIR" in entry["command"]
    assert isinstance(entry["timeout"], int) and 0 < entry["timeout"] <= 10
    assert entry.get("async") is not True


def test_the_gitignore_rule_ignores_the_halt_file():
    probe = REPO_ROOT / ".claude" / "halt"
    probe.touch()
    try:
        result = subprocess.run(
            ["git", "check-ignore", str(probe)],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            check=False,
        )
    finally:
        probe.unlink()
    assert result.returncode == 0, "git check-ignore must match the halt file"


def test_a_halt_file_denies_with_reason_and_path(tmp_path):
    result = _run_at(tmp_path, "operator requested a stop\n")
    assert result.returncode == 2
    assert DENY_TEXT in result.stderr
    assert str(tmp_path / ".claude" / "halt") in result.stderr
    assert "operator requested a stop" in result.stderr
    assert "Remove the file to resume" in result.stderr


def test_a_long_single_line_is_bounded(tmp_path):
    body = "y" * 5000
    result = _run_at(tmp_path, body)
    assert result.returncode == 2
    assert "y" * 200 in result.stderr
    assert "y" * 201 not in result.stderr


def test_a_whitespace_only_first_line_denies_with_the_fallback(tmp_path):
    result = _run_at(tmp_path, "   \n")
    assert result.returncode == 2
    assert "no readable reason" in result.stderr


def test_a_carriage_return_is_stripped_from_the_reason(tmp_path):
    result = _run_at(tmp_path, "stop the loop\r\n")
    assert result.returncode == 2
    assert "stop the loop" in result.stderr
    assert "\r" not in result.stderr


@pytest.mark.skipif(os.geteuid() == 0, reason="root reads a mode-000 file")
def test_an_unreadable_halt_file_denies_with_the_fallback(tmp_path):
    result = _run_at(tmp_path, "secret reason\n", mode=0o000)
    assert result.returncode == 2
    assert "no readable reason" in result.stderr


def test_no_halt_file_anywhere_allows(tmp_path):
    result = _run_at(tmp_path, None)
    assert result.returncode == 0
    assert result.stderr == ""


def test_a_primary_checkout_halt_denies_from_a_worktree(tmp_path):
    repo = tmp_path / "primary"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    proc = subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=Suite",
         "-c", "user.email=suite@example.invalid",
         "commit", "--allow-empty", "-qm", "init"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    worktree = tmp_path / "wt"
    subprocess.run(
        ["git", "-C", str(repo), "worktree", "add", "-q", str(worktree)],
        check=True,
        capture_output=True,
    )
    (repo / ".claude").mkdir()
    (repo / ".claude" / "halt").write_text("primary halt\n", encoding="utf-8")
    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = str(worktree)
    copied = worktree / ".claude" / "hooks" / "halt-gate.sh"
    copied.parent.mkdir(parents=True)
    copied.write_text(SCRIPT.read_text(encoding="utf-8"))
    copied.chmod(0o755)
    result = subprocess.run(
        [str(copied)],
        input=json.dumps({"tool_name": "Task"}),
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
        check=False,
    )
    assert result.returncode == 2
    assert "primary halt" in result.stderr


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
