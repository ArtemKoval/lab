"""Tests for the Gate 2 runner: the holdout split, certification on
held-out scenarios, the artifact write contract, and the loop bound."""

import json

import pytest

from dspy_gate import optimize


def cases(n):
    return [
        {
            "scenario_id": f"scenario-{i}",
            "capability": "ticket-triage",
            "surface": "dspy-eval",
            "checks": [
                {"tier": "A", "kind": "eq", "field": "severity", "value": "P0"}
            ],
        }
        for i in range(n)
    ]


def green_runner(cases_seen):
    def run(case):
        return {"severity": "P0"}, [{"tool": "escalate"}, {"step": "reply"}]

    return run


def red_runner(cases_seen):
    def run(case):
        return {"severity": "P3"}, []

    return run


def test_the_split_rounds_the_holdout_up_with_a_floor_of_one():
    train, val, heldout = optimize.split(cases(4), 0.3)
    assert len(heldout) == 2
    assert len(train) == 1
    assert len(val) == 1


def test_the_split_hides_the_heldout_ids_from_train_and_val():
    train, val, heldout = optimize.split(cases(10), 0.3)
    held_ids = {c["scenario_id"] for c in heldout}
    rest_ids = {c["scenario_id"] for c in train + val}
    assert not held_ids & rest_ids
    assert len(heldout) == 3


def test_the_split_is_deterministic():
    first = optimize.split(cases(10), 0.3)
    second = optimize.split(cases(10), 0.3)
    assert first == second


def test_a_tiny_case_set_is_refused():
    with pytest.raises(optimize.OptimizeError) as exc:
        optimize.split(cases(1), 0.3)
    assert "not enough scenarios" in str(exc.value)


def test_a_green_candidate_writes_artifacts(tmp_path):
    result = optimize.run(
        cases(4),
        holdout_ratio=0.3,
        artifacts_dir=tmp_path / "artifacts" / "demo",
        run_fn=green_runner(None),
        optimizer_fn=lambda program, train, val: program,
    )
    assert result.exit == 0
    pointer = tmp_path / "artifacts" / "demo" / "pointer.json"
    assert pointer.is_file()
    assert json.loads(pointer.read_text(encoding="utf-8"))["scenarios"] == 4


def test_a_red_candidate_writes_nothing(tmp_path):
    result = optimize.run(
        cases(4),
        holdout_ratio=0.3,
        artifacts_dir=tmp_path / "artifacts" / "demo",
        run_fn=red_runner(None),
        optimizer_fn=lambda program, train, val: program,
    )
    assert result.exit == 2
    assert not (tmp_path / "artifacts" / "demo" / "pointer.json").exists()


def test_the_optimizer_never_sees_the_heldout_ids(tmp_path):
    seen = {}

    def optimizer_fn(program, train, val):
        seen["ids"] = {c["scenario_id"] for c in train + val}
        return program

    optimize.run(
        cases(4),
        holdout_ratio=0.3,
        artifacts_dir=tmp_path,
        run_fn=green_runner(None),
        optimizer_fn=optimizer_fn,
    )
    _, _, heldout = optimize.split(cases(4), 0.3)
    held_ids = {c["scenario_id"] for c in heldout}
    assert not seen["ids"] & held_ids


def test_the_loop_bound_stops_the_retry(tmp_path):
    attempts = []

    def optimizer_fn(program, train, val):
        attempts.append(len(attempts))
        return program

    result = optimize.run(
        cases(4),
        holdout_ratio=0.3,
        artifacts_dir=tmp_path,
        run_fn=red_runner(None),
        optimizer_fn=optimizer_fn,
        max_loops=2,
    )
    assert result.exit == 2
    assert len(attempts) == 2
