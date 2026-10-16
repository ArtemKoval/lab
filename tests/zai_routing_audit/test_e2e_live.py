"""Live checks against the real endpoint. Opt-in only.

Run with:
    ZAI_ROUTING_AUDIT_E2E=1 tools/zai_routing_audit/.venv/bin/python -m pytest -m e2e
"""

import os
from pathlib import Path

import pytest

from zai_routing_audit import cli

GATE = os.environ.get("ZAI_ROUTING_AUDIT_E2E") == "1"
SETTINGS = Path.home() / ".claude" / "settings.json"

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(not GATE, reason="set ZAI_ROUTING_AUDIT_E2E=1 to run live checks"),
    pytest.mark.skipif(not SETTINGS.exists(), reason="no real settings file"),
]


def test_live_echo_matches():
    assert cli.main(["--json", "echo", "glm-5.3-flash"]) == 0


def test_live_usage_reports_rows():
    assert cli.main(["--json", "usage"]) == 0
