"""The failure branches of the tutor: env faults, arm faults, and
the json output paths."""

import json

import pytest

from chaos_ssh import cli
from chaos_ssh.catalog import CatalogError, load_catalog
from chaos_ssh.scratch import Scratch


def test_unreadable_catalog_file_raises(tmp_path):
    (tmp_path / "bad.json").mkdir()
    with pytest.raises(CatalogError) as exc:
        load_catalog(tmp_path)
    assert "bad.json" in str(exc.value)


def test_generate_key_failure_raises_with_remediation(
    capsys, catalog_dir, tutor, monkeypatch
):
    tutor.results = {"ssh-keygen": (1, "")}
    original_run = cli.env.run

    def failing_run(argv, capture=False):
        argv = list(argv)
        if argv[:1] == ["ssh-keygen"]:
            return {"returncode": 1, "stdout": "", "stderr": "boom"}
        return original_run(argv, capture=capture)

    monkeypatch.setattr(cli.env, "run", failing_run)
    with pytest.raises(SystemExit) as exc:
        cli.main(["start", "port-refused"])
    assert exc.value.code == 2
    assert "ssh-keygen" in capsys.readouterr().err


def test_keyscan_failure_raises_with_remediation(
    capsys, catalog_dir, tutor, monkeypatch
):
    original_run = cli.env.run

    def failing_run(argv, capture=False):
        argv = list(argv)
        if argv[:1] == ["ssh-keyscan"]:
            return {"returncode": 1, "stdout": "", "stderr": "boom"}
        return original_run(argv, capture=capture)

    monkeypatch.setattr(cli.env, "run", failing_run)
    with pytest.raises(SystemExit) as exc:
        cli.main(["start", "port-refused"])
    assert exc.value.code == 2
    assert "scan" in capsys.readouterr().err


def test_keyscan_filters_comment_and_short_lines(
    catalog_dir, tutor, monkeypatch
):
    original_run = cli.env.run

    def noisy_run(argv, capture=False):
        argv = list(argv)
        if argv[:1] == ["ssh-keyscan"]:
            return {
                "returncode": 0,
                "stdout": "# a comment\nshort\n[127.0.0.1]:2222 ssh-ed25519 AAAA ok\n",
                "stderr": "",
            }
        return original_run(argv, capture=capture)

    monkeypatch.setattr(cli.env, "run", noisy_run)
    assert cli.main(["start", "port-refused"]) == 0
    hosts = (cli.AREA_ROOT / ".state" / "port-refused" / "known_hosts").read_text(
        encoding="utf-8"
    )
    assert "# a comment" not in hosts
    assert "short" not in hosts
    assert "AAAA ok" in hosts


def test_unknown_arm_kind_raises_with_remediation(
    capsys, catalog_dir, tutor, monkeypatch
):
    original_require = cli._require

    def armed_require(scenario_id, table):
        scenario = original_require(scenario_id, table)
        scenario.connection["arm"] = {"kind": "no-such-kind"}
        return scenario

    monkeypatch.setattr(cli, "_require", armed_require)
    with pytest.raises(SystemExit) as exc:
        cli.main(["start", "port-refused"])
    assert exc.value.code == 2
    assert "no-such-kind" in capsys.readouterr().err


def test_agent_start_failure_raises(capsys, catalog_dir, tutor, monkeypatch):
    original_run = cli.env.run

    def failing_run(argv, capture=False):
        argv = list(argv)
        if argv[:1] == ["ssh-agent"]:
            return {"returncode": 1, "stdout": "", "stderr": "boom"}
        return original_run(argv, capture=capture)

    monkeypatch.setattr(cli.env, "run", failing_run)
    with pytest.raises(SystemExit) as exc:
        cli.main(["start", "no-agent-forwarding"])
    assert exc.value.code == 2
    assert "agent" in capsys.readouterr().err


def test_unready_container_exits_2(capsys, catalog_dir, tutor):
    def not_ready(port, timeout_s=30):
        return False

    cli.env.wait_ready = not_ready
    with pytest.raises(SystemExit) as exc:
        cli.main(["start", "port-refused"])
    assert exc.value.code == 2
    assert "did not answer" in capsys.readouterr().err


def test_corrupt_catalog_fails_the_run(capsys, catalog_dir, tutor, monkeypatch):
    (catalog_dir / "catalog" / "broken.json").write_text(
        "{nope", encoding="utf-8"
    )
    with pytest.raises(SystemExit) as exc:
        cli.main(["list"])
    assert exc.value.code == 2
    assert "broken.json" in capsys.readouterr().err


def test_hint_json_output(capsys, tutor):
    cli.main(["--json", "hint", "port-refused"])
    data = json.loads(capsys.readouterr().out)
    assert data["id"] == "port-refused"
    assert "Examine the port number." in data["hint"]


def test_reveal_json_output(capsys, tutor):
    cli.main(["--json", "reveal", "port-refused"])
    data = json.loads(capsys.readouterr().out)
    assert data["signature"] == "Connection refused"
    assert data["wrong"] and data["fix"]


def test_stop_json_output(capsys, tutor):
    cli.main(["--json", "stop", "port-refused"])
    data = json.loads(capsys.readouterr().out)
    assert data == {"id": "port-refused", "removed": False}


def test_scratch_cleanup_without_agent_pid(catalog_dir, tutor):
    scratch = Scratch(catalog_dir, "port-refused")
    scratch.ensure()
    scratch.cleanup()
    assert not (catalog_dir / ".state" / "port-refused").exists()


def test_container_script_rejects_paths_outside_the_inject_dir(
    catalog_dir, tutor
):
    from chaos_ssh.cli import _container_script
    from chaos_ssh.env import EnvError

    with pytest.raises(EnvError):
        _container_script("environments/other/x.sh")
    assert (
        _container_script("environments/inject/deep/x.sh")
        == "/opt/chaos/inject/deep/x.sh"
    )


def test_agent_pid_parse_takes_both_loop_branches(
    catalog_dir, tutor, monkeypatch
):
    original_run = cli.env.run

    def two_line_run(argv, capture=False):
        argv = list(argv)
        if argv[:1] == ["ssh-agent"]:
            return {
                "returncode": 0,
                "stdout": (
                    "SSH_AUTH_SOCK=/tmp/agent.sock; export SSH_AUTH_SOCK;\n"
                    "echo Agent pid 4242;"
                ),
                "stderr": "",
            }
        return original_run(argv, capture=capture)

    monkeypatch.setattr(cli.env, "run", two_line_run)
    cli.main(["start", "no-agent-forwarding"])
    pid = cli.AREA_ROOT / ".state" / "no-agent-forwarding" / "agent.pid"
    assert pid.read_text(encoding="utf-8") == "4242"


def test_agent_stop_with_empty_pid_skips_the_kill(
    catalog_dir, tutor, monkeypatch
):
    killed = []
    original_run = cli.env.run

    def recording_run(argv, capture=False):
        argv = list(argv)
        if argv[:1] == ["kill"]:
            killed.append(list(argv))
        return original_run(argv, capture=capture)

    monkeypatch.setattr(cli.env, "run", recording_run)
    scratch = Scratch(catalog_dir, "port-refused")
    scratch.ensure()
    scratch.agent_pid.write_text("", encoding="utf-8")
    scratch.agent_stop()
    assert killed == []
    assert not scratch.agent_pid.exists()


def test_module_entry_runs_the_cli(monkeypatch):
    import runpy
    import sys

    from chaos_ssh import cli as cli_module

    calls = []

    def fake_main(argv=None):
        calls.append(list(sys.argv))
        return 0

    monkeypatch.setattr(cli_module, "main", fake_main)
    monkeypatch.setattr("sys.argv", ["chaos_ssh", "list"])
    with pytest.raises(SystemExit) as exc:
        runpy.run_module("chaos_ssh", run_name="__main__", alter_sys=True)
    assert exc.value.code == 0
    assert calls == [calls[0]]
    assert calls[0][1:] == ["list"]
