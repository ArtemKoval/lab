"""Pin the SessionStart charter hook: settings wiring, script behavior,
charter bounds, and drift markers against the feature-pipeline skill."""

import json
import os
import stat
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / ".claude" / "hooks" / "harness-charter.sh"
CHARTER = REPO_ROOT / ".claude" / "hooks" / "charter.md"
SETTINGS = REPO_ROOT / ".claude" / "settings.json"
PIPELINE_SKILL = REPO_ROOT / ".claude" / "skills" / "feature-pipeline" / "SKILL.md"
DRIFT_PINS = (
    "OpenSpec",
    "openspec-git-discipline",
    "Nothing proceeds on red",
    "adversarial-reviewer",
)


def _run_hook(charter_dir, event="startup"):
    """Run the hook script with a fabricated session-start event."""
    env = dict(os.environ)
    if charter_dir is None:
        env.pop("CLAUDE_PROJECT_DIR", None)
    else:
        env["CLAUDE_PROJECT_DIR"] = str(charter_dir)
    return subprocess.run(
        [str(SCRIPT)],
        input=json.dumps(
            {
                "session_id": "test-session",
                "hook_event_name": "SessionStart",
                "source": event,
            }
        ),
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
        check=False,
    )


def _write_charter(root, text):
    hook_dir = root / ".claude" / "hooks"
    hook_dir.mkdir(parents=True)
    (hook_dir / "charter.md").write_text(text, encoding="utf-8")


def _envelope(payload):
    data = json.loads(payload)
    assert list(data) == ["hookSpecificOutput"], data
    inner = data["hookSpecificOutput"]
    assert inner["hookEventName"] == "SessionStart"
    return inner["additionalContext"]


def test_script_exists_and_is_executable():
    assert SCRIPT.is_file()
    mode = os.stat(SCRIPT).st_mode
    assert mode & stat.S_IXUSR, "the hook script must carry the executable bit"


def test_settings_wire_the_hook():
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    groups = settings["hooks"]["SessionStart"]
    entry = None
    for group in groups:
        if group.get("matcher") == "startup|clear|compact":
            entry = group["hooks"][0]
    assert entry is not None, "no SessionStart group matches startup|clear|compact"
    assert entry["type"] == "command"
    assert entry["command"].endswith('.claude/hooks/harness-charter.sh"')
    assert "$CLAUDE_PROJECT_DIR" in entry["command"]
    assert isinstance(entry["timeout"], int) and entry["timeout"] > 0
    assert entry.get("async") is not True


def test_settings_keep_the_existing_keys():
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    assert settings["outputStyle"] == "ASD-STE100"
    assert settings["enabledMcpjsonServers"] == ["zai-routing-audit"]
    assert settings["permissions"]["allow"] == [
        "mcp__zai-routing-audit",
        "Bash(tools/zai_routing_audit/.venv/bin/python:*)",
        "Bash(gh issue create:*)",
    ]


def test_session_start_emits_the_charter():
    result = _run_hook(REPO_ROOT)
    assert result.returncode == 0, result.stderr
    context = _envelope(result.stdout)
    assert "feature-pipeline" in context
    assert "charter" in context.lower()


def test_hostile_charter_escapes_cleanly(tmp_path):
    hostile = (
        'back\\slash "quote"\nnewline\ttab\rreturn %s end'
    )
    _write_charter(tmp_path, hostile)
    result = _run_hook(tmp_path)
    assert result.returncode == 0, result.stderr
    context = _envelope(result.stdout)
    assert context == hostile


def test_missing_charter_falls_back(tmp_path):
    """Copy the script to a bare root so both lookups miss: CLAUDE_PROJECT_DIR
    is unset and the $0-derived root holds no charter."""
    bare = tmp_path / "bare"
    (bare / ".claude" / "hooks").mkdir(parents=True)
    copied = bare / ".claude" / "hooks" / "harness-charter.sh"
    copied.write_text(SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")
    copied.chmod(0o755)
    env = dict(os.environ)
    env.pop("CLAUDE_PROJECT_DIR", None)
    result = subprocess.run(
        [str(copied)],
        input=json.dumps({"session_id": "s", "hook_event_name": "SessionStart", "source": "startup"}),
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    context = _envelope(result.stdout)
    assert context and "\n" not in context


def test_charter_stays_within_the_line_bound():
    lines = CHARTER.read_text(encoding="utf-8").splitlines()
    assert 40 <= len(lines) <= 60, len(lines)


@pytest.mark.parametrize("pin", DRIFT_PINS)
def test_drift_pins_appear_in_both_charter_and_skill(pin):
    assert pin in CHARTER.read_text(encoding="utf-8"), pin
    assert pin in PIPELINE_SKILL.read_text(encoding="utf-8"), pin


def test_charter_holds_no_stray_control_characters():
    """The hook escapes LF, CR, and TAB only; strict JSON breaks on any
    other C0 byte, so the charter itself must not carry one."""
    text = CHARTER.read_text(encoding="utf-8")
    allowed = {"\n", "\r", "\t"}
    bad = sorted({ch for ch in text if ord(ch) < 32 and ch not in allowed})
    assert not bad, [hex(ord(ch)) for ch in bad]
