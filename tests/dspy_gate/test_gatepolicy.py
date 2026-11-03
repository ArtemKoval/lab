"""Tests for the gates.yaml policy reader: load, role pins, and the
policy bounds that Gate 0 enforces on change thresholds."""

import textwrap

import pytest

from dspy_gate import gatepolicy

POLICY = """
    version: 1

    models:
      provider: zai
      roles:
        runtime: { model: glm-5.3-flash, temperature: 0.2, thinking: disabled, max_tokens: 8192 }
        judge:   { model: glm-5.3-flash, temperature: 0.0, thinking: disabled, max_tokens: 4096 }

    policy_bounds:
      tier_b_min: { min: 0.60, max: 1.00 }
      holdout_ratio: { min: 0.10, max: 0.50 }
      judge_ensemble: { min: 1, max: 5 }

    capabilities:
      ticket-triage:
        gate_2: { tier_a: 1.00, tier_b_min: 0.80 }
        holdout_ratio: 0.3
    """

CHANGE_GATES = """
    version: 1

    capabilities:
      ticket-triage:
        gate_2: { tier_a: 1.00, tier_b_min: 0.90, flake_budget: 2, max_optimize_loops: 3 }
        holdout_ratio: 0.3
        gate_5: { judge_ensemble: 3 }
    """

OUT_OF_BOUNDS = """
    version: 1

    capabilities:
      ticket-triage:
        gate_2: { tier_a: 1.00, tier_b_min: 0.40 }
        holdout_ratio: 0.9
        gate_5: { judge_ensemble: 9 }
    """


@pytest.fixture(scope="module")
def policy(tmp_path_factory):
    path = tmp_path_factory.mktemp("policy") / "gates.yaml"
    path.write_text(textwrap.dedent(POLICY), encoding="utf-8")
    return gatepolicy.load(path)


def test_load_reads_the_policy_sections(policy):
    assert policy["version"] == 1
    assert policy["models"]["provider"] == "zai"
    assert policy["capabilities"]["ticket-triage"]["holdout_ratio"] == 0.3


def test_roles_returns_the_pin_map(policy):
    roles = gatepolicy.roles(policy)
    assert roles["runtime"]["model"] == "glm-5.3-flash"
    assert roles["judge"]["thinking"] == "disabled"


def test_threshold_in_bounds_holds_at_both_edges(policy):
    assert gatepolicy.threshold_in_bounds(policy, "tier_b_min", 0.60)
    assert gatepolicy.threshold_in_bounds(policy, "tier_b_min", 1.00)
    assert not gatepolicy.threshold_in_bounds(policy, "tier_b_min", 0.59)
    assert not gatepolicy.threshold_in_bounds(policy, "tier_b_min", 1.01)


def test_threshold_in_bounds_is_true_for_an_unknown_name(policy):
    assert gatepolicy.threshold_in_bounds(policy, "flake_budget", 2)


def test_a_clean_change_gates_has_no_violations(policy, tmp_path):
    path = tmp_path / "gates.yaml"
    path.write_text(textwrap.dedent(CHANGE_GATES), encoding="utf-8")
    assert gatepolicy.violations(policy, gatepolicy.load(path)) == []


def test_out_of_bounds_thresholds_are_named(policy, tmp_path):
    path = tmp_path / "gates.yaml"
    path.write_text(textwrap.dedent(OUT_OF_BOUNDS), encoding="utf-8")
    found = gatepolicy.violations(policy, gatepolicy.load(path))
    assert len(found) == 3
    assert any("tier_b_min" in v for v in found)
    assert any("holdout_ratio" in v for v in found)
    assert any("judge_ensemble" in v for v in found)
