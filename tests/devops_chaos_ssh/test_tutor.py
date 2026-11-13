"""The tutor behavior: the five subcommands, the exit contract, the
arm order, and the scratch safety rules, over a faked container
boundary."""

import json

import pytest

from chaos_ssh import cli

def run_cli(capsys, *argv):
    """Run one cli invocation and return the exit code."""
    return cli.main(list(argv))


def test_list_prints_one_row_per_scenario(capsys, tutor):
    code = run_cli(capsys, "list")
    out = capsys.readouterr().out
    assert code == 0
    assert "port-refused" in out
    assert "transport" in out


def test_list_json_rows_carry_id_phase_title(capsys, tutor):
    code = run_cli(capsys, "--json", "list")
    rows = json.loads(capsys.readouterr().out)
    assert code == 0
    ids = [row["id"] for row in rows]
    assert ids == sorted(ids)
    assert set(rows[0]) == {"id", "phase", "title"}


def test_start_arms_with_remove_before_ports_and_up(capsys, tutor):
    code = run_cli(capsys, "start", "port-refused")
    assert code == 0
    kinds = [call[0] for call in tutor.calls]
    assert kinds.index("rm") < kinds.index("up")
    assert kinds.index("up") < kinds.index("ready")
    execs = [call for call in tutor.calls if call[0] == "exec"]
    assert any("install-practice-key.sh" in call[1] for call in execs)
    assert any("port-refused.sh" in call[1] for call in execs)


def test_start_prints_command_template_and_first_prompt(capsys, tutor):
    run_cli(capsys, "start", "port-refused")
    out = capsys.readouterr().out
    assert "ssh -F" in out
    assert "What does the message name as the failure?" in out


def test_start_unknown_id_exits_2_with_valid_ids(capsys, tutor):
    with pytest.raises(SystemExit) as exc:
        run_cli(capsys, "start", "no-such")
    assert exc.value.code == 2
    out = capsys.readouterr().err
    assert "port-refused" in out


def test_start_foreign_port_holder_exits_2(capsys, tutor):
    tutor.held_ports = {2222}
    with pytest.raises(SystemExit) as exc:
        run_cli(capsys, "start", "port-refused")
    assert exc.value.code == 2
    out = capsys.readouterr().err
    assert "2222" in out
    assert "override" in out


def test_start_without_injection_skips_inject_exec(capsys, tutor):
    run_cli(capsys, "start", "dns-failure")
    execs = [call for call in tutor.calls if call[0] == "exec"]
    assert not any(
        "inject" in call[1] and "_setup" not in call[1] for call in execs
    )


def test_start_seeds_known_hosts_before_injection(capsys, tutor):
    run_cli(capsys, "start", "port-refused")
    runs = [call for call in tutor.calls if call[0] == "run"]
    execs = [call for call in tutor.calls if call[0] == "exec"]
    scan_index = next(
        i
        for i, call in enumerate(tutor.calls)
        if call[0] == "run" and call[1][:1] == ["ssh-keyscan"]
    )
    inject_index = next(
        i
        for i, call in enumerate(tutor.calls)
        if call[0] == "exec" and "inject" in call[1] and "_setup" not in call[1]
    )
    assert scan_index < inject_index


def test_start_writes_config_with_the_five_bindings(capsys, tutor):
    run_cli(capsys, "start", "port-refused")
    scratch = cli.AREA_ROOT / ".state" / "port-refused"
    config = (scratch / "config").read_text(encoding="utf-8")
    assert "UserKnownHostsFile" in config
    assert "GlobalKnownHostsFile" in config
    assert "IdentitiesOnly yes" in config
    assert "IdentityAgent none" in config
    assert "IdentityFile" in config


def test_start_wrong_host_redirects_to_the_decoy_alias(capsys, tutor):
    run_cli(capsys, "start", "wrong-host")
    config = (cli.AREA_ROOT / ".state" / "wrong-host" / "config").read_text(
        encoding="utf-8"
    )
    assert "Port 2223" in config
    assert "HostKeyAlias decoy" in config


def test_start_password_disabled_omits_the_identity(capsys, tutor):
    run_cli(capsys, "start", "password-disabled")
    config = (
        cli.AREA_ROOT / ".state" / "password-disabled" / "config"
    ).read_text(encoding="utf-8")
    assert "IdentityFile" not in config


def test_start_key_permissions_arms_the_host_mode(capsys, tutor):
    run_cli(capsys, "start", "key-permissions")
    key = cli.AREA_ROOT / ".state" / "key-permissions" / "id_ed25519"
    assert (key.stat().st_mode & 0o777) == 0o644


def test_start_agent_composes_the_socket_prefix(capsys, tutor):
    run_cli(capsys, "start", "no-agent-forwarding")
    out = capsys.readouterr().out
    scratch = cli.AREA_ROOT / ".state" / "no-agent-forwarding"
    assert f"SSH_AUTH_SOCK={scratch / 'agent.sock'}" in out
    pid_file = scratch / "agent.pid"
    assert pid_file.exists()


def test_start_json_output_carries_the_command(capsys, tutor):
    run_cli(capsys, "--json", "start", "port-refused")
    data = json.loads(capsys.readouterr().out)
    assert data["id"] == "port-refused"
    assert "ssh -F" in data["command"]
    assert data["armed"] is True


def test_hint_sequence_then_last_repeats(capsys, tutor):
    run_cli(capsys, "start", "port-refused")
    code_one = run_cli(capsys, "hint", "port-refused")
    out_one = capsys.readouterr().out
    code_two = run_cli(capsys, "hint", "port-refused")
    out_two = capsys.readouterr().out
    code_three = run_cli(capsys, "hint", "port-refused")
    out_three = capsys.readouterr().out
    code_four = run_cli(capsys, "hint", "port-refused")
    out_four = capsys.readouterr().out
    assert code_one == code_two == code_three == code_four == 0
    assert "Examine the port number." in out_one
    assert "Ask what listens there." in out_two
    assert "Ask what listens there." in out_three
    assert out_three == out_four


def test_hint_resets_after_start(capsys, tutor):
    run_cli(capsys, "hint", "port-refused")
    run_cli(capsys, "hint", "port-refused")
    run_cli(capsys, "start", "port-refused")
    code = run_cli(capsys, "hint", "port-refused")
    out = capsys.readouterr().out
    assert code == 0
    assert "Examine the port number." in out


def test_hint_unknown_id_exits_2(capsys, tutor):
    with pytest.raises(SystemExit) as exc:
        run_cli(capsys, "hint", "no-such")
    assert exc.value.code == 2
    assert "port-refused" in capsys.readouterr().err


def test_reveal_prints_fault_signature_and_fix(capsys, tutor):
    code = run_cli(capsys, "reveal", "port-refused")
    out = capsys.readouterr().out
    assert code == 0
    assert "The injection stopped the practice sshd." in out
    assert "Connection refused" in out
    assert "Start the ssh service again." in out


def test_reveal_unknown_id_exits_2(capsys, tutor):
    with pytest.raises(SystemExit) as exc:
        run_cli(capsys, "reveal", "no-such")
    assert exc.value.code == 2


def test_stop_removes_container_and_scratch_and_agent(capsys, tutor):
    run_cli(capsys, "start", "no-agent-forwarding")
    pid = cli.AREA_ROOT / ".state" / "no-agent-forwarding" / "agent.pid"
    assert pid.exists()
    code = run_cli(capsys, "stop", "no-agent-forwarding")
    out = capsys.readouterr().out
    assert code == 0
    assert tutor.removals >= 1
    assert not (cli.AREA_ROOT / ".state" / "no-agent-forwarding").exists()
    assert "stop" in out


def test_stop_second_time_exits_0_with_no_container_message(capsys, tutor):
    run_cli(capsys, "stop", "port-refused")
    code = run_cli(capsys, "stop", "port-refused")
    out = capsys.readouterr().out
    assert code == 0
    assert "no container runs" in out


def test_stop_unknown_id_exits_2(capsys, tutor):
    with pytest.raises(SystemExit) as exc:
        run_cli(capsys, "stop", "no-such")
    assert exc.value.code == 2
    assert "port-refused" in capsys.readouterr().err
