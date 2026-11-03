"""Tests for the hook shim contract.

The tests run the real script as a subprocess the way the harness runs
it: one event on stdin, the project root in the environment, and the
exit code as the verdict.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).absolute().parents[2]
SHIM = REPO_ROOT / ".claude" / "hooks" / "peak-hours-gate.sh"

IN_WINDOW_NOW = "2026-11-03T07:00:00Z"  # 15:00 SGT Tuesday
OUT_WINDOW_NOW = "2026-11-03T11:00:00Z"  # 19:00 SGT Tuesday

TASK_EVENT = '{"tool_name": "Task"}\n'


def _run_shim(shim, event, env_extra=None):
    env = dict(os.environ)
    # A host export of the override or the clock seam must not flip the
    # pinned verdicts.
    env.pop("CLAUDE_PROJECT_DIR", None)
    env.pop("ZAI_PEAK_HOURS_OVERRIDE", None)
    env.pop("PEAK_HOURS_GATE_NOW", None)
    env.update(env_extra or {})
    result = subprocess.run(
        ["bash", str(shim)],
        input=event,
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    return result.returncode, result.stdout, result.stderr


@pytest.mark.skipif(not SHIM.exists(), reason="shim not written yet")
def test_shim_denies_in_window():
    code, _, err = _run_shim(
        SHIM, TASK_EVENT, {"PEAK_HOURS_GATE_NOW": IN_WINDOW_NOW}
    )
    assert code == 2
    assert "ZAI_PEAK_HOURS_OVERRIDE" in err


@pytest.mark.skipif(not SHIM.exists(), reason="shim not written yet")
def test_shim_allows_outside_window_and_stays_silent():
    code, out, err = _run_shim(
        SHIM, TASK_EVENT, {"PEAK_HOURS_GATE_NOW": OUT_WINDOW_NOW}
    )
    assert code == 0
    assert out == ""
    assert err == ""


@pytest.mark.skipif(not SHIM.exists(), reason="shim not written yet")
def test_shim_override_allows_in_window():
    code, _, _ = _run_shim(
        SHIM,
        TASK_EVENT,
        {"PEAK_HOURS_GATE_NOW": IN_WINDOW_NOW, "ZAI_PEAK_HOURS_OVERRIDE": "1"},
    )
    assert code == 0


@pytest.mark.skipif(not SHIM.exists(), reason="shim not written yet")
def test_shim_missing_root_allows_silently(tmp_path):
    moved = tmp_path / "peak-hours-gate.sh"
    shutil.copy(SHIM, moved)
    code, out, err = _run_shim(
        moved, TASK_EVENT, {"PEAK_HOURS_GATE_NOW": IN_WINDOW_NOW}
    )
    assert code == 0
    assert out == ""
    assert err == ""


@pytest.mark.skipif(not SHIM.exists(), reason="shim not written yet")
def test_shim_python3_fallback_runs_the_gate(tmp_path):
    fake = tmp_path / "lab"
    (fake / "tools" / "peak_hours_gate").mkdir(parents=True)
    shutil.copytree(
        REPO_ROOT / "tools" / "peak_hours_gate" / "peak_hours_gate",
        fake / "tools" / "peak_hours_gate" / "peak_hours_gate",
    )
    (fake / ".claude" / "hooks").mkdir(parents=True)
    moved = fake / ".claude" / "hooks" / "peak-hours-gate.sh"
    shutil.copy(SHIM, moved)
    code, _, err = _run_shim(
        moved, TASK_EVENT, {"PEAK_HOURS_GATE_NOW": IN_WINDOW_NOW}
    )
    assert code == 2
    assert "ZAI_PEAK_HOURS_OVERRIDE" in err
