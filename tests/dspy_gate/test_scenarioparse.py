"""Tests for the scenario parser: heading tags, WHEN/THEN extraction,
stable slugs, source hashes, requirement grouping, and the refusal
contract for an unparseable scenario."""

import hashlib
import textwrap

import pytest

from dspy_gate import scenarioparse


def write_change(root, capability="triage", spec_text=""):
    specs = root / "openspec" / "changes" / "demo" / "specs" / capability
    specs.mkdir(parents=True)
    (specs / "spec.md").write_text(textwrap.dedent(spec_text), encoding="utf-8")
    return root / "openspec" / "changes" / "demo"


SPEC = """
    ## ADDED Requirements

    ### Requirement: Triage assigns severity

    #### Scenario: Outage routes to on-call [surface: dspy-eval]
    - **WHEN** the ticket text contains the phrase production down
    - **THEN** severity = P0
    - **AND** team = on-call

    #### Scenario: Escalation comes first [surface: dspy-eval, judge]
    - **WHEN** a P0 ticket is processed
    - **THEN** the escalate tool runs before the reply step [judge: rubric = rubrics/escalation.md]
    """


def test_a_tagged_scenario_yields_surface_and_when_and_thens(tmp_path):
    change_dir = write_change(tmp_path, spec_text=SPEC)
    data = scenarioparse.parse_change(change_dir)
    first = data["requirements"][0]["scenarios"][0]
    assert first["surface"] == "dspy-eval"
    assert first["when"] == "the ticket text contains the phrase production down"
    assert first["thens"] == ["severity = P0", "team = on-call"]


def test_a_judge_tag_marks_the_scenario_and_carries_the_rubric(tmp_path):
    change_dir = write_change(tmp_path, spec_text=SPEC)
    data = scenarioparse.parse_change(change_dir)
    judged = data["requirements"][0]["scenarios"][1]
    assert judged["judged"] is True
    assert judged["rubric"] == "rubrics/escalation.md"


def test_the_capability_comes_from_the_spec_directory_name(tmp_path):
    change_dir = write_change(tmp_path, capability="ticket-triage", spec_text=SPEC)
    data = scenarioparse.parse_change(change_dir)
    assert data["requirements"][0]["scenarios"][0]["capability"] == "ticket-triage"


def test_the_slug_is_lowercase_kebab_and_capped_at_60(tmp_path):
    change_dir = write_change(tmp_path, spec_text=SPEC)
    data = scenarioparse.parse_change(change_dir)
    slug = data["requirements"][0]["scenarios"][0]["scenario_id"]
    assert slug == "outage-routes-to-on-call"
    assert len(slug) <= 60


def test_the_source_hash_is_stable_across_runs(tmp_path):
    change_dir = write_change(tmp_path, spec_text=SPEC)
    first = scenarioparse.parse_change(change_dir)
    second = scenarioparse.parse_change(change_dir)
    a = first["requirements"][0]["scenarios"][0]["source_hash"]
    b = second["requirements"][0]["scenarios"][0]["source_hash"]
    assert a == b and len(a) == 10


def test_the_source_hash_covers_the_whole_scenario_block(tmp_path):
    change_dir = write_change(tmp_path, spec_text=SPEC)
    data = scenarioparse.parse_change(change_dir)
    match = next(scenarioparse.SCENARIO_RE.finditer(textwrap.dedent(SPEC)))
    expected = hashlib.sha1(match.group(0).encode()).hexdigest()[:10]
    assert data["requirements"][0]["scenarios"][0]["source_hash"] == expected


def test_a_scenario_without_when_is_refused(tmp_path):
    bad = SPEC.replace("- **WHEN** the ticket text contains", "- **GIVEN** the text contains")
    change_dir = write_change(tmp_path, spec_text=bad)
    with pytest.raises(scenarioparse.ScenarioParseError) as exc:
        scenarioparse.parse_change(change_dir)
    assert "Outage routes to on-call" in str(exc.value)


def test_a_scenario_without_then_is_refused(tmp_path):
    bad = SPEC.replace(
        "- **THEN** severity = P0", "- **RESULT** severity = P0"
    ).replace("- **AND** team = on-call", "")
    change_dir = write_change(tmp_path, spec_text=bad)
    with pytest.raises(scenarioparse.ScenarioParseError):
        scenarioparse.parse_change(change_dir)


def test_a_change_without_scenarios_is_refused(tmp_path):
    change_dir = write_change(tmp_path, spec_text="## ADDED Requirements\n")
    with pytest.raises(scenarioparse.ScenarioParseError) as exc:
        scenarioparse.parse_change(change_dir)
    assert "demo" in str(exc.value)


def test_requirement_names_group_their_scenarios(tmp_path):
    change_dir = write_change(tmp_path, spec_text=SPEC)
    data = scenarioparse.parse_change(change_dir)
    assert data["requirements"][0]["name"] == "Triage assigns severity"
    assert len(data["requirements"][0]["scenarios"]) == 2


def test_specs_are_walked_in_sorted_order(tmp_path):
    change_dir = write_change(tmp_path, capability="aaa-first", spec_text=SPEC)
    write_change(tmp_path, capability="zzz-second", spec_text=SPEC)
    data = scenarioparse.parse_change(change_dir)
    caps = [s["capability"] for r in data["requirements"] for s in r["scenarios"]]
    assert caps == sorted(caps)
    assert "aaa-first" in caps and "zzz-second" in caps
