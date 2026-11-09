"""Tests for the dead-code scanner of the owned tools.

The tests import the scanner module in process, so the coverage run
sees the module, and one CLI smoke run exercises --help as a
subprocess.
"""

import json
import subprocess
import sys
from pathlib import Path

import dead_export_scan as scanner

REPO_ROOT = Path(__file__).absolute().parents[2]
MODULE_PATH = REPO_ROOT / "tools" / "dead_export_scan" / "dead_export_scan.py"

DEAD_FUNCTION = "def gone():\n    return 1\n"
DEAD_CLASS = "class Unused:\n    pass\n"
DEAD_IMPORT = "import os\n\nVALUE = 1\n"


def make_tree(tmp_path, name, content):
    """Write one Python file into a fixture package dir and return it."""
    package = tmp_path / name
    package.mkdir(parents=True, exist_ok=True)
    target = package / "module.py"
    target.write_text(content, encoding="utf-8")
    return target


def test_scan_names_dead_function_class_and_import(tmp_path):
    make_tree(tmp_path, "fixture_a", DEAD_FUNCTION + "\n" + DEAD_CLASS + "\n" + DEAD_IMPORT)
    findings, errors = scanner.scan([tmp_path / "fixture_a"], 60)
    assert errors == []
    names = {finding["name"] for finding in findings}
    assert "gone" in names
    assert "Unused" in names
    types = {finding["type"] for finding in findings}
    assert "import" in types


def test_scan_clean_tree_exits_ok(tmp_path):
    target = make_tree(tmp_path, "fixture_b", "def used():\n    return 1\n\n\nused()\n")
    findings, errors = scanner.scan([target.parent], 60)
    assert findings == []
    assert errors == []


def test_scan_skips_excluded_directories(tmp_path):
    skipped = tmp_path / "venv" / "lib"
    skipped.mkdir(parents=True)
    (skipped / "dead.py").write_text(DEAD_FUNCTION, encoding="utf-8")
    findings, errors = scanner.scan([tmp_path], 60)
    assert findings == []
    assert errors == []


def test_scan_names_a_missing_path_as_error(tmp_path):
    findings, errors = scanner.scan([tmp_path / "nowhere"], 60)
    assert findings == []
    assert errors == [f"path missing: {tmp_path / 'nowhere'}"]


def test_missing_vulture_is_an_operational_error(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "vulture", None)
    findings, errors = scanner.scan([tmp_path], 60)
    assert findings == []
    assert len(errors) == 1
    assert "vulture missing" in errors[0]
    assert "requirements.txt" in errors[0]


def test_main_json_reports_findings(tmp_path, capsys):
    make_tree(tmp_path, "fixture_c", DEAD_FUNCTION)
    code = scanner.main(["--paths", str(tmp_path / "fixture_c"), "--json"])
    report = json.loads(capsys.readouterr().out)
    assert code == 2
    assert report["ok"] is False
    assert report["findings"][0]["name"] == "gone"


def test_main_json_reports_clean(tmp_path, capsys):
    target = make_tree(tmp_path, "fixture_d", "def used():\n    return 1\n\n\nused()\n")
    code = scanner.main(["--paths", str(target.parent), "--json"])
    out = capsys.readouterr().out
    report = json.loads(out)
    assert code == 0
    assert report["ok"] is True
    assert report["findings"] == []
    assert report["errors"] == []
    assert out.index('"errors"') < out.index('"findings"') < out.index('"ok"')


def test_main_text_output_carries_the_lines(tmp_path, capsys):
    make_tree(tmp_path, "fixture_e", DEAD_FUNCTION)
    code = scanner.main(["--paths", str(tmp_path / "fixture_e")])
    out = capsys.readouterr().out
    assert code == 2
    assert "gone (function)" in out


def test_main_missing_vulture_reports_error(tmp_path, capsys, monkeypatch):
    monkeypatch.setitem(sys.modules, "vulture", None)
    code = scanner.main(["--paths", str(tmp_path), "--json"])
    report = json.loads(capsys.readouterr().out)
    assert code == 2
    assert report["ok"] is False
    assert "vulture missing" in report["errors"][0]


def test_cli_smoke_exits_zero():
    done = subprocess.run(
        [sys.executable, str(MODULE_PATH), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0


def test_scan_accepts_a_single_file(tmp_path):
    target = make_tree(tmp_path, "fixture_f", DEAD_FUNCTION)
    findings, errors = scanner.scan([target], 60)
    assert errors == []
    assert [finding["name"] for finding in findings] == ["gone"]


def test_scan_all_missing_paths_skips_scavenge(tmp_path):
    findings, errors = scanner.scan(
        [tmp_path / "gone_a", tmp_path / "gone_b"], 60
    )
    assert findings == []
    assert len(errors) == 2


def test_scan_ignores_a_non_python_file(tmp_path):
    target = tmp_path / "notes.txt"
    target.write_text("def gone():\n    return 1\n", encoding="utf-8")
    findings, errors = scanner.scan([target], 60)
    assert findings == []
    assert errors == []


def test_main_text_mode_prints_errors(tmp_path, capsys, monkeypatch):
    monkeypatch.setitem(sys.modules, "vulture", None)
    code = scanner.main(["--paths", str(tmp_path)])
    out = capsys.readouterr().out
    assert code == 2
    assert "error: vulture missing" in out


def test_help_names_the_first_docstring_line():
    done = subprocess.run(
        [sys.executable, str(MODULE_PATH), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    first_line = scanner.__doc__.splitlines()[0]
    assert done.returncode == 0
    assert first_line in done.stdout
