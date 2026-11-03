"""Tests for the nightly learning loop: the seven steps in order, the
triage classes, expansion, escalation drafts, and the safety rails."""

import json

from dspy_gate import nightly

MANIFEST = {
    "changes": {
        "demo": {
            "eval_cases": [
                {"scenario_id": "known-scenario", "capability": "ticket-triage",
                 "surface": "dspy-eval", "checks": []},
            ]
        }
    }
}


def row(scenario_id="known-scenario", detail="", green=False, route=""):
    return {
        "scenario_id": scenario_id,
        "capability": "ticket-triage",
        "green": green,
        "detail": detail,
        "route": route,
    }


def test_triage_classifies_the_four_kinds():
    failures = [
        row("known-scenario"),
        row("ghost-scenario"),
        row("env-scenario", detail="environment error: provider unreachable"),
        row("flaky-scenario"),
    ]
    classified = nightly.triage(failures, MANIFEST, known_flakes=("flaky-scenario",))
    kinds = {c["scenario_id"]: c["kind"] for c in classified}
    assert kinds == {
        "known-scenario": "eval gap",
        "ghost-scenario": "spec gap",
        "env-scenario": "environment rot",
        "flaky-scenario": "known flake",
    }


def test_the_loop_lists_the_seven_steps_in_order():
    report = nightly.run(
        [row("known-scenario")],
        manifest_data=MANIFEST,
        drafts_root=None,
        optimizer_fn=lambda program, train, val: program,
        run_fn=lambda case: ({"severity": "P0"}, []),
        budgets={"ticket-triage": {}},
        holdout_ratios={"ticket-triage": 0.3},
    )
    steps = [s["step"] for s in report["steps"]]
    assert steps == [
        "collect", "triage", "expand", "optimize", "certify", "promote", "escalate",
    ]


def test_the_loop_is_idempotent_across_runs(tmp_path):
    kwargs = dict(
        manifest_data=MANIFEST,
        drafts_root=tmp_path / "drafts",
        optimizer_fn=lambda program, train, val: program,
        run_fn=lambda case: ({"severity": "P0"}, []),
        budgets={"ticket-triage": {}},
        holdout_ratios={"ticket-triage": 0.3},
    )
    first = nightly.run([row("known-scenario")], **kwargs)
    second = nightly.run([row("known-scenario")], **kwargs)
    assert first == second


def test_expansion_grows_cases_only_for_eval_gaps():
    classified = [
        {"scenario_id": "known-scenario", "kind": "eval gap",
         "case": {"scenario_id": "known-scenario", "inputs": {"ticket": "production down"}}},
        {"scenario_id": "ghost-scenario", "kind": "spec gap"},
    ]
    derived = nightly.expand(classified)
    assert len(derived) == 1
    assert derived[0]["scenario_id"] == "known-scenario-expansion-1"


def test_a_recurring_spec_gap_drafts_a_change(tmp_path):
    classified = [{"scenario_id": "ghost-scenario", "kind": "spec gap"}]
    path = nightly.escalate(
        classified, drafts_root=tmp_path, occurrences={"ghost-scenario": 3}
    )
    draft = path / "proposal.md"
    assert draft.is_file()
    assert "ghost-scenario" in draft.read_text(encoding="utf-8")


def test_a_first_spec_gap_drafts_nothing(tmp_path):
    classified = [{"scenario_id": "ghost-scenario", "kind": "spec gap"}]
    path = nightly.escalate(
        classified, drafts_root=tmp_path, occurrences={"ghost-scenario": 1}
    )
    assert path is None


def test_the_draft_lands_under_the_drafts_root(tmp_path):
    specs = tmp_path / "specs"
    specs.mkdir()
    drafts = tmp_path / "drafts"
    classified = [{"scenario_id": "ghost-scenario", "kind": "spec gap"}]
    nightly.escalate(classified, drafts, occurrences={"ghost-scenario": 2})
    assert list(specs.iterdir()) == []
    assert (drafts / "ghost-scenario" / "proposal.md").is_file()


def test_promote_moves_the_pointer_and_keeps_the_previous(tmp_path):
    artifacts = tmp_path / "artifacts"
    (artifacts / "candidates" / "a").mkdir(parents=True)
    (artifacts / "candidates" / "a" / "pointer.json").write_text('{"v": 1}')
    current = nightly.promote(artifacts, "candidates/a")
    moved = json.loads((artifacts / "current.json").read_text())
    assert moved["source"] == "candidates/a"
    assert current["previous"] is None


def test_a_second_promotion_keeps_the_previous_pointer(tmp_path):
    artifacts = tmp_path / "artifacts"
    (artifacts / "candidates" / "a").mkdir(parents=True)
    (artifacts / "candidates" / "a" / "pointer.json").write_text('{"v": 1}')
    (artifacts / "candidates" / "b").mkdir(parents=True)
    (artifacts / "candidates" / "b" / "pointer.json").write_text('{"v": 2}')
    nightly.promote(artifacts, "candidates/a")
    result = nightly.promote(artifacts, "candidates/b")
    assert result["previous"] == "candidates/a"
    assert json.loads((artifacts / "previous.json").read_text())["source"] == "candidates/a"


def test_an_existing_draft_is_returned_as_is(tmp_path):
    classified = [{"scenario_id": "ghost-scenario", "kind": "spec gap"}]
    first = nightly.escalate(classified, tmp_path, {"ghost-scenario": 3})
    before = (first / "proposal.md").read_text(encoding="utf-8")
    second = nightly.escalate(classified, tmp_path, {"ghost-scenario": 3})
    assert second == first
    assert (first / "proposal.md").read_text(encoding="utf-8") == before


def case_payload(scenario_id):
    return {
        "scenario_id": scenario_id,
        "capability": "ticket-triage",
        "surface": "dspy-eval",
        "checks": [{"tier": "A", "kind": "eq", "field": "severity", "value": "P0"}],
    }


def test_the_loop_optimizes_and_promotes_a_green_candidate(tmp_path):
    rows = [
        {
            "scenario_id": "known-scenario",
            "capability": "ticket-triage",
            "green": False,
            "detail": "",
            "route": "",
            "case": case_payload(f"scenario-{i}"),
        }
        for i in range(3)
    ]
    report = nightly.run(
        rows,
        manifest_data=MANIFEST,
        drafts_root=tmp_path / "drafts",
        optimizer_fn=lambda program, train, val: program,
        run_fn=lambda case: ({"severity": "P0"}, []),
        budgets={},
        holdout_ratios={},
        artifacts_root=tmp_path / "artifacts",
    )
    outcomes = {s["step"]: s["outcome"] for s in report["steps"]}
    assert "ticket-triage" in outcomes["optimize"]
    assert "candidates/nightly" in outcomes["promote"]
    current = json.loads(
        ((tmp_path / "artifacts") / "current.json").read_text(encoding="utf-8")
    )
    assert current["source"] == "candidates/nightly"


def test_the_loop_records_a_split_refusal(tmp_path):
    rows = [
        {
            "scenario_id": "known-scenario",
            "capability": "ticket-triage",
            "green": False,
            "detail": "",
            "route": "",
            "case": case_payload("only-one"),
        }
    ]
    report = nightly.run(
        rows,
        manifest_data=MANIFEST,
        drafts_root=tmp_path / "drafts",
        optimizer_fn=lambda program, train, val: program,
        run_fn=lambda case: ({"severity": "P0"}, []),
        budgets={},
        holdout_ratios={},
    )
    outcomes = {s["step"]: s["outcome"] for s in report["steps"]}
    assert "not enough scenarios" in outcomes["optimize"]
