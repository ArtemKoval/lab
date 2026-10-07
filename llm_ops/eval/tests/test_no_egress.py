import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = Path(__file__).resolve().parent / "socket_probe.py"


def probe(**overrides):
    env = {k: v for k, v in os.environ.items() if k != "DEEPEVAL_TELEMETRY_OPT_OUT"}
    env.update(overrides, PYTHONPATH=str(ROOT))
    done = subprocess.run(
        [sys.executable, str(PROBE)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(done.stdout.strip().splitlines()[-1])


def test_a_metric_run_opens_no_connection_by_default():
    report = probe()
    assert report["error"] is None
    assert report["score"] == 0.8
    assert report["targets"] == []


def test_the_probe_sees_telemetry_when_the_user_turns_it_on():
    # This control proves that the probe can see a connection that the default hides.
    report = probe(DEEPEVAL_TELEMETRY_OPT_OUT="NO")
    assert report["targets"] != []
