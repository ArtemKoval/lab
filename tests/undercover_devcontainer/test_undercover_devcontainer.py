"""Guard the UnderCover dev container master copies under fde/.devcontainer."""

import json
import re
from pathlib import Path

DEVCONTAINER_DIR = Path(__file__).resolve().parents[2] / "fde" / ".devcontainer"
DEVCONTAINER_JSON = DEVCONTAINER_DIR / "devcontainer.json"
README = DEVCONTAINER_DIR / "README.md"


def _config():
    return json.loads(DEVCONTAINER_JSON.read_text(encoding="utf-8"))


def test_devcontainer_json_exists_and_parses():
    assert DEVCONTAINER_JSON.is_file()
    assert _config()["name"] == "UnderCover"


def test_base_image_is_pinned():
    image = _config()["image"]
    assert image.startswith("mcr.microsoft.com/devcontainers/python:")
    assert "3.12" in image


def test_container_serves_the_repo_root():
    config = _config()
    assert config["workspaceFolder"] == "/workspaces/undercover"
    assert "${localWorkspaceFolder}/../.." in config["workspaceMount"]


def test_post_create_installs_both_package_managers():
    command = _config()["postCreateCommand"]
    assert "uv sync" in command
    assert "npm install" in command


def test_course_extensions_are_present():
    extensions = set(_config()["customizations"]["vscode"]["extensions"])
    assert {"ms-python.python", "ms-toolsai.jupyter"} <= extensions


def test_readme_exists_and_stays_clean():
    assert README.is_file()
    text = README.read_text(encoding="utf-8")
    assert text.isascii(), "the upstream checklist bans emojis and non-ASCII text"
    assert not re.search(r"sk-or-v1-[0-9a-zA-Z]{20,}", text), "no real API key"


def test_readme_tells_how_to_open_the_container():
    text = README.read_text(encoding="utf-8")
    assert "Reopen in Container" in text
    assert "OPENROUTER_API_KEY" in text
