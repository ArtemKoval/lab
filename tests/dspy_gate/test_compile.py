"""Tests for the THEN-to-tier compiler: the constrained vocabulary,
the judge reference, the AND folding, and the refusal contract."""

import pytest

from dspy_gate import compile as compile_mod
from dspy_gate import scenarioparse


def make_scenario(thens, judged=False, rubric=None):
    return {
        "scenario_id": "demo-scenario",
        "title": "Demo scenario",
        "capability": "triage",
        "when": "a ticket arrives",
        "thens": thens,
        "surface": "dspy-eval",
        "judged": judged,
        "rubric": rubric,
        "source_hash": "abc1234567",
    }


def test_an_equality_then_compiles_to_tier_a():
    checks = compile_mod.compile_scenario(make_scenario(["severity = P0"]))
    assert checks == [{"tier": "A", "kind": "eq", "field": "severity", "value": "P0"}]


def test_a_quoted_value_loses_its_quotes():
    checks = compile_mod.compile_scenario(make_scenario(['team = "on-call"']))
    assert checks[0]["value"] == "on-call"


def test_a_membership_then_compiles_to_tier_a():
    checks = compile_mod.compile_scenario(
        make_scenario(["severity is one of P1, P2, P3"])
    )
    assert checks == [
        {"tier": "A", "kind": "in", "field": "severity", "values": ["P1", "P2", "P3"]}
    ]


def test_a_schema_then_compiles_to_tier_a():
    checks = compile_mod.compile_scenario(
        make_scenario(["the output carries the fields severity and team"])
    )
    assert checks == [
        {"tier": "A", "kind": "schema", "fields": ["severity", "team"]}
    ]


def test_a_tool_order_then_compiles_to_tier_c():
    checks = compile_mod.compile_scenario(
        make_scenario(["the escalate tool runs before the reply step"])
    )
    assert checks == [
        {"tier": "C", "kind": "call_order", "before": "escalate", "after": "reply"}
    ]


def test_a_judged_then_emits_the_rubric_reference_with_the_ensemble():
    checks = compile_mod.compile_scenario(
        make_scenario(["severity = P0"], judged=True, rubric="rubrics/escalation.md")
    )
    assert {"tier": "B", "kind": "judge", "rubric": "rubrics/escalation.md", "ensemble": 3} in checks
    assert {"tier": "A", "kind": "eq", "field": "severity", "value": "P0"} in checks


def test_an_inline_judge_tag_emits_the_rubric_reference():
    thens = ["the escalate tool runs before the reply step [judge: rubric = rubrics/escalation.md]"]
    checks = compile_mod.compile_scenario(make_scenario(thens))
    kinds = [c["kind"] for c in checks]
    assert kinds == ["call_order", "judge"]


def test_an_unformal_and_under_a_judged_then_folds_into_the_reference():
    thens = [
        "the escalate tool runs before the reply step [judge: rubric = rubrics/escalation.md]",
        "no customer-facing text exists before the escalation record",
    ]
    checks = compile_mod.compile_scenario(make_scenario(thens))
    assert len(checks) == 2
    assert checks[1]["kind"] == "judge"


def test_an_and_that_parses_becomes_its_own_tier_a_assertion():
    thens = ["severity = P0", "team = on-call"]
    checks = compile_mod.compile_scenario(make_scenario(thens))
    assert checks == [
        {"tier": "A", "kind": "eq", "field": "severity", "value": "P0"},
        {"tier": "A", "kind": "eq", "field": "team", "value": "on-call"},
    ]


def test_an_unformal_then_without_a_judge_is_refused():
    with pytest.raises(compile_mod.CompileError) as exc:
        compile_mod.compile_scenario(make_scenario(["the response should be helpful"]))
    assert "demo-scenario" in str(exc.value)
    assert "triage" in str(exc.value)


def test_the_pilot_escalation_scenario_compiles_to_order_and_judge():
    scenario = {
        "scenario_id": "escalation-happens-before-reply",
        "title": "Escalation happens before reply",
        "capability": "ticket-triage",
        "when": "a P0 ticket goes through the triage flow",
        "thens": [
            "the escalate tool runs before the reply step [judge: rubric = rubrics/escalation.md]",
            "no customer-facing text exists before the escalation record",
        ],
        "surface": "dspy-eval",
        "judged": True,
        "rubric": "rubrics/escalation.md",
        "source_hash": "abc1234567",
    }
    checks = compile_mod.compile_scenario(scenario)
    assert {"tier": "C", "kind": "call_order", "before": "escalate", "after": "reply"} in checks
    assert {"tier": "B", "kind": "judge", "rubric": "rubrics/escalation.md", "ensemble": 3} in checks
