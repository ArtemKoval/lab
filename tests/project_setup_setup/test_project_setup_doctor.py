"""Tests for the project-setup registry doctor.

The tests import the doctor module in process, so the coverage run
sees the module, and one smoke test runs the CLI as a subprocess.
"""

import json
import subprocess
import sys
from pathlib import Path

import project_setup_setup as doctor
import pytest

REPO_ROOT = Path(__file__).absolute().parents[2]
MODULE_PATH = REPO_ROOT / "tools" / "project_setup_setup" / "project_setup_setup.py"
SKILL = REPO_ROOT / ".claude" / "skills" / "project-setup" / "SKILL.md"

OK_CHECK = [sys.executable, "-c", "pass"]
FAIL_CHECK = [sys.executable, "-c", "import sys; sys.exit(3)"]
MARKER_CHECK = [
    sys.executable,
    "-c",
    "import pathlib, sys; sys.exit(0 if pathlib.Path('m').exists() else 1)",
]
MARKER_INSTALL = [
    sys.executable,
    "-c",
    "import pathlib; pathlib.Path('m').touch()",
]
NOOP_INSTALL = "echo 'stdlib-only; no install needed'"


def make_registry(repo_root, units, raw=None):
    """Write a registry file under repo_root and return the root."""
    target = repo_root / "tools" / "project_setup"
    target.mkdir(parents=True, exist_ok=True)
    payload = raw if raw is not None else json.dumps({"version": 1, "units": units})
    (target / "registry.json").write_text(payload, encoding="utf-8")
    return repo_root


def make_unit(unit_id, check=OK_CHECK, install=NOOP_INSTALL):
    """Return one well-formed fixture unit."""
    return {
        "id": unit_id,
        "kind": "system-tool",
        "purpose": "fixture unit",
        "check": check,
        "install": install,
        "requires": "none",
    }


def run_main(repo_root, *flags):
    """Run doctor.main in process and return (code, report_or_none)."""
    return doctor.main(["--repo-root", str(repo_root), *flags])


@pytest.mark.parametrize(
    ("raw", "fragment"),
    [
        ("{not json", "registry unreadable"),
        ('{"version": 1}', "registry holds no units list"),
        ("[1, 2]", "registry holds no units list"),
    ],
)
def test_load_registry_defects(tmp_path, raw, fragment):
    make_registry(tmp_path, [], raw=raw)
    _, defects = doctor.load_registry(tmp_path / "tools" / "project_setup" / "registry.json")
    assert defects and fragment in defects[0]


def test_load_registry_names_unit_defects(tmp_path):
    unit = make_unit("alpha")
    del unit["check"]
    no_id = make_unit("temp")
    del no_id["id"]
    path = (
        make_registry(tmp_path, [unit, make_unit("alpha"), no_id])
        / "tools"
        / "project_setup"
        / "registry.json"
    )
    _, defects = doctor.load_registry(path)
    joined = " | ".join(defects)
    assert "unit alpha misses check" in joined
    assert "unit id repeats: alpha" in joined
    assert "unit misses id" in joined


def test_load_registry_tolerates_a_non_object_unit(tmp_path):
    path = make_registry(tmp_path, []) / "tools" / "project_setup" / "registry.json"
    path.write_text('{"version": 1, "units": [7]}', encoding="utf-8")
    units, defects = doctor.load_registry(path)
    assert units == [7]
    assert defects == ["unit is not an object"]


def test_plan_units_skips_junk_units():
    rows, errors = doctor.plan_units([7, {"kind": "x"}], [])
    assert rows == []
    assert errors == []


def test_plan_units_filters_and_names_unknowns():
    units = [make_unit("alpha"), make_unit("beta")]
    rows, errors = doctor.plan_units(units, ["alpha", "ghost"])
    assert [row["id"] for row in rows] == ["alpha"]
    assert rows[0]["status"] == "unchecked"
    assert errors == ["unknown unit: ghost"]


def test_plan_view_joins_an_argv_install():
    rows = [{"id": "a", "unit": make_unit("a", install=["echo", "hi"]), "status": "absent"}]
    view = doctor.plan_view(rows)
    assert view == [{"id": "a", "status": "absent", "install": "echo hi"}]


def test_main_unstartable_argv_install_fails(tmp_path, capsys):
    units = [make_unit("alpha", check=MARKER_CHECK, install=["no-such-install-binary-xyz"])]
    make_registry(tmp_path, units)
    code = run_main(tmp_path, "--json", "--units", "alpha", "--install")
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == 2
    assert report["units"][0]["status"] == "install_failed"
    assert "install command failed to start" in captured.err


def test_main_valid_plan_reports_unchecked(tmp_path, capsys):
    make_registry(tmp_path, [make_unit("alpha")])
    code = run_main(tmp_path, "--json")
    out = capsys.readouterr().out
    report = json.loads(out)
    assert code == 0 and report["ok"] is True
    assert report["units"][0]["status"] == "unchecked"
    assert report["units"][0]["install"] == NOOP_INSTALL
    assert report["errors"] == []
    assert out.index('"errors"') < out.index('"ok"') < out.index('"units"')


def test_run_install_command_uses_shell_for_strings(monkeypatch, tmp_path):
    seen = []

    def fake_run(*args, **kwargs):
        seen.append(kwargs.get("shell"))
        return type("R", (), {"returncode": 0})()

    monkeypatch.setattr(doctor.subprocess, "run", fake_run)
    assert doctor.run_install_command("echo hi", tmp_path) == 0
    assert doctor.run_install_command(["echo", "hi"], tmp_path) == 0
    assert seen == [True, None]


def test_main_failing_shell_string_install_fails(tmp_path, capsys):
    units = [make_unit("alpha", check=MARKER_CHECK, install="exit 3")]
    make_registry(tmp_path, units)
    code = run_main(tmp_path, "--json", "--units", "alpha", "--install")
    report = json.loads(capsys.readouterr().out)
    assert code == 2
    assert report["units"][0]["status"] == "install_failed"


def test_help_names_the_first_docstring_line():
    done = subprocess.run(
        [sys.executable, str(MODULE_PATH), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    first_line = doctor.__doc__.splitlines()[0]
    assert done.returncode == 0
    assert first_line in done.stdout


def test_main_classifies_present_and_absent(tmp_path, capsys):
    make_registry(tmp_path, [make_unit("ok"), make_unit("gone", check=FAIL_CHECK)])
    code = run_main(tmp_path, "--json", "--units", "ok,gone")
    report = json.loads(capsys.readouterr().out)
    statuses = {row["id"]: row["status"] for row in report["units"]}
    assert code == 0 and statuses == {"ok": "present", "gone": "absent"}


def test_main_install_flow_installs_and_reads_back(tmp_path, capsys):
    units = [make_unit("alpha", check=MARKER_CHECK, install=MARKER_INSTALL)]
    make_registry(tmp_path, units)
    code = run_main(tmp_path, "--json", "--units", "alpha", "--install")
    report = json.loads(capsys.readouterr().out)
    assert code == 0
    assert report["units"][0]["status"] == "installed"
    assert (tmp_path / "m").exists()


@pytest.mark.parametrize(
    ("check", "install", "status"),
    [
        (FAIL_CHECK, [sys.executable, "-c", "pass"], "readback_mismatch"),
        (
            MARKER_CHECK,
            [sys.executable, "-c", "import sys; sys.exit(4)"],
            "install_failed",
        ),
    ],
)
def test_main_install_failures(tmp_path, capsys, check, install, status):
    make_registry(tmp_path, [make_unit("alpha", check=check, install=install)])
    code = run_main(tmp_path, "--json", "--units", "alpha", "--install")
    report = json.loads(capsys.readouterr().out)
    assert code == 2
    assert report["units"][0]["status"] == status


def test_main_blanket_install_refuses(tmp_path, capsys):
    units = [make_unit("alpha", check=MARKER_CHECK, install=MARKER_INSTALL)]
    make_registry(tmp_path, units)
    code = run_main(tmp_path, "--json", "--install")
    report = json.loads(capsys.readouterr().out)
    assert code == 2
    assert any("--install requires --units" in line for line in report["errors"])
    assert not (tmp_path / "m").exists()


def test_main_unknown_unit_installs_nothing(tmp_path, capsys):
    make_registry(tmp_path, [make_unit("alpha", check=OK_CHECK)])
    code = run_main(tmp_path, "--units", "ghost", "--install")
    out = capsys.readouterr().out
    assert code == 2
    assert "unknown unit: ghost" in out


def test_main_check_that_fails_to_start(tmp_path, capsys):
    units = [make_unit("alpha", check=["no-such-binary-xyz"])]
    make_registry(tmp_path, units)
    code = run_main(tmp_path, "--json", "--units", "alpha")
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == 0
    assert report["units"][0]["status"] == "absent"
    assert "check command failed to start" in captured.err


def test_main_invalid_registry_exits_two(tmp_path, capsys):
    make_registry(tmp_path, [], raw="{not json")
    code = run_main(tmp_path, "--json")
    report = json.loads(capsys.readouterr().out)
    assert code == 2
    assert report["ok"] is False


def test_main_present_unit_skips_the_install(tmp_path, capsys):
    units = [make_unit("alpha", check=OK_CHECK, install=MARKER_INSTALL)]
    make_registry(tmp_path, units)
    code = run_main(tmp_path, "--units", "alpha", "--install")
    out = capsys.readouterr().out
    assert code == 0
    assert "alpha: present" in out
    assert not (tmp_path / "m").exists()


def test_main_text_output_carries_the_lines(tmp_path, capsys):
    make_registry(tmp_path, [make_unit("alpha")])
    code = run_main(tmp_path)
    out = capsys.readouterr().out
    assert code == 0
    assert "alpha: unchecked" in out and NOOP_INSTALL in out


def test_main_shell_string_install_runs(tmp_path, capsys):
    shell_install = f"{sys.executable} -c 'import pathlib; pathlib.Path(\"m\").touch()'"
    units = [make_unit("alpha", check=MARKER_CHECK, install=shell_install)]
    make_registry(tmp_path, units)
    code = run_main(tmp_path, "--json", "--units", "alpha", "--install")
    report = json.loads(capsys.readouterr().out)
    assert code == 0 and report["units"][0]["status"] == "installed"
    assert (tmp_path / "m").exists()


def test_skill_carries_the_consent_rules():
    text = " ".join(SKILL.read_text(encoding="utf-8").split())
    section = text.split("## Consent rules", 1)[1]
    assert "The doctor's read-only run is the plan" in section
    assert "Detection selects nothing" in section
    assert "only a unit with explicit consent installs" in section
    assert "makes a backup copy of each file it replaces" in section
    assert "covers only registry-owned state" in section
