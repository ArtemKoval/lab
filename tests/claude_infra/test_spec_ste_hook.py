"""Pin the PreToolUse STE gate hook: settings wiring, script behavior,
and fail-open degradation. Mirrors test_harness_charter."""

import json
import os
import stat
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / ".claude" / "hooks" / "spec-ste-gate.sh"
SETTINGS = REPO_ROOT / ".claude" / "settings.json"
SPEC_TARGET = "openspec/specs/fde/chat/spec.md"


def _run_hook(root, event, unset_project_dir=False):
    env = dict(os.environ)
    if unset_project_dir:
        env.pop("CLAUDE_PROJECT_DIR", None)
    else:
        env["CLAUDE_PROJECT_DIR"] = str(root)
    return subprocess.run(
        [str(SCRIPT)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
        check=False,
    )


def _write_event(rel, content):
    return {
        "tool_name": "Write",
        "tool_input": {"file_path": str(REPO_ROOT / rel), "content": content},
    }


def test_script_exists_and_is_executable():
    assert SCRIPT.is_file()
    mode = os.stat(SCRIPT).st_mode
    assert mode & stat.S_IXUSR, "the hook script must carry the executable bit"


def test_settings_wire_the_ste_hook():
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    groups = settings["hooks"]["PreToolUse"]
    entry = None
    for group in groups:
        if group.get("matcher") == "Write|Edit":
            entry = group["hooks"][0]
    assert entry is not None, "no PreToolUse group matches Write|Edit"
    assert entry["type"] == "command"
    assert entry["command"].endswith('.claude/hooks/spec-ste-gate.sh"')
    assert "$CLAUDE_PROJECT_DIR" in entry["command"]
    assert isinstance(entry["timeout"], int) and entry["timeout"] > 0
    assert entry.get("async") is not True


def test_settings_keep_the_prior_hooks_and_keys():
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    session_groups = [
        group
        for group in settings["hooks"]["SessionStart"]
        if group.get("matcher") == "startup|clear|compact"
    ]
    assert session_groups, "the charter hook must stay wired"
    assert settings["outputStyle"] == "ASD-STE100"
    assert settings["enabledMcpjsonServers"] == ["zai-routing-audit"]


def test_a_blockable_write_exits_2(capsys):
    result = _run_hook(REPO_ROOT, _write_event(SPEC_TARGET, "Run it; stop it.\n"))
    assert result.returncode == 2
    assert "semicolon" in result.stderr


def test_a_clean_write_exits_0():
    result = _run_hook(REPO_ROOT, _write_event(SPEC_TARGET, "Run it now.\n"))
    assert result.returncode == 0


def test_an_archive_write_exits_0():
    result = _run_hook(
        REPO_ROOT,
        _write_event("openspec/changes/archive/old/spec.md", "Run it; stop it.\n"),
    )
    assert result.returncode == 0


def test_a_missing_root_fails_open(tmp_path):
    """Copy the script to a bare root so both lookups miss:
    CLAUDE_PROJECT_DIR is unset and the $0-derived root holds no package."""
    bare = tmp_path / "bare"
    (bare / ".claude" / "hooks").mkdir(parents=True)
    copied = bare / ".claude" / "hooks" / "spec-ste-gate.sh"
    copied.write_text(SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")
    copied.chmod(0o755)
    env = dict(os.environ)
    env.pop("CLAUDE_PROJECT_DIR", None)
    result = subprocess.run(
        [str(copied)],
        input=json.dumps(_write_event(SPEC_TARGET, "Run it; stop it.\n")),
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0
    assert "the write passes" in result.stderr
