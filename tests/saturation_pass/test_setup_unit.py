"""Tests for the saturation-pass setup registry unit."""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_registry_carries_the_saturation_pass_unit():
    registry = json.loads(
        (REPO_ROOT / "tools" / "project_setup" / "registry.json")
        .read_text(encoding="utf-8"))
    unit = next(u for u in registry["units"] if u["id"] == "saturation-pass")
    assert unit["kind"] == "dependency-file"
    assert unit["check"] == [
        "python3", "tools/saturation_pass/saturation_pass.py", "--help"]
    assert "no install needed" in unit["install"]


def test_the_cli_help_exit_is_0():
    import subprocess

    proc = subprocess.run(
        ["tools/zai_routing_audit/.venv/bin/python",
         "tools/saturation_pass/saturation_pass.py", "--help"],
        capture_output=True, text=True, check=False, cwd=REPO_ROOT)
    assert proc.returncode == 0
    assert "saturation_pass" in proc.stdout
