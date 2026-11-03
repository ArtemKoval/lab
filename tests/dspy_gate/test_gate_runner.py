"""Tests for the gate runner: Tier D budgets, the delta and frozen
suite runs, the failure routes, and the conformance matrix."""

import json

from dspy_gate import checks, evals, matrix

BUDGET = {"p95_tokens_per_scenario": 100, "p95_latency_s": 5}


def test_tier_d_without_usage_is_green_and_reports_na():
    result = checks.run_tier_d(BUDGET, None)
    assert result.passed
    assert "n/a" in result.detail


def test_tier_d_within_the_ceilings_is_green():
    result = checks.run_tier_d(BUDGET, {"p95_tokens": 90, "p95_latency_s": 4})
    assert result.passed


def test_tier_d_names_the_token_ceiling_on_a_breach():
    result = checks.run_tier_d(BUDGET, {"p95_tokens": 200, "p95_latency_s": 4})
    assert not result.passed
    assert "p95_tokens_per_scenario" in result.detail
    assert "100" in result.detail


def test_tier_d_names_the_latency_ceiling_on_a_breach():
    result = checks.run_tier_d(BUDGET, {"p95_tokens": 10, "p95_latency_s": 9})
    assert not result.passed
    assert "p95_latency_s" in result.detail


def case(scenario_id="outage-keywords-route-to-on-call", capability="ticket-triage"):
    return {
        "scenario_id": scenario_id,
        "capability": capability,
        "surface": "dspy-eval",
        "runner": "dspy-eval",
        "gates": [2, 3],
        "checks": [
            {"tier": "A", "kind": "eq", "field": "severity", "value": "P0"},
            {"tier": "A", "kind": "eq", "field": "team", "value": "on-call"},
        ],
        "judged": False,
        "rubric": None,
        "source_hash": "abc1234567",
        "when": "the ticket text contains the phrase production down",
        "thens": ["severity = P0", "team = on-call"],
    }


def test_a_green_delta_suite_reports_every_scenario():
    report = evals.run_delta([case()], budget=BUDGET)
    assert report.exit == 0
    assert report.rows[0]["scenario_id"] == "outage-keywords-route-to-on-call"
    assert report.rows[0]["green"] is True


def test_a_red_tier_a_failure_routes_to_fix_the_harness():
    broken = case()
    broken["checks"][0]["value"] = "P3"
    report = evals.run_delta([broken], budget=BUDGET)
    assert report.exit == 2
    row = report.rows[0]
    assert row["green"] is False
    assert row["route"] == "fix the harness"
    assert "severity" in row["detail"]


def test_a_deferred_tier_b_keeps_the_suite_green_and_names_the_route():
    judged = case(scenario_id="escalation-happens-before-reply")
    judged["checks"] = [
        {"tier": "B", "kind": "judge", "rubric": "rubrics/escalation.md", "ensemble": 3}
    ]
    judged["judged"] = True
    report = evals.run_delta([judged], budget=BUDGET)
    assert report.exit == 0
    row = report.rows[0]
    assert row["deferred"] is True
    assert row["route"] == "re-optimize"


def test_a_budget_breach_routes_to_fix_the_harness():
    report = evals.run_delta([case()], budget=BUDGET, usage={"p95_tokens": 999})
    assert report.exit == 2
    assert report.rows[0]["route"] == "fix the harness"


def test_an_environment_error_routes_to_repair_the_environment():
    def boom(case):
        raise RuntimeError("provider unreachable")

    report = evals.run_delta([case()], budget=BUDGET, run_fn=boom)
    assert report.exit == 2
    assert report.rows[0]["route"] == "repair the environment"


def test_an_empty_frozen_suite_passes_with_a_zero_count():
    report = evals.run_frozen([], budget=BUDGET)
    assert report.exit == 0
    assert report.rows == []


def test_a_frozen_regression_is_red():
    broken = case()
    broken["checks"][0]["value"] = "P3"
    report = evals.run_frozen([broken], budget=BUDGET)
    assert report.exit == 2


def test_the_matrix_renders_rows_and_statuses():
    broken = case()
    broken["checks"][0]["value"] = "P3"
    report = evals.run_delta([case(), broken], budget=BUDGET)
    text = matrix.render(report)
    assert "| scenario | status | tier | route |" in text
    assert "outage-keywords-route-to-on-call" in text
    assert "green" in text and "red" in text
    assert "fix the harness" in text


def test_the_matrix_json_is_stable():
    report = evals.run_delta([case()], budget=BUDGET)
    first = matrix.to_json(report)
    second = matrix.to_json(report)
    assert json.loads(first) == json.loads(second)
