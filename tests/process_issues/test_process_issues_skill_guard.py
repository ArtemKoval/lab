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
