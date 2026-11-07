"""Guard test for the pre-flight order in the process-issues skill.

The halt pre-flight step lives in skill prose by design, so the delta
scenario maps to this text guard instead of CLI code.
"""

from pathlib import Path

import pytest

SKILL = (Path(__file__).absolute().parents[2]
         / ".claude" / "skills" / "process-issues" / "SKILL.md")


def test_skill_preflight_orders_halt_peak_lock_scan():
    if not SKILL.exists():
        pytest.skip("the skill text lives outside this copy")
    text = SKILL.read_text(encoding="utf-8")
    section = text.split("## Pre-flight", 1)[1].split("\n## ", 1)[0]
    halt = section.find("halt")
    peak = section.find("peak window")
    acquire = section.find("acquire")
    scan = section.find("scan")
    assert -1 < halt < peak < acquire < scan


def test_skill_scheduled_run_orders_status_action_peak_acquire_scan():
    if not SKILL.exists():
        pytest.skip("the skill text lives outside this copy")
    text = SKILL.read_text(encoding="utf-8")
    assert "## Scheduled run" in text
    section = text.split("## Scheduled run", 1)[1].split("\n## ", 1)[0]
    status_step = section.find("1. Run `status --json`")
    peak_step = section.find("peak-hours-gate")
    acquire_step = section.find("8. Take the lock with `acquire")
    scan_step = section.find("9. Run the scan")
    release_step = section.find("11. Release the lock")
    assert -1 < status_step < peak_step < acquire_step < scan_step \
        < release_step
    assert "stop silently" in section
    assert "one issue per fire" in section
    assert "human spec gate" in section
    assert "named blocked" in section
    assert "config, issue-list, or lock row" in section
    assert "cron" in section and "08:00" in section and "20:00" in section


def test_skill_phases_carry_the_ledger_steps():
    if not SKILL.exists():
        pytest.skip("the skill text lives outside this copy")
    text = SKILL.read_text(encoding="utf-8")
    assert "## Phases" in text
    section = text.split("## Phases", 1)[1].split("\n## ", 1)[0]
    write_step = section.find("run `ledger write --kind K --key N`")
    confirm_step = section.find("run `ledger confirm --id MARKER`")
    pending_step = section.find("actions run `ledger pending`")
    assert -1 < write_step < confirm_step
    assert -1 < pending_step
    assert "process-issues loop" in section
    assert "process-issues:MARKER-->" in section
    assert "scan the bodies for the literal marker" in section
    assert "with the same marker and no new intent" in section
    assert "Retry a label" in section and "as a plain re-add" in section
    assert "already-done" in section and "as the confirmation" in section
    assert "behaves like a gate failure" in section
    fails = text.split("## Failures", 1)[1].split("\n## ", 1)[0]
    assert "pending list" in fails

def test_skill_phases_open_with_the_pick_acknowledgement():
    """Map the three pick scenarios to skill prose.

    The acknowledgement rule lives in skill prose by design, so the
    delta scenarios map to this text guard instead of CLI code: the
    object line, the fixed first line, and the silence rule.
    """
    if not SKILL.exists():
        pytest.skip("the skill text lives outside this copy")
    text = SKILL.read_text(encoding="utf-8")
    assert "## Phases" in text
    section = text.split("## Phases", 1)[1].split("\n## ", 1)[0]
    pick = section.find("- Pick.")
    propose = section.find("- Propose phase")
    assert -1 < pick < propose
    fixed = section.find("process-issues loop", pick)
    on_it = section.find("`On it:", pick)
    assert -1 < fixed < on_it
    assert "names the object" in section and "expected result" in section
    assert "no progress comment" in section
    assert "phase result" in section
    assert "posts no pick comment" in section
