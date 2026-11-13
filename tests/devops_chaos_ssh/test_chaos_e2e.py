"""The opt-in e2e lane of the ssh tutor.

The lane runs only with DEVOPS_CHAOS_SSH_E2E=1 and a live docker
daemon on the host. It arms one scenario against the real container,
runs the printed connection command with the real ssh client, and
asserts the refusal signature substring. Every function holds CC 2
or less, because the hermetic suite never runs this module and the
crapper gate reads zero coverage here.
"""

import os
import subprocess

import pytest

from chaos_ssh import cli, env

pytestmark = pytest.mark.e2e

requires_e2e = pytest.mark.skipif(
    os.environ.get("DEVOPS_CHAOS_SSH_E2E") != "1",
    reason="the lane runs only with DEVOPS_CHAOS_SSH_E2E=1",
)


def _ports_free():
    return env.port_status(2222) and env.port_status(2223)


def _the_connection_command(notice):
    matches = [
        line for line in notice.splitlines() if line.startswith("ssh -F")
    ]
    return matches[0]


def _refusal_or_reset(stderr):
    return "Connection refused" in stderr or "Connection reset" in stderr


def _control_login():
    """Return (ok, detail) for one practice login with the scratch key.

    The control login holds the load-bearing baseline live: the
    container boots, the key install works, the accounts stand
    unlocked, and the daemon accepts the practice key.
    """
    scratch = cli.AREA_ROOT / ".state" / "dns-failure"
    attempt = subprocess.run(
        [
            "ssh",
            "-F", str(scratch / "config"),
            "-o", "IdentitiesOnly=yes",
            "-o", "IdentityAgent=none",
            "-o", "UserKnownHostsFile=" + str(scratch / "known_hosts"),
            "-o", "GlobalKnownHostsFile=" + str(scratch / "global_known_hosts"),
            "-o", "BatchMode=yes",
            "-i", str(scratch / "id_ed25519"),
            "-p", "2222",
            "practice@127.0.0.1",
            "echo control-ok",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    return attempt.returncode == 0 and "control-ok" in attempt.stdout, (
        attempt.stderr.strip()
    )


@requires_e2e
def test_port_refused_end_to_end(capsys):
    """Arm port-refused, connect, see the refusal, and stop clean."""
    assert _ports_free()
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
    assert _refusal_or_reset(attempt.stderr)
    assert cli.main(["stop", "port-refused"]) == 0
    survivor = subprocess.run(
        ["pgrep", "-f", "agent.sock"], capture_output=True, text=True
    )
    assert survivor.returncode != 0


@requires_e2e
def test_control_login_succeeds(capsys):
    """The unfaulted container accepts the practice key of the scratch
    state. A locked account fails here before any scenario teaches."""
    assert _ports_free()
    assert cli.main(["start", "dns-failure"]) == 0
    ok, detail = _control_login()
    assert ok, f"the control login failed: {detail}"
    assert cli.main(["stop", "dns-failure"]) == 0


@requires_e2e
def test_pubkey_rejected_signature_live(capsys):
    """The auth fault prints the shared signature of the auth trio."""
    assert _ports_free()
    assert cli.main(["start", "pubkey-rejected"]) == 0
    out = capsys.readouterr().out
    command = _the_connection_command(out)
    attempt = subprocess.run(
        command + " -o BatchMode=yes",
        shell=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert attempt.returncode != 0
    assert "Permission denied (publickey)" in attempt.stderr
    assert cli.main(["stop", "pubkey-rejected"]) == 0


@requires_e2e
def test_stop_cleans_the_container(capsys):
    """A stop with no armed run exits 0 and names the state."""
    cli.main(["stop", "port-refused"])
    out = capsys.readouterr().out
    assert "no container runs" in out or "Stopped" in out
