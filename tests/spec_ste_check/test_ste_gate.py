"""The enforcement gate: the real spec corpus must scan clean of errors."""

import json
from pathlib import Path

from spec_ste_check import cli

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_gate_scope_scans_clean_of_errors(capsys):
    code = cli.main(["--json", "--repo-root", str(REPO_ROOT)])
    data = json.loads(capsys.readouterr().out)
    errors = [v for v in data["violations"] if v["severity"] == "error"]
    assert code == 0, "\n".join(
        f"{v['file']}:{v['line']}: {v['rule']}: {v['text'][:70]}" for v in errors
    )
