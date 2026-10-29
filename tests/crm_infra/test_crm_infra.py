"""Guard the crm project wiring: dev container, registry, skill, and nouns.

The crm project is a standalone port of the UnderCover week one milestones,
transformed into a generic CRM engine with an insurance domain pack. These
tests keep the parts a clean clone needs present and consistent, and keep
domain nouns out of the engine code.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CRM = ROOT / "crm"

# The engine directories the noun guard scans, and the nouns it bans.
ENGINE_DIRS = ("backend", "agent", "dashboard/src", "e2e")
BANNED_NOUNS = re.compile(
    r"\b(claims?|payouts?|handlers?|polic(?:y|ies)|undercover)\b", re.IGNORECASE
)
# Hits that are ordinary English or agreed spellings, one path fragment each.
# `e2e/pages.spec.ts`, `backend/tests/test_documents.py`, and
# `agent/tests/test_case_agent.py` pin the served text of the insurance pack,
# which keeps the pack's own words. The `agent/harness.py` middleware
# override keeps the framework's own parameter name.
ALLOWLIST: tuple[str, ...] = (
    "crm/e2e/pages.spec.ts",
    "crm/backend/tests/test_documents.py",
    "crm/agent/tests/test_case_agent.py",
    "crm/agent/harness.py",
)


def test_devcontainer_exists_and_is_pinned():
    config = json.loads((CRM / ".devcontainer" / "devcontainer.json").read_text())
    assert config["name"] == "crm"
    assert (
        config["image"] == "mcr.microsoft.com/devcontainers/python:3-3.12-trixie"
    )
    post_create = config["postCreateCommand"]
    assert "uv sync" in post_create
    assert "npm install" in post_create


def test_registry_carries_the_crm_units():
    registry = json.loads(
        (ROOT / "tools" / "project_setup" / "registry.json").read_text()
    )
    units = {unit["id"]: unit for unit in registry["units"]}
    for unit_id in ("uv", "crm-python-deps", "crm-node-deps"):
        unit = units[unit_id]
        assert unit["check"], f"{unit_id} carries no check"
        assert unit["install"], f"{unit_id} carries no install"
        assert unit["purpose"] and unit["requires"]


def test_the_crm_python_check_names_real_modules():
    registry = json.loads(
        (ROOT / "tools" / "project_setup" / "registry.json").read_text()
    )
    units = {unit["id"]: unit for unit in registry["units"]}
    modules = units["crm-python-deps"]["check"][-1].removeprefix("import ")
    assert "backend.main" in modules
    assert "agent.harness" in modules
    assert (CRM / "backend" / "main.py").is_file()
    assert (CRM / "agent" / "harness.py").is_file()


def test_the_crm_app_skill_exists():
    skill = ROOT / ".claude" / "skills" / "crm-app" / "SKILL.md"
    text = skill.read_text()
    assert "name: crm-app" in text
    for command in ("npm run dev", "npm run seed", "npm run check"):
        assert command in text


def test_the_port_tool_is_present():
    assert (CRM / "port" / "port.py").is_file()
    assert (CRM / "port" / "README.md").is_file()


def test_engine_code_carries_no_domain_noun():
    hits = []
    for engine_dir in ENGINE_DIRS:
        for path in (CRM / engine_dir).rglob("*"):
            if path.suffix not in (".py", ".ts", ".tsx", ".css", ".html"):
                continue
            for number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if BANNED_NOUNS.search(line) and not _allowed(path, line):
                    hits.append(f"{path.relative_to(ROOT)}:{number}: {line.strip()}")
    assert hits == []


def _allowed(path: Path, line: str) -> bool:
    lowered = line.lower()
    if "claimed" in lowered:
        return True
    return any(str(path.relative_to(ROOT)).startswith(allow) for allow in ALLOWLIST)
