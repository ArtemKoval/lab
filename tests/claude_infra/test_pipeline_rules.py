"""Pin the superpowers-derived rules in the feature-pipeline skill and
the absence of the stale no-hooks claims."""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PIPELINE = REPO_ROOT / ".claude" / "skills" / "feature-pipeline" / "SKILL.md"
APPLY_SKILL = REPO_ROOT / ".claude" / "skills" / "openspec-apply-change" / "SKILL.md"


def _collapsed(path):
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))


def test_review_reception_rules_present():
    text = _collapsed(PIPELINE)
    assert "verify each one against the code before you implement it" in text
    assert "No performative agreement" in text
    assert "Clarify every unclear item before you fix any item" in text
    assert "Reply in the review thread, not as a top-level comment" in text


def test_model_selection_rule_present():
    text = _collapsed(PIPELINE)
    assert "Name the model on every agent dispatch when the harness allows it" in text
    assert "Give the final whole-diff review to the strongest available model" in text
    assert "Judge cost by turn count, not token price" in text


def test_discard_contract_present():
    assert "Destroy work only after the user types discard" in _collapsed(PIPELINE)


def test_worktree_provenance_rule_present():
    text = _collapsed(PIPELINE)
    assert "Remove only worktrees this pipeline created" in text
    assert "show the user the file list first and never force" in text
    assert "leave worktrees other tools created in place" in text


def test_builder_check_present():
    text = _collapsed(PIPELINE)
    assert "Builder check before the proposal PR" in text
    assert "asks a builder's questions" in text
    assert "theirs (one message to the user)" in text


def test_stale_no_hooks_claims_gone():
    text = PIPELINE.read_text(encoding="utf-8")
    assert "has adopted no hooks yet" not in text
    assert "no `hooks` key in `.claude/settings.json`" not in text


def test_apply_skill_carries_the_plan_exec_section():
    text = _collapsed(APPLY_SKILL)
    assert "plan_exec ledger (long runs)" in text
    assert "ledger ... init" in text
    assert "ledger ... complete" in text
    assert "ledger ... show" in text
    assert "package ... --base" in text
    assert "trust it plus `git log` over recollection" in text
