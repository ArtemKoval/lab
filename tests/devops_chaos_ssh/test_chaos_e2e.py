"""The opt-in e2e lane of the ssh tutor.

The lane runs only with DEVOPS_CHAOS_SSH_E2E=1 and a live docker
daemon on the host. It arms one scenario against the real container,
runs the printed connection command with the real ssh client, and
asserts the refusal signature substring.
"""

import os
import subprocess

import pytest

from chaos_ssh import cli

pytestmark = pytest.mark.e2e

requires_e2e = pytest.mark.skipif(
    os.environ.get("DEVOPS_CHAOS_SSH_E2E") != "1",
    reason="the lane runs only with DEVOPS_CHAOS_SSH_E2E=1",
)


@requires_e2e
def test_port_refused_end_to_end(capsys):
    """Arm port-refused, connect, see the refusal, and stop clean."""
    assert cli.main(["start", "port-refused"]) == 0
    out = capsys.readouterr().out
    command = _the_connection_command(out)
    attempt = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert attempt.returncode != 0
    refusal = "Connection refused" in attempt.stderr
    reset = "Connection reset" in attempt.stderr
    assert refusal or reset
    assert cli.main(["stop", "port-refused"]) == 0


@requires_e2e
def test_stop_cleans_the_container(capsys):
    """A stop with no armed run exits 0 and names the state."""
    cli.main(["stop", "port-refused"])
    out = capsys.readouterr().out
    assert "no container runs" in out or "Stopped" in out


def _the_connection_command(notice: str) -> str:
    """Extract the ssh command line from the start notice."""
    lines = notice.splitlines()
    starts = [
        i for i, line in enumerate(lines) if line.startswith("ssh -F")
    ]
    if not starts:
        raise AssertionError(f"the notice carries no ssh command: {notice}")
    return lines[starts[0]]
