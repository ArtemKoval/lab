"""Behavior tests for the session status line setup doctor and the
registry unit. The doctor runs in process, per the house pattern."""

import json
import shutil
from pathlib import Path

import session_statusline_setup as doctor

# absolute(), not resolve(): the mutator symlink overlay must keep this
# path inside the worker tree for the registry read.
REPO_ROOT = Path(__file__).absolute().parents[2]


def make_checkout(tmp_path):
    """Copy the wiring surfaces into one checkout-shaped tree."""
    root = tmp_path / "repo"
    (root / "tools" / "session_statusline").mkdir(parents=True)
    (root / "tools" / "zai_routing_audit" / ".venv" / "bin").mkdir(parents=True)
    (root / ".claude").mkdir()
    shutil.copy(
        REPO_ROOT / "tools" / "session_statusline" / "session_statusline.py",
        root / "tools" / "session_statusline" / "session_statusline.py",
    )
    (root / "tools" / "zai_routing_audit" / ".venv" / "bin" / "python").write_text("")
    (root / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")
    return root


def test_registry_carries_the_statusline_unit():
    registry = json.loads(
        (REPO_ROOT / "tools" / "project_setup" / "registry.json").read_text(
            encoding="utf-8"
        )
    )
    units = {unit["id"]: unit for unit in registry["units"]}
    unit = units["session-statusline"]
    assert unit["kind"] == "hook-wiring"
    assert unit["install"].endswith("--install")
    assert "zai-routing-audit-python-deps" in unit["requires"]


def test_doctor_reports_ok_on_this_checkout(capsys):
    code = doctor.main(["--repo-root", str(REPO_ROOT), "--json"])
    report = json.loads(capsys.readouterr().out)
    assert code == 0
    assert report["ok"] is True
    assert report["problems"] == []


def test_doctor_install_writes_the_checkout_paths(tmp_path, capsys):
    root = make_checkout(tmp_path)
    code = doctor.main(["--repo-root", str(root), "--install", "--json"])
    report = json.loads(capsys.readouterr().out)
    assert code == 0
    assert report["ok"] is True
    settings = json.loads((root / ".claude" / "settings.json").read_text())
    command = settings["statusLine"]["command"]
    assert command.startswith(f"{root}/tools/zai_routing_audit/.venv/bin/python ")
    assert command.endswith(f"{root}/tools/session_statusline/session_statusline.py")
    assert settings["statusLine"]["refreshInterval"] == 15


def test_doctor_repairs_a_foreign_command(tmp_path, capsys):
    root = make_checkout(tmp_path)
    settings_path = root / ".claude" / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "statusLine": {
                    "type": "command",
                    "command": "/elsewhere/python /elsewhere/tool.py",
                    "refreshInterval": 60,
                }
            }
        ),
        encoding="utf-8",
    )
    code = doctor.main(["--repo-root", str(root), "--json"])
    report = json.loads(capsys.readouterr().out)
    assert code == 2
    assert report["status"]["settings"] == "foreign"
    code = doctor.main(["--repo-root", str(root), "--install", "--json"])
    assert code == 0
    command = json.loads(settings_path.read_text())["statusLine"]["command"]
    assert str(root) in command


def test_doctor_reports_missing_pieces(tmp_path, capsys):
    root = tmp_path / "empty"
    root.mkdir()
    (root / ".claude").mkdir()
    (root / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")
    code = doctor.main(["--repo-root", str(root), "--json"])
    report = json.loads(capsys.readouterr().out)
    assert code == 2
    assert report["ok"] is False
    assert report["status"]["tool"] == "missing"
    assert report["status"]["venv"] == "missing"
    assert report["status"]["settings"] == "absent"


def test_doctor_survives_unreadable_settings(tmp_path, capsys):
    root = make_checkout(tmp_path)
    (root / ".claude" / "settings.json").write_text("{broken", encoding="utf-8")
    code = doctor.main(["--repo-root", str(root), "--json"])
    report = json.loads(capsys.readouterr().out)
    assert code == 2
    assert report["status"]["settings"] == "unreadable"
    assert report["ok"] is False


def test_doctor_plain_text_output(capsys):
    code = doctor.main(["--repo-root", str(REPO_ROOT)])
    out = capsys.readouterr()
    assert code == 0
    assert "session-statusline wiring: ok" in out.out


def test_doctor_install_skips_without_the_tool_dir(tmp_path, capsys):
    root = tmp_path / "no-tool"
    root.mkdir()
    (root / ".claude").mkdir()
    (root / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")
    code = doctor.main(["--repo-root", str(root), "--install", "--json"])
    assert code == 2
    assert json.loads((root / ".claude" / "settings.json").read_text()) == {}


def test_doctor_install_rebuilds_unreadable_settings(tmp_path, capsys):
    root = make_checkout(tmp_path)
    (root / ".claude" / "settings.json").write_text("{broken", encoding="utf-8")
    code = doctor.main(["--repo-root", str(root), "--install", "--json"])
    report = json.loads(capsys.readouterr().out)
    assert code == 0
    assert report["ok"] is True
    block = json.loads((root / ".claude" / "settings.json").read_text())
    assert block["statusLine"]["type"] == "command"


def test_doctor_plain_text_names_problems_on_stderr(tmp_path, capsys):
    root = tmp_path / "empty"
    root.mkdir()
    (root / ".claude").mkdir()
    (root / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")
    code = doctor.main(["--repo-root", str(root)])
    captured = capsys.readouterr()
    assert code == 2
    assert "the tool file is missing" in captured.err
    assert "session-statusline wiring: broken" in captured.out
