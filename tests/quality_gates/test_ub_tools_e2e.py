"""Live runs of the three vendored gate launchers against a fixture tree.
Opt-in through UB_TOOLS_E2E=1 with the three unit venvs built. The default
suite never runs a launcher."""

import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        os.environ.get("UB_TOOLS_E2E") != "1",
        reason="opt-in via UB_TOOLS_E2E=1",
    ),
    pytest.mark.skipif(
        not all(
            (REPO_ROOT / f"tools/{tool}/.venv/bin/python").is_file()
            for tool in ("crapper", "dryer", "mutator")
        ),
        reason="the three gate venvs are not built",
    ),
]

CONFORMING = "def one(x):\n    return x\n"
BREACH = (
    "def grade(score):\n"
    "    if score >= 90:\n"
    '        return "A"\n'
    "    elif score >= 80:\n"
    '        return "B"\n'
    "    elif score >= 70:\n"
    '        return "C"\n'
    "    elif score >= 60:\n"
    '        return "D"\n'
    "    elif score >= 50:\n"
    '        return "E"\n'
    "    else:\n"
    '        return "F"\n'
)


def _write(root, name, text):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _run(tool, args, cwd):
    return subprocess.run(
        [str(REPO_ROOT / f"tools/{tool}/{tool}"), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )


def _coverage_lcov(root, tool):
    py = str(REPO_ROOT / f"tools/{tool}/.venv/bin/python")
    data = root / "target" / "coverage" / "python" / ".coverage"
    subprocess.run(
        [py, "-m", "coverage", "run", f"--data-file={data}", "--source=src", "-m", "pytest", "-q"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=300,
        check=True,
    )
    report = root / "target" / "coverage" / "python" / "lcov.info"
    subprocess.run(
        [py, "-m", "coverage", "lcov", f"--data-file={data}", "-o", str(report)],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=300,
        check=True,
    )


def test_crapper_gate_passes_a_conforming_unit(tmp_path):
    _write(tmp_path, "src/one.py", CONFORMING)
    _write(tmp_path, "test_one.py", "from src.one import one\n\ndef test_one():\n    assert one(1) == 1\n")
    _coverage_lcov(tmp_path, "crapper")
    result = _run("crapper", ["--threshold", "10", "--use-existing-coverage", "src/one.py"], tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_crapper_gate_fails_a_crap_breach(tmp_path):
    _write(tmp_path, "src/cal.py", BREACH)
    _write(tmp_path, "test_cal.py", "from src.cal import grade\n\ndef test_grade():\n    assert grade(95) == 'A'\n")
    _coverage_lcov(tmp_path, "crapper")
    result = _run("crapper", ["--threshold", "10", "--use-existing-coverage", "src/cal.py"], tmp_path)
    assert result.returncode == 2, result.stdout + result.stderr
    assert "CRAP threshold exceeded" in result.stdout + result.stderr


def test_crapper_gate_passes_the_boundary_score(tmp_path):
    _write(tmp_path, "src/one.py", CONFORMING)
    _write(tmp_path, "test_one.py", "from src.one import one\n\ndef test_one():\n    assert one(1) == 1\n")
    _coverage_lcov(tmp_path, "crapper")
    # The worst CRAP score is exactly 1, so a threshold of 1 sits on the
    # boundary: the gate fails only when the score exceeds the threshold.
    result = _run("crapper", ["--threshold", "1", "--use-existing-coverage", "src/one.py"], tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_dryer_gate_passes_a_clean_unit(tmp_path):
    _write(tmp_path, "src/one.py", CONFORMING)
    result = _run("dryer", ["--threshold", "0.8", "--fail-above", "src/one.py"], tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_dryer_gate_fails_a_duplicate_pair(tmp_path):
    body = "def alpha(xs):\n    ys = filter(xs, odd)\n    zs = map(ys, inc)\n    return list(zs)\n"
    _write(tmp_path, "src/left.py", body)
    _write(tmp_path, "src/right.py", body)
    result = _run("dryer", ["--threshold", "0.8", "--fail-above", "--min-nodes", "1", "src"], tmp_path)
    assert result.returncode == 2, result.stdout + result.stderr
    assert "DUPLICATE" in result.stdout


def test_mutator_gate_kills_every_mutant(tmp_path):
    _write(tmp_path, "src/add.py", "def add(a, b):\n    return a + b\n")
    _write(tmp_path, "test_add.py", "from src.add import add\n\ndef test_add():\n    assert add(1, 1) == 2\n")
    _coverage_lcov(tmp_path, "mutator")
    command = f"{REPO_ROOT / 'tools/mutator/.venv/bin/python'} -m pytest -q test_add.py"
    result = _run(
        "mutator",
        ["--use-existing-coverage", "--max-workers", "2", "--test-command", command, "src/add.py"],
        tmp_path,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_mutator_gate_reports_a_survivor(tmp_path):
    _write(
        tmp_path,
        "src/flag.py",
        "def cap(x):\n    if x > 0:\n        return 1\n    return 0\n",
    )
    _write(
        tmp_path,
        "test_flag.py",
        "from src.flag import cap\n\ndef test_cap():\n    assert cap(1) == 1\n",
    )
    _coverage_lcov(tmp_path, "mutator")
    command = f"{REPO_ROOT / 'tools/mutator/.venv/bin/python'} -m pytest -q test_flag.py"
    result = _run(
        "mutator",
        ["--use-existing-coverage", "--max-workers", "2", "--test-command", command, "src/flag.py"],
        tmp_path,
    )
    assert result.returncode == 3, result.stdout + result.stderr
