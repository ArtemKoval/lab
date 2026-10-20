"""Exercise the CLI contract against a real filesystem. Hermetic."""

import json
from pathlib import Path

from devcontainer_init.cli import main


def _read(target):
    path = Path(target) / ".devcontainer" / "devcontainer.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _existing_config(target, name="demo"):
    target.mkdir()
    config_path = target / ".devcontainer" / "devcontainer.json"
    config_path.parent.mkdir()
    config_path.write_text(json.dumps({"name": name}) + "\n", encoding="utf-8")
    return config_path


def test_scaffold_writes_the_default_config(tmp_path, capsys):
    target = tmp_path / "demo"
    target.mkdir()
    assert main([str(target)]) == 0
    config = _read(target)
    assert config["name"] == "demo"
    assert config["image"] == "ubuntu:26.04"
    assert config["remoteUser"] == "vscode"
    assert config["customizations"]["vscode"]["extensions"] == []
    assert capsys.readouterr().out.startswith("wrote ")


def test_scaffold_reuses_an_existing_devcontainer_directory(tmp_path):
    target = tmp_path / "demo"
    target.mkdir()
    (target / ".devcontainer").mkdir()
    assert main([str(target)]) == 0
    assert _read(target)["name"] == "demo"


def test_scaffold_reports_the_written_path_in_json(tmp_path, capsys):
    target = tmp_path / "demo"
    target.mkdir()
    assert main([str(target), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "ok": True,
        "written": str(target / ".devcontainer" / "devcontainer.json"),
        "os": "26.04",
        "extensions": [],
    }


def test_missing_target_fails_without_creating_it(tmp_path, capsys):
    missing = tmp_path / "nope"
    assert main([str(missing)]) == 2
    assert not missing.exists()
    assert "does not exist" in capsys.readouterr().err


def test_missing_target_reports_json_failure(tmp_path, capsys):
    assert main([str(tmp_path / "nope"), "--json"]) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert "does not exist" in payload["error"]


def test_refuses_overwrite_without_force(tmp_path, capsys):
    target = tmp_path / "demo"
    config_path = _existing_config(target)
    assert main([str(target)]) == 2
    assert config_path.read_text(encoding="utf-8") == '{"name": "demo"}\n'
    assert "refusing" in capsys.readouterr().err


def test_force_overwrites_an_existing_config(tmp_path):
    target = tmp_path / "demo"
    _existing_config(target)
    assert main([str(target), "--force"]) == 0
    assert _read(target)["image"] == "ubuntu:26.04"


def test_os_and_extension_flags_flow_into_the_config(tmp_path):
    target = tmp_path / "demo"
    target.mkdir()
    argv = [
        str(target),
        "--os",
        "24.04",
        "--extension",
        "a",
        "--extension",
        "b",
        "--extension",
        "a",
    ]
    assert main(argv) == 0
    config = _read(target)
    assert config["image"] == "ubuntu:24.04"
    assert config["customizations"]["vscode"]["extensions"] == ["a", "b"]


def test_default_target_is_the_current_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main([]) == 0
    assert (tmp_path / ".devcontainer" / "devcontainer.json").exists()
