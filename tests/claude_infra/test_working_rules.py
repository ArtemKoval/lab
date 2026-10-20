"""Pin the working-rules surfaces, so the rule text and the handover flow
survive refactors of CLAUDE.md, the feature-pipeline skill, the issue
template, and the permission rules."""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(*parts):
    return REPO_ROOT.joinpath(*parts).read_text(encoding="utf-8")


def test_claude_md_states_the_three_working_rules():
    text = _read("CLAUDE.md")
    working_rules = text.split("## Working rules", 1)[1]
    assert "Build a tool first." in working_rules
    assert "Keep reusable artifacts under version control." in working_rules
    assert "Open a handover issue after you solve a task." in working_rules
    assert "/tmp" in working_rules
    assert "Remove secrets" in working_rules


def test_feature_pipeline_carries_the_rules():
    text = _read(".claude", "skills", "feature-pipeline", "SKILL.md")
    assert "Prefer a tool to a prompt." in text
    assert "Keep artifacts that you will use again under version control." in text
    assert "open a handover issue" in text
    assert ".github/ISSUE_TEMPLATE/handover.md" in text


def test_handover_template_has_the_report_sections():
    text = _read(".github", "ISSUE_TEMPLATE", "handover.md")
    assert "name: Handover" in text
    for section in ("## Task", "## Logs", "## Metrics", "## Observations", "## Follow-ups"):
        assert section in text
    assert "Remove secrets" in text


def test_settings_allow_gh_issue_create():
    settings = json.loads(_read(".claude", "settings.json"))
    assert "Bash(gh issue create:*)" in settings["permissions"]["allow"]
