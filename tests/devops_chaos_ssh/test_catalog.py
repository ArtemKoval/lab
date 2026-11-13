"""The catalog loader: parse, validate, and index the scenario
files."""

import json
from pathlib import Path

import pytest

from chaos_ssh.catalog import CatalogError, Scenario, load_catalog


def write_scenario(directory: Path, data: dict, name: str | None = None):
    """Write one catalog file; the name defaults to the scenario id."""
    path = directory / f"{name or data['id']}.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def make_dir(tmp_path):
    """The catalog directory inside the temp area root."""
    directory = tmp_path / "catalog"
    directory.mkdir(exist_ok=True)
    return directory


@pytest.fixture(autouse=True)
def inject_script(tmp_path):
    """The referenced inject script exists in the temp area."""
    directory = tmp_path / "environments" / "inject"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "port-refused.sh").write_text(
        "#!/bin/bash\n", encoding="utf-8"
    )


def valid_data(scenario_id="port-refused", **overrides):
    """One valid scenario body with every required field."""
    data = {
        "id": scenario_id,
        "title": "The ssh daemon is stopped",
        "phase": "transport",
        "fault": "The injection stops the practice sshd.",
        "inject": "environments/inject/port-refused.sh",
        "command": "ssh -F {scratch}/config {target}",
        "signature": "Connection refused",
        "prompts": ["What does the message name as the failure?"],
        "hints": ["Examine the port number in your command."],
        "reveal": {
            "wrong": "The injection stopped the practice sshd.",
            "fix": "Start the ssh service again.",
        },
        "connection": {
            "target": "practice",
            "hostname": "127.0.0.1",
            "user": "practice",
            "port": 2222,
            "identity": True,
            "hostkeyalias": None,
            "arm": None,
            "agent": False,
        },
    }
    data.update(overrides)
    return data


def test_load_reads_every_file_and_sorts_by_id(tmp_path):
    write_scenario(make_dir(tmp_path), valid_data("port-refused"))
    write_scenario(make_dir(tmp_path), valid_data("dns-failure", inject=None))
    scenarios = load_catalog(make_dir(tmp_path))
    assert [s.id for s in scenarios] == ["dns-failure", "port-refused"]


def test_load_returns_scenario_objects_with_reveal_fields(tmp_path):
    write_scenario(make_dir(tmp_path), valid_data())
    scenario = load_catalog(make_dir(tmp_path))[0]
    assert isinstance(scenario, Scenario)
    assert scenario.inject == "environments/inject/port-refused.sh"
    assert scenario.reveal_wrong == "The injection stopped the practice sshd."
    assert scenario.reveal_fix == "Start the ssh service again."


def test_missing_file_field_raises_catalog_error(tmp_path):
    data = valid_data()
    del data["signature"]
    write_scenario(make_dir(tmp_path), data)
    with pytest.raises(CatalogError) as exc:
        load_catalog(make_dir(tmp_path))
    assert "signature" in str(exc.value)


def test_reveal_without_wrong_or_fix_raises(tmp_path):
    data = valid_data(reveal={"wrong": "x"})
    write_scenario(make_dir(tmp_path), data)
    with pytest.raises(CatalogError) as exc:
        load_catalog(make_dir(tmp_path))
    assert "fix" in str(exc.value)


def test_connection_without_port_raises(tmp_path):
    data = valid_data()
    del data["connection"]["port"]
    write_scenario(make_dir(tmp_path), data)
    with pytest.raises(CatalogError) as exc:
        load_catalog(make_dir(tmp_path))
    assert "port" in str(exc.value)


def test_file_name_that_differs_from_id_raises(tmp_path):
    write_scenario(make_dir(tmp_path), valid_data("port-refused"), name="other")
    with pytest.raises(CatalogError) as exc:
        load_catalog(make_dir(tmp_path))
    assert "port-refused" in str(exc.value)


def test_ids_stay_unique_through_the_file_name_rule(tmp_path):
    write_scenario(make_dir(tmp_path), valid_data("same"))
    write_scenario(make_dir(tmp_path), valid_data("other"), name="other")
    scenarios = load_catalog(make_dir(tmp_path))
    ids = [scenario.id for scenario in scenarios]
    assert len(ids) == len(set(ids))


def test_empty_catalog_directory_raises(tmp_path):
    with pytest.raises(CatalogError) as exc:
        load_catalog(make_dir(tmp_path))
    assert "catalog" in str(exc.value)


def test_broken_json_raises_catalog_error(tmp_path):
    (make_dir(tmp_path) / "broken.json").write_text(
        "{not json", encoding="utf-8"
    )
    with pytest.raises(CatalogError) as exc:
        load_catalog(make_dir(tmp_path))
    assert "broken.json" in str(exc.value)


def test_empty_prompts_raise(tmp_path):
    write_scenario(make_dir(tmp_path), valid_data(prompts=[]))
    with pytest.raises(CatalogError) as exc:
        load_catalog(make_dir(tmp_path))
    assert "prompts" in str(exc.value)


def test_null_inject_is_allowed(tmp_path):
    write_scenario(make_dir(tmp_path), valid_data("dns-failure", inject=None))
    scenario = load_catalog(make_dir(tmp_path))[0]
    assert scenario.inject is None
