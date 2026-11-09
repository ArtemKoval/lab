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
    for section in (
        "## Task",
        "## Telemetry",
        "## Logs",
        "## Gates",
        "## Metrics",
        "## Observations",
        "## Follow-ups",
    ):
        assert section in text
    assert "Remove secrets" in text


def test_handover_template_carries_the_gate_outcome_rule():
    text = _read(".github", "ISSUE_TEMPLATE", "handover.md")
    phrases = (
        "the command, the",
        "the exit code",
        "A skip carries the reason",
        "counts as a failed gate",
    )
    assert all(phrase in text for phrase in phrases)


def test_settings_allow_gh_issue_create():
    settings = json.loads(_read(".claude", "settings.json"))
    assert "Bash(gh issue create:*)" in settings["permissions"]["allow"]


def test_claude_md_documents_the_gate_integrity_marker():
    text = _read("CLAUDE.md")
    assert "tests/claude_infra/test_gate_integrity.py" in text
    assert "gate-integrity: acknowledged" in text


def test_gate_integrity_guard_keeps_its_shape():
    text = _read("tests", "claude_infra", "test_gate_integrity.py")
    assert 'MARKER_LINE = "gate-integrity: acknowledged"' in text
    assert "PROTECTED_PATTERNS = (" in text
    assert ".claude/hooks/*" in text
    assert "conftest.py" in text
    assert "pytest.fail(" in text
    assert '--name-only",\n        "origin/' in text


def test_confidence_discipline_pinned():
    text = " ".join(_read("CLAUDE.md").split())
    rules = text.split("## Working rules", 1)[1]
    first = (
        "Every finding in a report or a handover issue carries a "
        "confidence of observed, derived, or inferred"
    )
    second = "A limitation goes in a limitations list, not in the finding text"
    third = "An open unknown goes in a list with a status and a next probe"
    assert first in rules
    assert second in rules
    assert third in rules
    order = [
        rules.index("Keep reusable artifacts under version control"),
        rules.index(first),
        rules.index("Open a handover issue after you solve a task"),
    ]
    assert order == sorted(order)


def test_handover_template_has_the_unknown_sections():
    text = _read(".github", "ISSUE_TEMPLATE", "handover.md")
    expected = """## Limitations

<!-- One line per limitation. A limitation says what this run's
     results do not cover. Write None when the run has no limitation. -->

## Open unknowns

<!-- One line per open unknown: the question, the status, and the
     next probe. Write None when the run leaves no question open. -->

## Follow-ups"""
    assert expected in text
