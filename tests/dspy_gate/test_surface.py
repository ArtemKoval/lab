"""Tests for the fixture preview page and the visual-baseline
governance rule."""

import urllib.request

import pytest

from dspy_gate import surface
from dspy_gate.harness import preview


@pytest.fixture(scope="module")
def server():
    started = preview.start_server(port=0)
    yield started
    started.shutdown()


def fetch(url):
    with urllib.request.urlopen(url, timeout=5) as response:
        return response.read().decode("utf-8")


def test_the_preview_page_serves_deterministic_content(server):
    base = f"http://127.0.0.1:{server.port}/"
    first = fetch(base)
    second = fetch(base)
    assert first == second


def test_the_preview_page_carries_the_governed_labels(server):
    page = fetch(f"http://127.0.0.1:{server.port}/")
    assert "Triage Console" in page
    assert "severity" in page and "team" in page


def test_the_preview_page_carries_the_fixture_rows(server):
    page = fetch(f"http://127.0.0.1:{server.port}/")
    assert "P0" in page
    assert "on-call" in page


def test_the_port_takes_the_env_override(monkeypatch):
    monkeypatch.setenv("DSPY_GATE_PREVIEW_PORT", "8399")
    assert preview.configured_port(default=8321) == 8399


def test_the_port_defaults_to_8321(monkeypatch):
    monkeypatch.delenv("DSPY_GATE_PREVIEW_PORT", raising=False)
    assert preview.configured_port(default=8321) == 8321


def test_a_visual_scenario_without_a_baseline_is_a_violation(tmp_path):
    manifest_data = {
        "changes": {
            "demo": {
                "eval_cases": [
                    {
                        "scenario_id": "banner-is-legible",
                        "capability": "console",
                        "surface": "e2e-visual",
                    }
                ]
            }
        }
    }
    found = surface.baseline_violations(manifest_data, tmp_path)
    assert any("banner-is-legible" in v for v in found)


def test_a_baseline_without_a_scenario_is_a_violation(tmp_path):
    visual = tmp_path / "openspec" / "specs" / "console" / "visual"
    visual.mkdir(parents=True)
    (visual / "ghost-baseline.console.png").write_bytes(b"png")
    found = surface.baseline_violations({"changes": {}}, tmp_path)
    assert any("ghost-baseline" in v for v in found)


def test_a_matched_visual_scenario_passes_both_ways(tmp_path):
    visual = tmp_path / "openspec" / "specs" / "console" / "visual"
    visual.mkdir(parents=True)
    (visual / "banner-is-legible.console.png").write_bytes(b"png")
    manifest_data = {
        "changes": {
            "demo": {
                "eval_cases": [
                    {
                        "scenario_id": "banner-is-legible",
                        "capability": "console",
                        "surface": "e2e-visual",
                    }
                ]
            }
        }
    }
    assert surface.baseline_violations(manifest_data, tmp_path) == []


def test_non_visual_scenarios_need_no_baseline(tmp_path):
    manifest_data = {
        "changes": {
            "demo": {
                "eval_cases": [
                    {
                        "scenario_id": "outage-keywords-route-to-on-call",
                        "capability": "ticket-triage",
                        "surface": "dspy-eval",
                    }
                ]
            }
        }
    }
    assert surface.baseline_violations(manifest_data, tmp_path) == []
