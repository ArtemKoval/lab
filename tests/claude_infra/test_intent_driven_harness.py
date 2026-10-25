"""Pin the intent-driven harness wiring: schema resolution, ported skills
and agents, rule-to-skill resolution, ADR seeds, and the glossary paths."""

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PINNED_COMMIT = "b5bda460a2180a55fc508fdedc4ef058d95355db"
PORTED_SKILLS = (
    "grill-me",
    "adversarial-authoring",
    "architectural-decision-records",
    "c4-diagrams",
    "gherkin-authoring",
    "glossary",
    "openspec-git-discipline",
    "verify-change",
    "spec-as-source",
    "acceptance-test-authoring",
    "test-driven-development",
)
AGENTS = ("adversarial-author", "adversarial-reviewer", "senior-dev", "senior-qa")
ARTIFACT_IDS = ("proposal", "specs", "design", "adr", "tasks")
ADR_TEMPLATES = ("custom.md", "madr-full.md", "madr-minimal.md", "nygard.md", "y-statement.md")


def _read(*parts):
    return REPO_ROOT.joinpath(*parts).read_text(encoding="utf-8")


def _frontmatter(path):
    head = path.read_text(encoding="utf-8").split("---", 2)[1]
    return head


def test_schema_files_resolve_and_validate():
    schema = _read("openspec", "schemas", "intent-driven", "schema.yaml")
    assert "name: intent-driven" in schema
    for artifact in ARTIFACT_IDS:
        assert f"- id: {artifact}" in schema, artifact
    for template in ARTIFACT_IDS:
        name = "spec" if template == "specs" else template
        assert _read("openspec", "schemas", "intent-driven", "templates", f"{name}.md"), name
    assert _read("openspec", "schemas", "intent-driven", "README.md")


def test_schema_validate_runs_from_repo_root():
    if shutil.which("openspec") is None:
        pytest.skip("openspec CLI is not installed")
    result = subprocess.run(
        ["openspec", "schema", "validate", "intent-driven"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_agents_carry_required_frontmatter():
    agent_dir = REPO_ROOT / ".claude" / "agents"
    files = sorted(agent_dir.glob("*.md"))
    assert {f.stem for f in files} == set(AGENTS)
    for path in files:
        head = _frontmatter(path)
        assert f"name: {path.stem}" in head, path.name
        assert "description:" in head
        description_line = next(
            line for line in head.splitlines() if line.startswith("description:")
        )
        assert description_line.strip() != "description:", path.name


def test_rules_resolve_to_skills_and_layers_stay_disabled():
    config = _read("openspec", "config.yaml")
    rules = []
    for line in config.splitlines():
        stripped = line.strip()
        if stripped.startswith("- Must use ") and stripped.endswith(" skill"):
            rules.append(stripped.removeprefix("- Must use ").removesuffix(" skill"))
    assert len(rules) == 6, rules
    for name in rules:
        assert (REPO_ROOT / ".claude" / "skills" / name / "SKILL.md").is_file(), name
    for line in config.splitlines():
        for disabled in ("spec-as-source", "glossary"):
            if disabled in line:
                assert disabled not in line.split("#", 1)[0], line
    # the schema switch is live
    assert config.splitlines()[0] == "schema: intent-driven"


def test_ported_skills_carry_provenance_and_support_files():
    for name in PORTED_SKILLS:
        skill = _read(".claude", "skills", name, "SKILL.md")
        head = skill.split("---", 2)[1]
        assert "ported:" in head, name
        assert PINNED_COMMIT in head, name
    for template in ADR_TEMPLATES:
        assert (REPO_ROOT / ".claude" / "skills" / "architectural-decision-records" / "templates" / template).is_file(), template
    assert (REPO_ROOT / ".claude" / "skills" / "architectural-decision-records" / "preferences.md").is_file()
    authoring = _read(".claude", "skills", "adversarial-authoring", "SKILL.md")
    for agent in AGENTS[:2]:
        assert agent in authoring, agent
    assert "test-driven-development" in _read(".claude", "agents", "senior-dev.md")
    assert "acceptance-test-authoring" in _read(".claude", "agents", "senior-qa.md")


def test_discipline_gates_are_documented():
    pipeline = _read(".claude", "skills", "feature-pipeline", "SKILL.md")
    assert "Discipline, first merge" in pipeline
    assert "chore/archive-<change>" in pipeline
    assert "openspec-git-discipline" in pipeline
    claude_md = _read("CLAUDE.md")
    assert "Change discipline" in claude_md
    assert "superseding ADR" in claude_md


def test_adr_seeds_exist_and_supersede_nothing():
    for name in ("0001-add-intent-driven-harness.md", "0002-claude-code-single-harness.md"):
        text = _read("adr", name)
        assert "- Status: accepted" in text, name
        assert not any(
            line.strip().startswith("Supersedes:") or line.strip().startswith("- Supersedes:")
            for line in text.splitlines()
        ), name


def test_glossary_lives_where_the_skill_reads_it():
    business = _read("glossary", "business.md")
    technical = _read("glossary", "technical.md")
    for term in ("Capability:", "Intent:", "Gate:", "Handover:"):
        assert term in business, term
    for term in ("ASIT:", "ADR:", "Council notes:", "Spec delta:", "Supersession:", "Harness:"):
        assert term in technical, term


ADOPTION_SKILLS = (
    "systematic-debugging",
    "verification-before-completion",
    "writing-skills",
)
UPSTREAM_COMMIT = "2ce8aa15d05bd57213e6f746f953aafb7ded7a8b"


def test_adoption_skills_resolve_with_upstream_provenance():
    for name in ADOPTION_SKILLS:
        frontmatter = _frontmatter(REPO_ROOT / ".claude" / "skills" / name / "SKILL.md")
        assert f"name: {name}" in frontmatter, name
        assert "Use when" in frontmatter, name
        assert "from: obra/superpowers" in frontmatter, name
        assert f"commit: {UPSTREAM_COMMIT}" in frontmatter, name
        assert "license: MIT" in frontmatter, name
    # The template-pinned tuple stays untouched by the adoption skills.
    assert not set(ADOPTION_SKILLS) & set(PORTED_SKILLS)
