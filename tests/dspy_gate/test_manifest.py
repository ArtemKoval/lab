"""Tests for the manifest writer, the Gate 1 bidirectional verifier,
and the per-scenario dataset emitters."""

import json

from dspy_gate import datasets, manifest

CHANGE = {
    "change_id": "demo",
    "requirements": [
        {
            "name": "Triage assigns severity",
            "scenarios": [
                {
                    "scenario_id": "outage-routes-to-on-call",
                    "title": "Outage routes to on-call",
                    "capability": "ticket-triage",
                    "when": "the ticket text contains the phrase production down",
                    "thens": ["severity = P0", "team = on-call"],
                    "surface": "dspy-eval",
                    "judged": False,
                    "rubric": None,
                    "source_hash": "abc1234567",
                },
                {
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
                    "source_hash": "def2345678",
                },
            ],
        }
    ],
}

MODULES = {
    "ticket-triage": {
        "module": "Triage",
        "impl": "hand",
        "entry": "dspy_gate/harness/triage.py::triage",
        "examples": {"outage-routes-to-on-call": {"ticket": "production down"}},
    }
}


def built():
    return manifest.build(CHANGE, MODULES)


def test_build_records_every_scenario_as_an_eval_case():
    data = built()
    cases = data["changes"]["demo"]["eval_cases"]
    assert [c["scenario_id"] for c in cases] == [
        "outage-routes-to-on-call",
        "escalation-happens-before-reply",
    ]


def test_build_carries_capability_surface_and_checks():
    case = built()["changes"]["demo"]["eval_cases"][0]
    assert case["capability"] == "ticket-triage"
    assert case["surface"] == "dspy-eval"
    assert case["gates"] == [2, 3]
    assert {"tier": "A", "kind": "eq", "field": "severity", "value": "P0"} in case["checks"]


def test_build_annotates_the_judged_case_with_the_rubric():
    case = built()["changes"]["demo"]["eval_cases"][1]
    judge = [c for c in case["checks"] if c["tier"] == "B"]
    assert judge == [
        {"tier": "B", "kind": "judge", "rubric": "rubrics/escalation.md", "ensemble": 3}
    ]


def test_build_lists_the_module_with_impl():
    data = built()
    module = data["changes"]["demo"]["modules"][0]
    assert module["module"] == "Triage"
    assert module["impl"] == "hand"
    assert module["entry"] == "dspy_gate/harness/triage.py::triage"
    assert module["scenarios"] == [
        "outage-routes-to-on-call",
        "escalation-happens-before-reply",
    ]


def test_the_manifest_starts_with_the_generated_marker():
    data = built()
    assert data["_generated"].startswith("GENERATED")


def test_write_and_load_round_trip(tmp_path):
    path = tmp_path / "eval_manifest.json"
    manifest.write(built(), path)
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["changes"]["demo"]["eval_cases"][0]["scenario_id"] == (
        "outage-routes-to-on-call"
    )


def test_verify_passes_on_full_coverage_both_ways():
    assert manifest.verify(built(), CHANGE, MODULES) == []


def test_verify_names_an_orphan_case():
    data = built()
    data["changes"]["demo"]["eval_cases"].append(
        {"scenario_id": "ghost-scenario", "capability": "ticket-triage"}
    )
    found = manifest.verify(data, CHANGE, MODULES)
    assert any("ghost-scenario" in v for v in found)


def test_verify_names_a_missing_case():
    parsed = {"change_id": "demo", "requirements": [dict(CHANGE["requirements"][0])]}
    parsed["requirements"][0]["scenarios"] = [
        dict(CHANGE["requirements"][0]["scenarios"][0]),
        dict(CHANGE["requirements"][0]["scenarios"][1]),
        {
            "scenario_id": "uncovered-scenario",
            "capability": "ticket-triage",
            "surface": "dspy-eval",
        },
    ]
    found = manifest.verify(built(), parsed, MODULES)
    assert any("uncovered-scenario" in v for v in found)


def test_an_unregistered_capability_is_skipped():
    parsed = {
        "change_id": "demo",
        "requirements": [
            {
                "name": "Machinery",
                "scenarios": [
                    {
                        "scenario_id": "infra-behaves",
                        "capability": "spec-bridge",
                        "surface": None,
                        "judged": False,
                        "rubric": None,
                        "when": "the bridge runs",
                        "thens": ["the command exits 0"],
                        "source_hash": "aaa1111111",
                    }
                ],
            }
        ],
    }
    data = manifest.build(parsed, MODULES)
    assert data["changes"]["demo"]["eval_cases"] == []


def test_dataset_write_carries_inputs_and_expected(tmp_path):
    case = built()["changes"]["demo"]["eval_cases"][0]
    path = datasets.write_case(tmp_path, case, MODULES)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["scenario_id"] == "outage-routes-to-on-call"
    assert data["inputs"] == {"ticket": "production down"}
    assert data["expected"]["checks"] == case["checks"]


def test_dataset_write_falls_back_to_the_when_text(tmp_path):
    case = built()["changes"]["demo"]["eval_cases"][1]
    path = datasets.write_case(tmp_path, case, MODULES)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["inputs"] == {"when": "a P0 ticket goes through the triage flow"}
