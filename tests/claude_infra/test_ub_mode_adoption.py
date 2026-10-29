"""Pin the adopt-ub-mode adoption: the vendored gate tools with provenance,
the ub-mode skill, the registry units, and the feature-pipeline integration."""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

PINNED_COMMITS = {
    "crapper": "6fd92c4c9bcc56efb64a2f8743d5a2993bcfd42d",
    "dryer": "66ff6d21a42c04afcad89c78a80066176d1294b0",
    "mutator": "a5a0cb803b66e0cdb8bf471b3b08af701d424a41",
}
SKILL_COMMIT = "57a8bdd28e45ed41900ace0bafa2ff76dd9ed70f"


def _read(*parts):
    return REPO_ROOT.joinpath(*parts).read_text(encoding="utf-8")


def _collapsed(*parts):
    return re.sub(r"\s+", " ", _read(*parts))


def _frontmatter(*parts):
    return _read(*parts).split("---", 2)[1]


def test_vendored_tools_carry_the_upstream_layout():
    for tool in ("crapper", "dryer", "mutator"):
        base = REPO_ROOT / "tools" / tool
        assert (base / "LICENSE").is_file(), tool
        assert (base / "src" / tool).is_dir(), tool
        assert (base / "tests").is_dir(), tool
        assert (base / "pyproject.toml").is_file(), tool
    assert (REPO_ROOT / "tools" / "crapper" / "crapper").is_file()
    assert (REPO_ROOT / "tools" / "dryer" / "dryer").is_file()
    assert (REPO_ROOT / "tools" / "mutator" / "mutator").is_file()
    assert (REPO_ROOT / "tools" / "crapper" / "uml").is_file()


def test_vendored_readmes_pin_the_upstream_url_and_commit():
    for tool, commit in PINNED_COMMITS.items():
        text = _read("tools", tool, "README.md")
        assert f"https://github.com/unclebob/{tool}" in text, tool
        assert commit in text, tool
        assert "0BSD" in text, tool


def test_dryer_carries_the_fail_above_flag_and_owned_tests():
    cli = _read("tools", "dryer", "src", "dryer", "cli.py")
    assert "--fail-above" in cli
    assert "options.fail_above" in cli
    assert _read("tools", "dryer", "tests", "test_fail_above.py")


def test_mutator_sits_beside_crapper():
    assert (REPO_ROOT / "tools" / "crapper").is_dir()
    assert (REPO_ROOT / "tools" / "mutator").is_dir()


def test_ub_mode_skill_resolves_with_provenance():
    head = _frontmatter(".claude", "skills", "ub-mode", "SKILL.md")
    assert "name: ub-mode" in head
    assert "Use when" in head
    assert "/ub-mode" in head
    assert "reduced principles" in head
    assert "from: unclebob/ub-mode" in head
    assert f"commit: {SKILL_COMMIT}" in head
    assert "license: none - unlicensed upstream" in head


def test_ub_mode_skill_keeps_the_upstream_body_and_local_section():
    text = _read(".claude", "skills", "ub-mode", "SKILL.md")
    for phase in ("First Make it Work", "Then Make it Right", "Follow Practice"):
        assert phase in text
    for rule in (
        "Laziness Protocol",
        "Attack the Premise",
        "Subtract Before You Add",
        "Redesign From First Principles",
    ):
        assert rule in text
    assert "# Local Gates" in text
    assert "tools/crapper/crapper --threshold 10" in text
    assert "tools/dryer/dryer --threshold 0.8 --fail-above" in text
    assert "tools/mutator/mutator" in text
    assert "uml-viewer" in text


def test_registry_carries_one_unit_per_gate_tool():
    registry = json.loads(_read("tools", "project_setup", "registry.json"))
    units = {unit["id"]: unit for unit in registry["units"]}
    for tool in ("crapper", "dryer", "mutator"):
        unit = units[f"{tool}-python-deps"]
        assert unit["kind"] == "dependency-file", tool
        assert f"tools/{tool}/.venv" in " ".join(unit["check"]), tool
        assert "-e" in unit["install"], tool
        assert "coverage" in unit["install"], tool


def test_pipeline_carries_the_adopted_discipline():
    text = _collapsed(".claude", "skills", "feature-pipeline", "SKILL.md")
    for phase in ("First Make it Work", "Then Make it Right", "Practice"):
        assert phase in text
    for rule in (
        "One decision lives in one place",
        "Get the data shape right before you write the logic",
        "Do not bolt a new requirement onto the old design",
        "Attack the premise",
        "Subtract before you add",
    ):
        assert rule in text


def test_pipeline_steps_carry_the_test_and_commit_rules():
    text = _collapsed(".claude", "skills", "feature-pipeline", "SKILL.md")
    assert "Throw out a test that still passes when every function returns nothing" in text
    assert "Each commit says why, what changed, and how you proved it" in text


def test_pipeline_names_the_default_gates():
    text = _collapsed(".claude", "skills", "feature-pipeline", "SKILL.md")
    assert "tools/crapper/crapper --threshold 10" in text
    assert "tools/dryer/dryer --threshold 0.8 --fail-above" in text
    assert "tools/mutator/mutator" in text
