"""The scratch ssh state of one scenario.

The scratch directory stands in for the learner's ~/.ssh for one
armed scenario. Every path the tutor hands to the ssh client lives
inside this directory, and the tutor never touches the real ~/.ssh.
"""

import os
import shutil
from pathlib import Path

from chaos_ssh import env

GLOBAL_HOSTS_NAME = "global_known_hosts"
HOSTS_NAME = "known_hosts"
KEY_NAME = "id_ed25519"
CONFIG_NAME = "config"
POSITION_NAME = "position"
AGENT_SOCK_NAME = "agent.sock"
AGENT_PID_NAME = "agent.pid"


class Scratch:
    """One scenario scratch directory with its ssh state."""

    def __init__(self, area_root: Path, scenario_id: str):
        self.root = area_root / ".state" / scenario_id
        self.scenario_id = scenario_id

    @property
    def config(self) -> Path:
        return self.root / CONFIG_NAME

    @property
    def key(self) -> Path:
        return self.root / KEY_NAME

    @property
    def agent_sock(self) -> Path:
        return self.root / AGENT_SOCK_NAME

    @property
    def agent_pid(self) -> Path:
        return self.root / AGENT_PID_NAME

    def ensure(self) -> None:
        """Create the directory and the empty global hosts file."""
        self.root.mkdir(parents=True, exist_ok=True)
        global_hosts = self.root / GLOBAL_HOSTS_NAME
        global_hosts.touch(exist_ok=True)

    def generate_key(self) -> None:
        """Create the practice keypair inside the scratch directory."""
        result = env.run(
            (
                "ssh-keygen",
                "-t",
                "ed25519",
                "-N",
                "",
                "-q",
                "-f",
                str(self.key),
            ),
            capture=True,
        )
        if result["returncode"] != 0:
            raise env.EnvError(
                "the practice key generation failed",
                "examine the ssh-keygen output, and remove a stale "
                "scratch state with the stop command",
            )
        os.chmod(self.key, 0o600)

    def write_config(
        self,
        *,
        target: str,
        port: int,
        user: str,
        identity: bool,
        hostkeyalias: str | None,
    ) -> None:
        """Render the scratch ssh config with the five bindings."""
        lines = [
            "Host *",
            f"    UserKnownHostsFile {self.root / HOSTS_NAME}",
            f"    GlobalKnownHostsFile {self.root / GLOBAL_HOSTS_NAME}",
            "    IdentitiesOnly yes",
            "    IdentityAgent none",
            f"Host {target}",
            "    HostName 127.0.0.1",
            f"    Port {port}",
            f"    User {user}",
        ]
        if identity:
            lines.append(f"    IdentityFile {self.key}")
        if hostkeyalias:
            lines.append(f"    HostKeyAlias {hostkeyalias}")
        self.config.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def seed_known_hosts(self, port: int, alias: str | None = None) -> None:
        """Seed the scratch known_hosts from the running container."""
        result = env.run(
            ("ssh-keyscan", "-p", str(port), "-t", "ed25519", "127.0.0.1"),
            capture=True,
        )
        if result["returncode"] != 0 or not result["stdout"].strip():
            raise env.EnvError(
                "the host key scan failed",
                "examine the container state, and run the start "
                "command again after the stop command",
            )
        lines = []
        for line in result["stdout"].splitlines():
            fields = line.split()
            if len(fields) < 3 or fields[0].startswith("#"):
                continue
            name = alias or f"[127.0.0.1]:{port}"
            lines.append(" ".join([name, *fields[1:]]))
        hosts = self.root / HOSTS_NAME
        with hosts.open("a", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")

    def apply_arm(self, arm: dict | None) -> None:
        """Apply the host-side fault of the scenario, when it has one."""
        if not arm:
            return
        kind = arm.get("kind")
        if kind == "key-mode":
            mode = int(str(arm.get("mode", "0644")), 8)
            os.chmod(self.key, mode)
            return
        raise env.EnvError(
            f"the arm kind {kind} is unknown",
            "examine the catalog file of the scenario, and repair the "
            "arm block",
        )

    def reset_position(self) -> None:
        """Reset the hint position of the scenario."""
        (self.root / POSITION_NAME).write_text("0", encoding="utf-8")

    def next_hint(self, hints: list) -> str:
        """Print the next hint, and hold the last one at the end."""
        position_file = self.root / POSITION_NAME
        position = 0
        if position_file.exists():
            position = int(position_file.read_text(encoding="utf-8") or "0")
        index = min(position, len(hints) - 1)
        following = min(position + 1, len(hints) - 1)
        self.root.mkdir(parents=True, exist_ok=True)
        position_file.write_text(str(following), encoding="utf-8")
        return hints[index]

    def agent_start(self) -> None:
        """Start a scratch ssh agent bound to the scratch socket."""
        result = env.run(
            ("ssh-agent", "-a", str(self.agent_sock)),
            capture=True,
        )
        if result["returncode"] != 0:
            raise env.EnvError(
                "the scratch agent failed to start",
                "examine the ssh-agent output, and remove a stale "
                "scratch state with the stop command",
            )
        pid = ""
        for line in result["stdout"].splitlines():
            if line.startswith("echo Agent pid"):
                pid = line.split()[-1].rstrip(";")
        self.agent_pid.write_text(pid, encoding="utf-8")

    def agent_stop(self) -> None:
        """End the scratch agent when its pid file stands."""
        if not self.agent_pid.exists():
            return
        pid = self.agent_pid.read_text(encoding="utf-8").strip()
        if pid:
            env.run(("kill", pid))
        self.agent_pid.unlink(missing_ok=True)

    def cleanup(self) -> None:
        """Remove the whole scratch state, agent included."""
        self.agent_stop()
        shutil.rmtree(self.root, ignore_errors=True)
