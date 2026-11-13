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


def test_unready_container_exits_2(capsys, catalog_dir, tutor, monkeypatch):
    def not_ready(port, timeout_s=30):
        return False

    monkeypatch.setattr(cli.env, "wait_ready", not_ready)
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


def test_json_flag_after_the_subcommand(capsys, tutor):
    assert cli.main(["list", "--json"]) == 0
    rows = json.loads(capsys.readouterr().out)
    assert rows[0]["id"]


def test_read_only_commands_leave_the_boundary_untouched(
    capsys, catalog_dir, tutor
):
    cli.main(["list"])
    cli.main(["hint", "port-refused"])
    cli.main(["reveal", "port-refused"])
    cli.main(["stop", "port-refused"])
    kinds = [call[0] for call in tutor.calls]
    assert "up" not in kinds
    assert "exec" not in kinds


def test_start_resets_a_stale_scratch_state(capsys, catalog_dir, tutor):
    scratch_dir = catalog_dir / ".state" / "port-refused"
    scratch_dir.mkdir(parents=True)
    (scratch_dir / "position").write_text("not-a-number", encoding="utf-8")
    (scratch_dir / "id_ed25519").write_text("stale", encoding="utf-8")
    assert cli.main(["start", "port-refused"]) == 0
    assert (scratch_dir / "position").read_text(encoding="utf-8") == "0"


def test_corrupt_position_reads_as_the_first_hint(catalog_dir):
    from chaos_ssh.scratch import Scratch

    scratch = Scratch(catalog_dir, "port-refused")
    scratch.ensure()
    (scratch.root / "position").write_text(
        "not-a-number", encoding="utf-8"
    )
    assert scratch.next_hint(["first", "second"]) == "first"


def test_command_placeholder_validation(tmp_path):
    body = {
        "id": "bad-command",
        "title": "t",
        "phase": "transport",
        "fault": "f",
        "inject": None,
        "command": "ssh -p {port}",
        "signature": "s",
        "prompts": ["p"],
        "hints": ["h"],
        "reveal": {"wrong": "w", "fix": "f"},
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
    (tmp_path / "catalog").mkdir()
    (tmp_path / "catalog" / "bad-command.json").write_text(
        json.dumps(body), encoding="utf-8"
    )
    from chaos_ssh.catalog import CatalogError, load_catalog

    with pytest.raises(CatalogError) as exc:
        load_catalog(tmp_path / "catalog")
    assert "placeholder" in str(exc.value)


def test_inject_path_validation(tmp_path):
    body = {
        "id": "missing-script",
        "title": "t",
        "phase": "transport",
        "fault": "f",
        "inject": "environments/inject/no-such.sh",
        "command": "ssh -F {scratch}/config {target}",
        "signature": "s",
        "prompts": ["p"],
        "hints": ["h"],
        "reveal": {"wrong": "w", "fix": "f"},
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
    (tmp_path / "catalog").mkdir()
    (tmp_path / "catalog" / "missing-script.json").write_text(
        json.dumps(body), encoding="utf-8"
    )
    (tmp_path / "environments").mkdir()
    from chaos_ssh.catalog import CatalogError, load_catalog

    with pytest.raises(CatalogError) as exc:
        load_catalog(tmp_path / "catalog")
    assert "no-such.sh" in str(exc.value)


def test_ensure_is_idempotent(catalog_dir):
    from chaos_ssh.scratch import Scratch

    scratch = Scratch(catalog_dir, "port-refused")
    scratch.ensure()
    scratch.ensure()
    assert (scratch.root / "global_known_hosts").exists()


def test_keyscan_empty_output_raises(capsys, catalog_dir, tutor, monkeypatch):
    original_run = cli.env.run

    def empty_run(argv, capture=False):
        argv = list(argv)
        if argv[:1] == ["ssh-keyscan"]:
            return {"returncode": 0, "stdout": "", "stderr": ""}
        return original_run(argv, capture=capture)

    monkeypatch.setattr(cli.env, "run", empty_run)
    with pytest.raises(SystemExit) as exc:
        cli.main(["start", "port-refused"])
    assert exc.value.code == 2
    assert "scan" in capsys.readouterr().err


def test_keyscan_keeps_three_field_lines_and_names_the_host(
    catalog_dir, tutor, monkeypatch
):
    original_run = cli.env.run

    def noisy_run(argv, capture=False):
        argv = list(argv)
        if argv[:1] == ["ssh-keyscan"]:
            return {
                "returncode": 0,
                "stdout": (
                    "# a comment\nshort\n"
                    "127.0.0.1 ssh-ed25519 AAAAbase\n"
                    "[127.0.0.1]:2222 ssh-ed25519 AAAA ok\n"
                    "# a longer comment\n"
                ),
                "stderr": "",
            }
        return original_run(argv, capture=capture)

    monkeypatch.setattr(cli.env, "run", noisy_run)
    assert cli.main(["start", "port-refused"]) == 0
    hosts = (
        catalog_dir / ".state" / "port-refused" / "known_hosts"
    ).read_text(encoding="utf-8")
    assert "# a comment" not in hosts
    assert "short" not in hosts
    assert "[127.0.0.1]:2222 ssh-ed25519 AAAA ok" in hosts
    assert "127.0.0.1 ssh-ed25519 AAAAbase" not in hosts
    assert "[127.0.0.1]:2222 ssh-ed25519 AAAAbase" in hosts
    assert "a longer comment" not in hosts
    assert "#" not in hosts


def test_hint_positions_step_and_hold(capsys, tutor):
    cli.main(["start", "port-refused"])
    position = catalog_dir_path() / ".state" / "port-refused" / "position"
    codes = []
    written = []
    for _ in range(4):
        cli.main(["hint", "port-refused"])
        written.append(position.read_text(encoding="utf-8"))
    assert written == ["1", "1", "1", "1"]


def catalog_dir_path():
    from chaos_ssh import cli as cli_module

    return cli_module.AREA_ROOT


def test_missing_subcommand_exits_2():
    with pytest.raises(SystemExit) as exc:
        cli.main([])
    assert exc.value.code == 2


def test_next_hint_walks_three_hints_and_holds(catalog_dir):
    from chaos_ssh.scratch import Scratch

    scratch = Scratch(catalog_dir, "port-refused")
    scratch.ensure()
    hints = ["first", "second", "third"]
    seen = [scratch.next_hint(hints) for _ in range(4)]
    assert seen == ["first", "second", "third", "third"]
    position = (scratch.root / "position").read_text(encoding="utf-8")
    assert position == "2"


def test_require_keys_names_the_section(tmp_path):
    from chaos_ssh.catalog import CatalogError, load_catalog

    base = {
        "id": "x",
        "title": "t",
        "phase": "transport",
        "fault": "f",
        "inject": None,
        "command": "ssh -F {scratch}/config {target}",
        "signature": "s",
        "prompts": ["p"],
        "hints": ["h"],
        "reveal": {"wrong": "w", "fix": "f"},
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
    (tmp_path / "catalog").mkdir()
    body = dict(base)
    del body["signature"]
    (tmp_path / "catalog" / "x.json").write_text(
        json.dumps(body), encoding="utf-8"
    )
    with pytest.raises(CatalogError) as exc:
        load_catalog(tmp_path / "catalog")
    assert "the file misses" in str(exc.value)

    body = dict(base)
    body["reveal"] = {"wrong": "w"}
    (tmp_path / "catalog" / "x.json").write_text(
        json.dumps(body), encoding="utf-8"
    )
    with pytest.raises(CatalogError) as exc:
        load_catalog(tmp_path / "catalog")
    assert "the reveal misses" in str(exc.value)

    body = dict(base)
    del body["connection"]["port"]
    (tmp_path / "catalog" / "x.json").write_text(
        json.dumps(body), encoding="utf-8"
    )
    with pytest.raises(CatalogError) as exc:
        load_catalog(tmp_path / "catalog")
    assert "the connection misses" in str(exc.value)
