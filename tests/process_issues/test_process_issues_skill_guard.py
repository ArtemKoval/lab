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
    assert "cron" in section and "08:00" in section and "20:00" in section
