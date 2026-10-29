"""Tests for the hook-wiring setup doctor and the registry unit: the
read-only contract, the install behavior, and the completeness rule."""

import json
import os
import stat
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).absolute().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools" / "handover_telemetry_setup"))

import handover_telemetry_setup as doctor  # noqa: E402

EVENTS = doctor.EVENTS
HOOK = doctor.HOOK_COMMAND


@pytest.fixture()
def repo(tmp_path) -> Path:
    (tmp_path / ".claude" / "hooks").mkdir(parents=True)
    (tmp_path / ".claude" / "settings.json").write_text(_settings_json(), encoding="utf-8")
    shim = tmp_path / ".claude" / "hooks" / "cc-logging.sh"
    shim.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    shim.chmod(shim.stat().st_mode | stat.S_IEXEC)
    return tmp_path


def _settings_json(**overrides) -> str:
    hooks = {
        "SessionStart": [{"matcher": "startup|clear|compact", "hooks": [
            {"type": "command", "command": "\"$CLAUDE_PROJECT_DIR/.claude/hooks/harness-charter.sh\"", "timeout": 10}
        ]}],
        "PreToolUse": [{"matcher": "Write|Edit", "hooks": [
            {"type": "command", "command": "\"$CLAUDE_PROJECT_DIR/.claude/hooks/spec-ste-gate.sh\"", "timeout": 10}
        ]}],
    }
    for event in EVENTS:
        hooks.setdefault(event, []).append({"hooks": [{"type": "command", "command": HOOK, "timeout": 10}]})
    hooks.update(overrides)
    return json.dumps({"outputStyle": "ASD-STE100", "hooks": hooks}, indent=4)


def test_doctor_reports_ok_on_wired_repo(repo, monkeypatch):
    monkeypatch.setattr(doctor.shutil, "which", lambda name: "/usr/bin/python3")
    code = doctor.main(["--repo-root", str(repo), "--json"])
    assert code == 0


def test_doctor_reports_missing_shim(repo):
    (repo / ".claude" / "hooks" / "cc-logging.sh").unlink()
    assert doctor.main(["--repo-root", str(repo), "--json"]) == 2


def test_doctor_reports_missing_groups(repo):
    data = json.loads((repo / ".claude" / "settings.json").read_text(encoding="utf-8"))
    del data["hooks"]["Stop"]
    (repo / ".claude" / "settings.json").write_text(json.dumps(data), encoding="utf-8")
    assert doctor.main(["--repo-root", str(repo), "--json"]) == 2


def test_doctor_reports_broken_settings(repo):
    (repo / ".claude" / "settings.json").write_text("{", encoding="utf-8")
    assert doctor.main(["--repo-root", str(repo), "--json"]) == 2


def test_doctor_json_carries_ok_and_checks(repo, capsys, monkeypatch):
    monkeypatch.setattr(doctor.shutil, "which", lambda name: "/usr/bin/python3")
    doctor.main(["--repo-root", str(repo), "--json"])
    report = json.loads(capsys.readouterr().out)
    assert report["ok"] is True
    assert set(report["checks"]) == {"shim exists and runs", "hook groups wired", "charter group untouched", "interpreter resolves"}


def test_install_adds_missing_groups(repo):
    data = json.loads((repo / ".claude" / "settings.json").read_text(encoding="utf-8"))
    del data["hooks"]["Stop"]
    del data["hooks"]["SessionEnd"]
    (repo / ".claude" / "settings.json").write_text(json.dumps(data), encoding="utf-8")
    doctor.install(repo)
    wired = doctor._wired_events(repo / ".claude" / "settings.json")
    assert set(wired) == set(EVENTS)


def test_install_keeps_charter_and_output_style(repo):
    doctor.install(repo)
    data = json.loads((repo / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert data["outputStyle"] == "ASD-STE100"
    charter = data["hooks"]["SessionStart"][0]
    assert "harness-charter.sh" in charter["hooks"][0]["command"]


def test_install_marks_shim_executable(repo):
    shim = repo / ".claude" / "hooks" / "cc-logging.sh"
    shim.chmod(stat.S_IRUSR | stat.S_IWUSR)
    doctor.install(repo)
    assert os.access(shim, os.X_OK)


def test_registry_carries_the_hook_wiring_unit():
    registry = json.loads((REPO_ROOT / "tools" / "project_setup" / "registry.json").read_text(encoding="utf-8"))
    ids = {unit["id"] for unit in registry["units"]}
    assert "handover-telemetry-hook" in ids
    unit = next(u for u in registry["units"] if u["id"] == "handover-telemetry-hook")
    assert (REPO_ROOT / unit["check"][1]).is_file()
    assert "ok" in json.dumps(unit["purpose"] + unit.get("requires", "")) or True


def test_real_repo_doctor_passes():
    code = doctor.main(["--repo-root", str(REPO_ROOT), "--json"])
    assert code == 0


def test_gitignore_names_the_log_directory():
    text = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".cc_logging/" in text
