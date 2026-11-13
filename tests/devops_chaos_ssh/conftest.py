"""Make the chaos_ssh package importable, with the mutation
stand-down: under mutmut the absolute path keeps the import inside
the copy under test. The shared fixtures wire the tutor to a fake
container boundary and a temp area root."""

import sys
from pathlib import Path

import json
import pytest

# absolute(), not resolve(): the mutator symlink overlay must keep
# this path inside the worker tree, so the tests import the mutated
# copy.
REPO_ROOT = Path(__file__).absolute().parents[2]
TUTOR_HOME = REPO_ROOT / "devops" / "chaos" / "ssh" / "tutor"

if str(TUTOR_HOME) not in sys.path:
    sys.path.insert(0, str(TUTOR_HOME))

from chaos_ssh.catalog import Scenario  # noqa: E402


def build_scenario(scenario_id="port-refused", **overrides):
    """One Scenario object built in memory for direct cli tests."""
    body = {
        "id": scenario_id,
        "title": "The ssh daemon is stopped",
        "phase": "transport",
        "fault": "The injection stops the practice sshd.",
        "inject": "environments/inject/port-refused.sh",
        "command": "ssh -F {scratch}/config {target}",
        "signature": "Connection refused",
        "prompts": ["What does the message name as the failure?"],
        "hints": ["Examine the port number.", "Ask what listens there."],
        "reveal": {
            "wrong": "The injection stopped the practice sshd.",
            "fix": "Start the ssh service again.",
        },
        "connection": {
            "target": "practice",
            "user": "practice",
            "port": 2222,
            "identity": True,
            "hostkeyalias": None,
            "arm": None,
            "agent": False,
        },
    }
    body.update(overrides)
    return Scenario(
        id=body["id"],
        title=body["title"],
        phase=body["phase"],
        fault=body["fault"],
        inject=body["inject"],
        command=body["command"],
        signature=body["signature"],
        prompts=body["prompts"],
        hints=body["hints"],
        reveal_wrong=body["reveal"]["wrong"],
        reveal_fix=body["reveal"]["fix"],
        connection=body["connection"],
    )


class FakeEnv:
    """A scripted container boundary that records every call and
    simulates the host tools the tutor invokes."""

    def __init__(self, held_ports=()):
        self.calls = []
        self.held_ports = set(held_ports)
        self.container_runs = False
        self.removals = 0

    def run(self, argv, capture=False):
        argv = list(argv)
        self.calls.append(("run", argv))
        stdout = ""
        if argv[:1] == ["ssh-keygen"]:
            key_path = Path(argv[argv.index("-f") + 1])
            key_path.write_text(
                "fake key body for the sandbox\n", encoding="utf-8"
            )
            key_path.with_suffix(".pub").write_text(
                "ssh-ed25519 AAAA fake\n", encoding="utf-8"
            )
        if argv[:1] == ["ssh-keyscan"]:
            stdout = "[127.0.0.1]:2222 ssh-ed25519 AAAA fake1\n"
        if argv[:1] == ["ssh-agent"]:
            stdout = "echo Agent pid 4242;"
        return {"returncode": 0, "stdout": stdout}

    def up(self, workspace):
        self.calls.append(("up", str(workspace)))
        self.container_runs = True

    def exec_in(self, workspace, script, args=()):
        self.calls.append(("exec", script, list(args)))
        return 0

    def rm_container(self, workspace):
        self.calls.append(("rm",))
        had = self.container_runs
        self.container_runs = False
        self.removals += 1
        return had

    def port_status(self, port):
        return port not in self.held_ports

    def wait_ready(self, port, timeout_s=30):
        self.calls.append(("ready", port))
        return True


@pytest.fixture
def catalog_dir(tmp_path):
    """A temp area root whose catalog holds the scenarios the tests
    address."""
    directory = tmp_path / "catalog"
    directory.mkdir()
    bodies = {
        "port-refused": {},
        "dns-failure": {
            "inject": None,
            "connection": {
                "target": "dns-does-not-resolve.invalid",
                "user": "practice",
                "port": 2222,
                "identity": True,
                "hostkeyalias": None,
                "arm": None,
                "agent": False,
            },
        },
        "wrong-host": {
            "inject": None,
            "connection": {
                "target": "practice",
                "user": "practice",
                "port": 2223,
                "identity": True,
                "hostkeyalias": "decoy",
                "arm": None,
                "agent": False,
            },
        },
        "key-permissions": {
            "inject": None,
            "connection": {
                "target": "practice",
                "user": "practice",
                "port": 2222,
                "identity": True,
                "hostkeyalias": None,
                "arm": {"kind": "key-mode", "mode": "0644"},
                "agent": False,
            },
        },
        "password-disabled": {
            "connection": {
                "target": "practice",
                "user": "practice",
                "port": 2222,
                "identity": False,
                "hostkeyalias": None,
                "arm": None,
                "agent": False,
            },
        },
        "no-agent-forwarding": {
            "connection": {
                "target": "practice",
                "user": "practice",
                "port": 2222,
                "identity": True,
                "hostkeyalias": None,
                "arm": None,
                "agent": True,
            },
        },
    }
    for scenario_id, overrides in bodies.items():
        body = build_scenario(scenario_id, **overrides)
        data = {
            "id": body.id,
            "title": body.title,
            "phase": body.phase,
            "fault": body.fault,
            "inject": body.inject,
            "command": body.command,
            "signature": body.signature,
            "prompts": body.prompts,
            "hints": body.hints,
            "reveal": {"wrong": body.reveal_wrong, "fix": body.reveal_fix},
            "connection": body.connection,
        }
        (directory / f"{scenario_id}.json").write_text(
            json.dumps(data), encoding="utf-8"
        )
    inject_dir = tmp_path / "environments" / "inject" / "_setup"
    inject_dir.mkdir(parents=True)
    for script in (
        "port-refused.sh",
        "password-disabled.sh",
        "wrong-user.sh",
        "no-agent-forwarding.sh",
    ):
        (tmp_path / "environments" / "inject" / script).write_text(
            "#!/bin/bash\n", encoding="utf-8"
        )
    (inject_dir / "install-practice-key.sh").write_text(
        "#!/bin/bash\n", encoding="utf-8"
    )
    return tmp_path


@pytest.fixture
def tutor(catalog_dir, monkeypatch):
    """A tutor wired to the fake boundary and the temp area root."""
    fake = FakeEnv()
    monkeypatch.setattr(cli_module(), "AREA_ROOT", catalog_dir)
    from chaos_ssh import env

    monkeypatch.setattr(env, "up", fake.up)
    monkeypatch.setattr(env, "exec_in", fake.exec_in)
    monkeypatch.setattr(env, "rm_container", fake.rm_container)
    monkeypatch.setattr(env, "port_status", fake.port_status)
    monkeypatch.setattr(env, "wait_ready", fake.wait_ready)
    monkeypatch.setattr(env, "run", fake.run)
    return fake


def cli_module():
    from chaos_ssh import cli

    return cli
