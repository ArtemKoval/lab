"""Browser journeys over the fixture preview page. Opt-in only.

Run with:
    DSPY_GATE_E2E=1 tools/dspy_gate/.venv/bin/python -m pytest -m e2e tests/dspy_gate/test_journeys.py

The a11y-first rule: semantic claims read the accessibility tree.
Pixels serve layout claims only, and the VLM judge votes on them only
when the provider key is present.
"""

import os
from pathlib import Path

import pytest

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        os.environ.get("DSPY_GATE_E2E") != "1",
        reason="set DSPY_GATE_E2E=1 to run the browser journeys",
    ),
]

playwright = pytest.importorskip("playwright.sync_api")

EXPECTED_ROWS = [
    ("production down", "P0", "on-call"),
    ("refund the June charge", "P2", "billing"),
    ("rename my workspace", "P3", "general"),
]


def test_the_a11y_tree_carries_the_triage_rows():
    from dspy_gate.harness import preview

    server = preview.start_server(port=0)
    try:
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 720})
            page.goto(f"http://127.0.0.1:{server.port}/")
            table = page.get_by_role("table", name="Triage results")
            for ticket, severity, team in EXPECTED_ROWS:
                row = table.get_by_role("row").filter(has_text=ticket)
                assert row.get_by_role("cell", name=severity).count() >= 1
                assert row.get_by_role("cell", name=team).count() >= 1
            banner = page.get_by_role("status")
            assert "Escalation recorded before reply" in banner.inner_text()
            browser.close()
    finally:
        server.shutdown()
