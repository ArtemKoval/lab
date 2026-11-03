"""Tests for the dspy-gate setup doctor: the read-only checks, the
install path, the JSON report, and the exit contract."""

import json
import subprocess
import sys
import types
from pathlib import Path

REPO_ROOT = Path(__file__).absolute().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools" / "dspy_gate_setup"))

import dspy_gate_setup as doctor  # noqa: E402

DOCTOR = REPO_ROOT / "tools" / "dspy_gate_setup" / "dspy_gate_setup.py"


def run_doctor(root, *flags):
    return subprocess.run(
        [sys.executable, str(DOCTOR), "--repo-root", str(root), *flags],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )


def test_the_in_process_checks_pass_on_the_real_repo():
    checks = doctor._checks(REPO_ROOT)
    assert all(checks.values()), checks


def test_the_in_process_checks_fail_on_a_bare_root(tmp_path):
    checks = doctor._checks(tmp_path)
    assert not any(checks.values())


def test_the_hooks_wired_check_reads_the_settings(tmp_path):
    settings = tmp_path / ".claude" / "settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text(json.dumps({"hooks": {}}), encoding="utf-8")
    assert doctor._hooks_wired(tmp_path) is False
    settings.write_text("not json", encoding="utf-8")
    assert doctor._hooks_wired(tmp_path) is False


def test_install_marks_the_shims_executable(tmp_path):
    hooks = tmp_path / ".claude" / "hooks"
    hooks.mkdir(parents=True)
    shim = hooks / "spec-gates-protect.sh"
    shim.write_text("#!/bin/bash\nexit 0\n", encoding="utf-8")
    doctor.install(tmp_path)
    import os

    assert os.access(shim, os.X_OK)


def test_install_builds_the_tool_venv(tmp_path, monkeypatch):
    calls = []
    exists = {"venv_python": False, "pip": False}

    def fake_exists(self):
        if self.name == "python" and ".venv" in str(self):
            return exists["venv_python"]
        if self.name == "pip":
            return exists["pip"]
        return Path(self).exists()

    def fake_run(argv, check=False):
        calls.append(argv[0:3])
        return types.SimpleNamespace(returncode=0)

    monkeypatch.setattr(doctor.subprocess, "run", fake_run)
    monkeypatch.setattr(doctor.Path, "exists", fake_exists)
    doctor.install(tmp_path)
    assert any("venv" in " ".join(map(str, c)) for c in calls)


def test_main_runs_in_process_and_reports_json(capsys):
    code = doctor.main(["--repo-root", str(REPO_ROOT), "--json"])
    report = json.loads(capsys.readouterr().out)
    assert code == 0
    assert report["ok"] is True


def test_main_fails_on_a_bare_root(capsys):
    import tempfile

    bare = Path(tempfile.mkdtemp())
    code = doctor.main(["--repo-root", str(bare)])
    assert code == 2
    assert "MISSING" in capsys.readouterr().out


def test_a_non_executable_shim_fails_the_check(tmp_path):
    shim = tmp_path / ".claude" / "hooks" / "spec-gates-protect.sh"
    shim.parent.mkdir(parents=True)
    shim.write_text("#!/bin/bash\nexit 0\n", encoding="utf-8")
    assert doctor._shim_ok(tmp_path, doctor.SHIMS[0]) is False


def test_the_doctor_main_installs_in_process(tmp_path, capsys, monkeypatch):
    """Hermetic: the subprocess calls are recorded, never executed, so
    no real venv appears in the working tree."""
    calls = []

    def fake_run(argv, check=False, **kwargs):
        calls.append((check, argv[0]))
        return types.SimpleNamespace(returncode=0)

    monkeypatch.setattr(doctor.subprocess, "run", fake_run)
    monkeypatch.setattr(doctor.Path, "exists", lambda self: False)
    monkeypatch.setattr(
        doctor, "probe_interpreter", lambda root: sys.executable
    )
    code = doctor.main(["--repo-root", str(tmp_path), "--install", "--json"])
    report = json.loads(capsys.readouterr().out)
    assert code == 2  # a bare root cannot pass the read-only checks
    assert calls and all(check is False for check, _ in calls)


def test_probe_interpreter_prefers_the_tool_venv(tmp_path):
    venv_python = tmp_path / "tools" / "dspy_gate" / ".venv" / "bin" / "python"
    venv_python.parent.mkdir(parents=True)
    venv_python.write_text("", encoding="utf-8")
    assert str(doctor.probe_interpreter(tmp_path)) == str(venv_python)


def test_probe_interpreter_falls_back_to_this_interpreter(tmp_path):
    import sys as _sys

    assert doctor.probe_interpreter(tmp_path) == _sys.executable


def test_the_real_repo_passes_read_only():
    result = run_doctor(REPO_ROOT)
    assert result.returncode == 0, result.stdout
    assert "gates.yaml" in result.stdout


def test_the_real_repo_reports_json_with_ok():
    result = run_doctor(REPO_ROOT, "--json")
    report = json.loads(result.stdout)
    assert report["ok"] is True
    assert all(report["checks"].values())


def test_a_root_without_the_tool_fails(tmp_path):
    result = run_doctor(tmp_path)
    assert result.returncode == 2
    report = json.loads(run_doctor(tmp_path, "--json").stdout)
    assert report["ok"] is False


def test_the_doctor_contract_holds():
    source = DOCTOR.read_text(encoding="utf-8")
    assert "--install" in source
    assert "--json" in source
    assert "--repo-root" in source


def test_the_registry_carries_the_unit():
    registry = json.loads(
        (REPO_ROOT / "tools" / "project_setup" / "registry.json").read_text(
            encoding="utf-8"
        )
    )
    ids = {unit["id"] for unit in registry["units"]}
    assert "dspy-gate" in ids
    unit = next(u for u in registry["units"] if u["id"] == "dspy-gate")
    assert unit["check"][0] == "python3"
    assert "dspy_gate_setup.py" in " ".join(unit["check"])
