"""Tests for the Gate 0 linter: testable-or-reject, surface tags,
rubric existence, policy bounds, and the openspec validate pass."""

import textwrap

from dspy_gate import gatepolicy, lint

CLEAN = """
    ## ADDED Requirements

    ### Requirement: Triage assigns severity

    #### Scenario: Outage routes to on-call [surface: dspy-eval]
    - **WHEN** the ticket text contains the phrase production down
    - **THEN** severity = P0

    #### Scenario: Judged escalation [surface: dspy-eval, judge]
    - **WHEN** a P0 ticket is processed
    - **THEN** the escalate tool runs before the reply step [judge: rubric = rubrics/escalation.md]
    """

POLICY = """
    version: 1
    policy_bounds:
      tier_b_min: { min: 0.60, max: 1.00 }
    """

GATES_OK = """
    version: 1
    capabilities:
      triage:
        gate_2: { tier_a: 1.00, tier_b_min: 0.80 }
    """

GATES_BAD = """
    version: 1
    capabilities:
      triage:
        gate_2: { tier_a: 1.00, tier_b_min: 0.10 }
    """

VAGUE = """
    ## ADDED Requirements

    ### Requirement: The reply is good

    #### Scenario: The reply is good [surface: dspy-eval]
    - **WHEN** a ticket is processed
    - **THEN** the response should be helpful
    """

NO_SURFACE = CLEAN.replace("[surface: dspy-eval]", "")
BAD_SURFACE = CLEAN.replace("[surface: dspy-eval]", "[surface: e2e-print]", 1)
DANGLING = CLEAN.replace("rubrics/escalation.md", "rubrics/missing.md")
NO_SCENARIO = CLEAN + """
    ### Requirement: Empty requirement
    """


def make_change(tmp_path, spec_text=CLEAN, gates_text=None):
    specs = tmp_path / "openspec" / "changes" / "demo" / "specs" / "triage"
    specs.mkdir(parents=True)
    (specs / "spec.md").write_text(textwrap.dedent(spec_text), encoding="utf-8")
    if gates_text:
        (tmp_path / "openspec" / "changes" / "demo" / "gates.yaml").write_text(
            textwrap.dedent(gates_text), encoding="utf-8"
        )
    rubrics = tmp_path / "openspec" / "changes" / "demo" / "rubrics"
    rubrics.mkdir(parents=True)
    (rubrics / "escalation.md").write_text("# rubric\n", encoding="utf-8")
    return tmp_path / "openspec" / "changes" / "demo"


def make_policy(tmp_path):
    path = tmp_path / "policy.yaml"
    path.write_text(textwrap.dedent(POLICY), encoding="utf-8")
    return gatepolicy.load(path)


def fake_validate(ok=True):
    def run(change_dir):
        return ok, "" if ok else "structural error"

    return run


def registry():
    return {"triage": {"module": "Triage", "impl": "hand"}}


def test_a_clean_change_has_no_violations(tmp_path):
    change = make_change(tmp_path, gates_text=GATES_OK)
    found = lint.lint_change(change, make_policy(tmp_path), registry(), validate=fake_validate())
    assert found == []


def test_a_failed_openspec_validate_is_a_violation(tmp_path):
    change = make_change(tmp_path)
    found = lint.lint_change(change, make_policy(tmp_path), validate=fake_validate(False))
    assert any("openspec validate" in v for v in found)


def test_a_requirement_without_a_scenario_is_a_violation(tmp_path):
    change = make_change(tmp_path, spec_text=NO_SCENARIO)
    found = lint.lint_change(change, make_policy(tmp_path), registry(), validate=fake_validate())
    assert any("no scenario" in v for v in found)


def test_a_vague_then_is_a_violation(tmp_path):
    change = make_change(tmp_path, spec_text=VAGUE)
    found = lint.lint_change(change, make_policy(tmp_path), registry(), validate=fake_validate())
    assert any("Uncompilable THEN" in v for v in found)


def test_a_missing_surface_tag_is_a_violation(tmp_path):
    change = make_change(tmp_path, spec_text=NO_SURFACE)
    found = lint.lint_change(change, make_policy(tmp_path), registry(), validate=fake_validate())
    assert any("no surface tag" in v for v in found)


def test_an_unknown_surface_value_is_a_violation(tmp_path):
    change = make_change(tmp_path, spec_text=BAD_SURFACE)
    found = lint.lint_change(change, make_policy(tmp_path), registry(), validate=fake_validate())
    assert any("unknown surface" in v for v in found)


def test_a_dangling_rubric_is_a_violation(tmp_path):
    change = make_change(tmp_path, spec_text=DANGLING)
    found = lint.lint_change(change, make_policy(tmp_path), registry(), validate=fake_validate())
    assert any("rubrics/missing.md" in v for v in found)


def test_an_out_of_bounds_threshold_is_a_violation(tmp_path):
    change = make_change(tmp_path, gates_text=GATES_BAD)
    found = lint.lint_change(change, make_policy(tmp_path), registry(), validate=fake_validate())
    assert any("outside policy bounds" in v for v in found)


def test_a_change_without_gates_yaml_passes_the_bounds_rule(tmp_path):
    change = make_change(tmp_path)
    found = lint.lint_change(change, make_policy(tmp_path), registry(), validate=fake_validate())
    assert found == []
