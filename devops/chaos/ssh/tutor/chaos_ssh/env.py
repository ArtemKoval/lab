"""The container and host-process boundary of the ssh tutor.

Every subprocess call of the tutor goes through run() or one of the
functions here, so the hermetic suite fakes one seam. The container
commands drive the devcontainer CLI with the house up and exec
pattern; the stop path removes the workspace container with a forced
docker rm.
"""

import socket
import subprocess
import time
from pathlib import Path

DEVCONTAINER_CLI = ("npx", "--yes", "@devcontainers/cli")


class EnvError(Exception):
    """One container or host command fails, with the next action."""

    def __init__(self, message, remediation):
        super().__init__(message)
        self.remediation = remediation


def run(argv, capture=False):
    """Run one host command and return its result mapping."""
    stdout = subprocess.PIPE if capture else subprocess.DEVNULL
    completed = subprocess.run(
        argv, stdout=stdout, stderr=subprocess.PIPE, check=False
    )
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout.decode() if capture else "",
        "stderr": completed.stderr.decode(),
    }


def up(workspace: Path) -> None:
    """Start the workspace container, replacing an existing one."""
    argv = (
        *DEVCONTAINER_CLI,
        "up",
        "--workspace-folder",
        str(workspace),
        "--remove-existing-container",
    )
    result = run(argv)
    if result["returncode"] != 0:
        raise _container_error("the up command failed", result["stderr"])


def exec_in(workspace: Path, script: str, args=()) -> int:
    """Run one bash script inside the workspace container."""
    argv = (
        *DEVCONTAINER_CLI,
        "exec",
        "--workspace-folder",
        str(workspace),
        "--",
        "bash",
        script,
        *args,
    )
    result = run(argv)
    if result["returncode"] != 0:
        raise _container_error(
            f"the script {script} failed inside the container",
            result["stderr"],
        )
    return 0


def rm_container(workspace: Path) -> bool:
    """Remove the workspace container with a forced docker rm."""
    listing = run(
        (
            "docker",
            "ps",
            "-aq",
            "--filter",
            f"label=devcontainer.local_folder={workspace}",
        ),
        capture=True,
    )
    ids = listing["stdout"].split()
    if not ids:
        return False
    removal = run(("docker", "rm", "-f", *ids))
    if removal["returncode"] != 0:
        raise _container_error(
            "the container removal failed", removal["stderr"]
        )
    return True


def port_status(port: int) -> bool:
    """Return True when the host port is free to bind."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def wait_ready(port: int, timeout_s: int = 60) -> bool:
    """Wait until a TCP connect to the host port succeeds."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.settimeout(1)
            if probe.connect_ex(("127.0.0.1", port)) == 0:
                return True
        time.sleep(0.5)
    return False


def _container_error(message: str, stderr: str) -> EnvError:
    remediation = (
        "run the devcontainer command by hand to see the fault, and "
        "check that docker is running and the docker group is active; "
        "the sg docker -c prefix gives the shell the group"
    )
    detail = stderr.strip().splitlines()[-1] if stderr.strip() else ""
    return EnvError(f"{message}: {detail}", remediation)
