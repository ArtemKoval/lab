"""Contract tests for the hook shim: a live subprocess run through
.claude/hooks/cc-logging.sh, and the fail-open path."""

import json
import os
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).absolute().parents[2]
SHIM = REPO_ROOT / ".claude" / "hooks" / "cc-logging.sh"


def test_shim_runs_a_live_event(tmp_path):
    log_dir = tmp_path / "repo" / ".cc_logging"
    event = json.dumps({"hook_event_name": "Stop", "session_id": "shim-1"})
    out = subprocess.run(
        [str(SHIM)],
        input=event,
        capture_output=True,
        text=True,
        timeout=30,
        shell=False,
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path / "repo")},
    )
    assert out.returncode == 0
    assert out.stdout == ""
    lines = (log_dir / "shim-1.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1


def test_shim_exits_zero_without_interpreter(tmp_path):
    event = json.dumps({"hook_event_name": "Stop", "session_id": "x"})
    restricted = tmp_path / "bin"
    restricted.mkdir()
    minimal_env = {"PATH": str(restricted), "CLAUDE_PROJECT_DIR": str(tmp_path / "repo")}
    out = subprocess.run(
        [str(SHIM)],
        input=event,
        capture_output=True,
        text=True,
        timeout=30,
        shell=False,
        env=minimal_env,
    )
    assert out.returncode == 0


def test_shim_exists_and_is_executable():
    assert SHIM.is_file()
    assert os.access(SHIM, os.X_OK)
    assert shutil.which("python3") is not None or Path(
        REPO_ROOT, "tools/zai_routing_audit/.venv/bin/python"
    ).is_file()
