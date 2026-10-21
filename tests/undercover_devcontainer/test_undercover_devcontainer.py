"""Guard the UnderCover dev container masters under fde/.devcontainer.

The masters mirror the contribution folder community_contributions/artem_koval
in ed-donner/undercover, as sent in pull request 22. The two sides stay
byte-identical, so the paths in the README speak about the upstream repo and
not about this repo. The env var UNDERCOVER_REPO gives the local clone of the
upstream repo for the byte-identity test. The test skips when the clone is
absent.
"""

import json
import os
import re
from pathlib import Path

import pytest

DEVCONTAINER_DIR = Path(__file__).resolve().parents[2] / "fde" / ".devcontainer"
DEVCONTAINER_JSON = DEVCONTAINER_DIR / "devcontainer.json"
README = DEVCONTAINER_DIR / "README.md"
UPSTREAM_SUBFOLDER = Path("community_contributions") / "artem_koval"
KEY_PATTERN = re.compile(r"sk-or-v1-[0-9a-zA-Z]{20,}")
JSON_STRING_OR_COMMENT = re.compile(r'"(?:[^"\\]|\\.)*"|//[^\n]*|/\*.*?\*/', re.DOTALL)


def _load_json(path):
    """Parse a devcontainer.json file, and drop its JSONC comments."""

    def keep_strings(match):
        return match.group(0) if match.group(0).startswith('"') else ""

    text = path.read_text(encoding="utf-8")
    return json.loads(JSON_STRING_OR_COMMENT.sub(keep_strings, text))


def _config():
    return _load_json(DEVCONTAINER_JSON)


def _upstream_copy(name):
    default_repo = Path.home() / "Documents" / "git" / "undercover"
    repo = Path(os.environ.get("UNDERCOVER_REPO", default_repo))
    return repo / UPSTREAM_SUBFOLDER / name


def test_devcontainer_json_exists_and_parses():
    assert DEVCONTAINER_JSON.is_file()
    assert _config()["name"] == "UnderCover"


def test_base_image_is_pinned():
    assert _config()["image"] == "mcr.microsoft.com/devcontainers/python:3-3.12-trixie"


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


def test_mirror_files_stay_clean():
    for path in (DEVCONTAINER_JSON, README):
        text = path.read_text(encoding="utf-8")
        assert text.isascii(), "the upstream checklist bans emojis"
        assert not KEY_PATTERN.search(text), f"no real API key in {path.name}"


def test_readme_tells_how_to_open_the_container():
    text = README.read_text(encoding="utf-8")
    assert "Reopen in Container" in text
    assert "OPENROUTER_API_KEY" in text


def test_load_json_accepts_comments(tmp_path):
    doc = tmp_path / "config.json"
    doc.write_text('{\n  // pin kept for trixie\n  "a": 1 /* one */\n}\n', encoding="utf-8")
    assert _load_json(doc) == {"a": 1}


def test_load_json_keeps_comment_marks_inside_strings(tmp_path):
    doc = tmp_path / "config.json"
    doc.write_text('{"u": "https://a//b", "q": "say \\"hi\\""}', encoding="utf-8")
    assert _load_json(doc) == {"u": "https://a//b", "q": 'say "hi"'}


def test_load_json_accepts_plain_json(tmp_path):
    doc = tmp_path / "config.json"
    doc.write_text('{"a": [1, 2]}', encoding="utf-8")
    assert _load_json(doc) == {"a": [1, 2]}


def test_masters_match_the_upstream_contribution():
    master = DEVCONTAINER_JSON.read_bytes()
    copy = _upstream_copy(Path(".devcontainer") / "devcontainer.json")
    if not copy.is_file():
        pytest.skip("no local clone of the upstream repo on this machine")
    assert master == copy.read_bytes()
    assert README.read_bytes() == _upstream_copy("README.md").read_bytes()
