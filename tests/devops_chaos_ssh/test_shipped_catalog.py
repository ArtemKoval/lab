"""The shipped catalog: the arming data of every scenario must
match the fault the catalog promises. These invariants hold the
real files on disk, not fixtures."""

from pathlib import Path

import pytest

from chaos_ssh.catalog import load_catalog

AREA_ROOT = Path(__file__).absolute().parents[2] / "devops" / "chaos" / "ssh"
CATALOG_DIR = AREA_ROOT / "catalog"


@pytest.fixture(scope="module")
def scenarios():
    return {s.id: s for s in load_catalog(CATALOG_DIR)}


def test_the_catalog_holds_the_thirteen_scenarios(scenarios):
    assert sorted(scenarios) == [
        "broken-shell",
        "dns-failure",
        "firewall-drop",
        "host-key-changed",
        "kex-mismatch",
        "key-permissions",
        "no-agent-forwarding",
        "password-disabled",
        "port-refused",
        "pubkey-rejected",
        "wrong-host",
        "wrong-port",
        "wrong-user",
    ]


def test_dns_failure_targets_an_unresolvable_name(scenarios):
    target = scenarios["dns-failure"].connection["target"]
    assert target.endswith(".invalid")


def test_dns_failure_carries_no_hostname(scenarios):
    """The resolve fault fires only when the config leaves the name
    intact, so the client resolves it and fails."""
    assert scenarios["dns-failure"].connection["hostname"] is None


def test_every_other_scenario_pins_the_loopback_hostname(scenarios):
    for scenario_id, scenario in scenarios.items():
        if scenario_id == "dns-failure":
            continue
        assert scenario.connection["hostname"] == "127.0.0.1", scenario_id


def test_wrong_host_points_at_the_decoy_alias(scenarios):
    connection = scenarios["wrong-host"].connection
    assert connection["port"] == 2223
    assert connection["hostkeyalias"] == "decoy"


def test_wrong_port_carries_the_dead_port_in_its_command(scenarios):
    scenario = scenarios["wrong-port"]
    assert "-p 2224" in scenario.command
    assert scenario.connection["port"] == 2222


def test_key_permissions_arms_the_host_mode(scenarios):
    assert scenarios["key-permissions"].connection["arm"] == {
        "kind": "key-mode",
        "mode": "0644",
    }


def test_password_disabled_omits_the_identity(scenarios):
    assert scenarios["password-disabled"].connection["identity"] is False


def test_wrong_user_connects_as_guest(scenarios):
    assert scenarios["wrong-user"].connection["user"] == "guest"


def test_no_agent_forwarding_requests_the_agent(scenarios):
    scenario = scenarios["no-agent-forwarding"]
    assert scenario.connection["agent"] is True
    assert "-A" in scenario.command
    assert "SSH_AUTH_SOCK" in scenario.command


def test_every_inject_path_points_at_a_real_script(scenarios):
    for scenario in scenarios.values():
        if scenario.inject:
            assert (AREA_ROOT / scenario.inject).exists(), scenario.id


def test_every_scenario_carries_a_signature_and_hints(scenarios):
    for scenario in scenarios.values():
        assert scenario.signature
        assert len(scenario.hints) >= 2
        assert scenario.reveal_wrong and scenario.reveal_fix
