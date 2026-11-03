"""Tests for the Gate 4 freeze: eval cases, baselines, and the
capability thresholds freeze beside the spec at archive time."""

import json

import pytest

from dspy_gate import freeze

CASE = {
    "_generated": "GENERATED",
    "scenario_id": "outage-keywords-route-to-on-call",
    "inputs": {"ticket": "production down"},
    "expected": {"checks": [{"tier": "A", "kind": "eq", "field": "severity", "value": "P0"}]},
}

GATES = """
version: 1

capabilities:
  ticket-triage:
    gate_2: { tier_a: 1.00, tier_b_min: 0.80, flake_budget: 2, max_optimize_loops: 3 }
    budget: { p95_tokens_per_scenario: 2500 }
    holdout_ratio: 0.3
"""


@pytest.fixture()
def repo(tmp_path):
    change = tmp_path / "openspec" / "changes" / "demo"
    evals = change / "evals" / "ticket-triage"
    evals.mkdir(parents=True)
    (evals / "outage-keywords-route-to-on-call.json").write_text(
        json.dumps(CASE, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (change / "gates.yaml").write_text(GATES, encoding="utf-8")
    manifest = {"changes": {"demo": {"eval_cases": [
        {"scenario_id": "outage-keywords-route-to-on-call",
         "capability": "ticket-triage", "surface": "dspy-eval"}
    ]}}}
    (tmp_path / "openspec" / "eval_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return tmp_path


def test_the_freeze_copies_the_eval_cases(repo):
    freeze.run(repo, "demo")
    frozen = repo / "openspec" / "specs" / "ticket-triage" / "evals"
    assert (frozen / "outage-keywords-route-to-on-call.json").is_file()


def test_the_freeze_is_idempotent(repo):
    freeze.run(repo, "demo")
    frozen = repo / "openspec" / "specs" / "ticket-triage" / "evals"
    first = (frozen / "outage-keywords-route-to-on-call.json").read_bytes()
    freeze.run(repo, "demo")
    second = (frozen / "outage-keywords-route-to-on-call.json").read_bytes()
    assert first == second


def test_the_freeze_writes_the_capability_thresholds(repo):
    freeze.run(repo, "demo")
    path = repo / "openspec" / "specs" / "ticket-triage" / "gates.yaml"
    text = path.read_text(encoding="utf-8")
    assert "ticket-triage:" in text
    assert "tier_b_min" in text


def test_the_freeze_reports_the_frozen_counts(repo):
    report = freeze.run(repo, "demo")
    assert report == {"ticket-triage": {"evals": 1, "gates": True}}
