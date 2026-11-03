"""Boundary and exact-value tests that kill the mutation survivors:
edge positions, exact scores and counts, key ordering, and default
values. One mutant class per test."""

import json
from pathlib import Path

import pytest

from dspy_gate import bank, certs, checks, judge, matrix, scenarioparse


def test_bank_write_twice_to_the_same_store(tmp_path):
    path = tmp_path / "bank.jsonl"
    entry = {"scenario_id": "s", "gate_verdicts": {"A": True}}
    assert bank.write(path, entry) is True
    assert bank.write(path, entry) is True
    assert len(bank.read_all(path)) == 2


def test_bank_write_text_is_sorted_json_with_a_trailing_newline(tmp_path):
    path = tmp_path / "bank.jsonl"
    bank.write(path, {"scenario_id": "s", "verdicts": {}, "gate_verdicts": {"A": True}})
    line = path.read_text(encoding="utf-8")
    assert line.endswith("\n")
    assert line.index('"gate_verdicts"') < line.index('"scenario_id"')


def test_evict_returns_the_removed_count(tmp_path):
    path = tmp_path / "bank.jsonl"
    bank.write(path, {"scenario_id": "s", "gate_verdicts": {"A": True}})
    assert bank.evict(path, "s") == 1
    assert bank.evict(path, "s") == 0


def test_retrieve_orders_by_overlap_score(tmp_path):
    path = tmp_path / "bank.jsonl"
    bank.write(
        path,
        {
            "scenario_id": "noise",
            "inputs": {"ticket": "completely unrelated words"},
            "prediction": {"team": "general"},
            "gate_verdicts": {"A": True},
        },
    )
    bank.write(
        path,
        {
            "scenario_id": "match",
            "inputs": {"ticket": "sudden production down event"},
            "prediction": {"team": "on-call"},
            "gate_verdicts": {"A": True},
        },
    )
    hits = bank.retrieve(path, "production down", k=2)
    assert [h["scenario_id"] for h in hits] == ["match", "noise"]


def test_tier_c_fails_when_both_positions_tie():
    trace = [{"tool": "escalate", "step": "reply"}]
    result = checks.run_tier_c(
        [{"tier": "C", "kind": "call_order", "before": "escalate", "after": "reply"}],
        trace,
    )
    assert not result.passed


def test_tier_d_is_green_at_the_exact_token_ceiling():
    result = checks.run_tier_d({"p95_tokens_per_scenario": 100}, {"p95_tokens": 100})
    assert result.passed


def test_tier_d_is_green_at_the_exact_latency_ceiling():
    result = checks.run_tier_d({"p95_latency_s": 5}, {"p95_latency_s": 5})
    assert result.passed


def test_certify_digest_ignores_role_order():
    a = "models:\n  roles:\n    runtime: {model: m}\n    judge: {model: j}\n"
    b = "models:\n  roles:\n    judge: {model: j}\n    runtime: {model: m}\n"
    assert certs.pins_digest(a) == certs.pins_digest(b)


def test_record_defaults_to_green(tmp_path):
    path = tmp_path / "certs" / "triage.jsonl"
    certs.record(path, pins="p", source="s")
    rows = certs.read_rows(path)
    assert rows[0]["green"] is True


def test_record_twice_and_the_line_order_is_sorted(tmp_path):
    path = tmp_path / "certs" / "triage.jsonl"
    certs.record(path, pins="p1", source="s")
    certs.record(path, pins="p2", source="s")
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert lines[0].startswith('{"green"')


def test_drift_reads_the_last_row_not_the_first(tmp_path):
    path = tmp_path / "certs" / "triage.jsonl"
    current = certs.pins_digest("models:\n  roles: {}\n")
    certs.record(path, pins="stale", source="s")
    certs.record(path, pins=current, source="s")
    assert certs.drift(path, current) == []


def test_status_defers_only_tier_b_cases(tmp_path, capsys, monkeypatch):
    from test_gate_cli import make_repo, run
    import json

    root = make_repo(tmp_path)
    run(["regen", "demo"], root, monkeypatch)
    capsys.readouterr()
    run(["--json", "status", "demo"], root, monkeypatch)
    payload = json.loads(capsys.readouterr().out)
    for row in payload["rows"]:
        assert row["deferred"] is False


def test_status_reports_a_failing_tier_a_row_green_false(tmp_path, capsys, monkeypatch):
    from test_gate_cli import make_repo, run
    import json

    root = make_repo(tmp_path)
    run(["regen", "demo"], root, monkeypatch)
    capsys.readouterr()
    dataset = (
        root / "openspec" / "changes" / "demo" / "evals" / "triage"
        / "outage-routes-to-on-call.json"
    )
    manifest = root / "openspec" / "eval_manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["changes"]["demo"]["eval_cases"][0]["checks"][0]["value"] = "P9"
    manifest.write_text(json.dumps(data), encoding="utf-8")
    run(["--json", "status", "demo"], root, monkeypatch)
    payload = json.loads(capsys.readouterr().out)
    row = payload["rows"][0]
    assert row["green"] is False
    assert row["deferred"] is False


def test_evals_json_prints_sorted_keys(tmp_path, capsys, monkeypatch):
    from test_gate_cli import make_repo, run

    root = make_repo(tmp_path)
    run(["regen", "demo"], root, monkeypatch)
    capsys.readouterr()
    run(["--json", "evals", "demo"], root, monkeypatch)
    out = capsys.readouterr().out
    assert out.startswith('{"exit":')
    assert out.index('"exit"') < out.index('"report"')


def test_budget_of_returns_the_default_for_a_missing_capability():
    from test_gate_cli import run  # noqa: F401
    from dspy_gate import cli

    case = {"capability": "absent-cap"}
    assert cli.budget_of({}, case) == {}


def test_certify_groups_rows_by_their_own_capability(tmp_path, capsys, monkeypatch):
    from test_gate_cli import make_repo, run
    from dspy_gate import cli, certs

    root = make_repo(tmp_path)
    run(["regen", "demo"], root, monkeypatch)
    manifest = root / "openspec" / "eval_manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    cases = data["changes"]["demo"]["eval_cases"]
    other = dict(cases[0])
    other["scenario_id"] = "other-cap-scenario"
    other["capability"] = "other-cap"
    other["dataset_path"] = "evals/other-cap/other.json"
    other["checks"] = [
        {"tier": "A", "kind": "eq", "field": "severity", "value": "WRONG"}
    ]
    cases.append(other)
    manifest.write_text(json.dumps(data), encoding="utf-8")
    assert run(["certify", "demo"], root, monkeypatch) == 2
    good = certs.read_rows(certs.ledger_path(root, "triage"))[-1]
    bad = certs.read_rows(certs.ledger_path(root, "other-cap"))[-1]
    assert good["green"] is True
    assert bad["green"] is False


def test_a_red_delta_run_makes_certify_exit_two(tmp_path, capsys, monkeypatch):
    from test_gate_cli import make_repo, run

    root = make_repo(
        tmp_path,
        spec_text=(
            "## ADDED Requirements\n\n### Requirement: Triage\n\n"
            "#### Scenario: Outage [surface: dspy-eval]\n"
            "- **WHEN** the ticket arrives\n- **THEN** severity = P9\n"
        ),
    )
    run(["regen", "demo"], root, monkeypatch)
    capsys.readouterr()
    assert run(["certify", "demo"], root, monkeypatch) == 2


def test_the_parser_requires_a_command(tmp_path):
    from test_gate_cli import run

    assert run([], tmp_path) == 2


def test_the_parser_requires_the_nightly_report(tmp_path):
    from test_gate_cli import run

    assert run(["nightly", "demo"], tmp_path) == 2


def test_codegen_sorts_the_baked_dict_keys():
    from dspy_gate import codegen, manifest

    from test_manifest import CHANGE, MODULES

    text = codegen.generate(manifest.build(CHANGE, MODULES))
    assert text.index("'capability'") < text.index("'scenario_id'")
    assert text.index("'checks'") < text.index("'scenario_id'")


def test_the_dataset_record_carries_the_generated_marker(tmp_path):
    from dspy_gate import datasets, manifest

    from test_manifest import CHANGE, MODULES

    case = manifest.build(CHANGE, MODULES)["changes"]["demo"]["eval_cases"][0]
    path = datasets.write_case(tmp_path, case, MODULES)
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["_generated"].startswith("GENERATED")


def test_the_freeze_writes_sorted_yaml_without_a_version_default(tmp_path):
    from dspy_gate import freeze

    change = tmp_path / "openspec" / "changes" / "demo" / "evals" / "triage"
    change.mkdir(parents=True)
    (change / "s.json").write_text("{}", encoding="utf-8")
    (tmp_path / "openspec").mkdir(parents=True, exist_ok=True)
    (tmp_path / "openspec" / "eval_manifest.json").write_text(json.dumps({
        "changes": {"demo": {"eval_cases": [
            {"scenario_id": "s", "capability": "triage", "surface": "dspy-eval"}
        ]}}
    }))
    (tmp_path / "openspec" / "changes" / "demo" / "gates.yaml").write_text(
        "capabilities:\n  triage:\n    gate_2: {tier_a: 1.0}\n",
        encoding="utf-8",
    )
    freeze.run(tmp_path, "demo")
    text = (
        (tmp_path / "openspec" / "specs" / "triage" / "gates.yaml")
        .read_text(encoding="utf-8")
    )
    assert text.index("capabilities:") < text.index("version:")
    assert "version: 1" in text


def test_the_preview_thread_is_a_daemon():
    from dspy_gate.harness import preview

    server = preview.start_server(port=0)
    try:
        assert server.thread.daemon is True
    finally:
        server.shutdown()


def test_the_judge_passes_a_mean_equal_to_the_threshold():
    scores = iter([1.0, 0.6])
    result = judge.judge_case(
        {
            "rubric": "r.md",
            "checks": [{"tier": "B", "kind": "judge", "ensemble": 2}],
        },
        lambda case: next(scores),
        threshold=0.8,
    )
    assert result.passed


def test_a_half_vote_counts_in_a_one_vote_ensemble():
    scores = iter([0.5])
    assert judge.visual_gate({}, lambda case: next(scores), votes=1) is True


def test_a_tied_visual_vote_fails():
    scores = iter([1.0, 0.0])
    assert judge.visual_gate({}, lambda case: next(scores), votes=2) is False


def test_the_manifest_build_pins_version_one():
    from dspy_gate import manifest

    from test_manifest import CHANGE, MODULES

    assert manifest.build(CHANGE, MODULES)["version"] == 1


def test_stable_json_sorts_keys(tmp_path):
    from dspy_gate import manifest

    path = tmp_path / "m.json"
    manifest.write({"version": 1, "changes": {}}, path)
    text = path.read_text(encoding="utf-8")
    assert text.index('"changes"') < text.index('"version"')
    manifest.write({"version": 1, "changes": {}}, path)


def test_the_matrix_json_sorts_keys():
    from dspy_gate import evals, matrix

    text = matrix.to_json(evals.Report(0, []))
    assert text.index('"exit"') < text.index('"rows"')


def test_escalate_drafts_at_exactly_the_threshold(tmp_path):
    from dspy_gate import nightly

    classified = [{"scenario_id": "ghost-scenario", "kind": "spec gap"}]
    path = nightly.escalate(classified, tmp_path, {"ghost-scenario": 2})
    assert (path / "proposal.md").is_file()


MANIFEST_LIKE = {
    "changes": {
        "demo": {
            "eval_cases": [
                {"scenario_id": "known-scenario", "capability": "ticket-triage",
                 "surface": "dspy-eval", "checks": []},
            ]
        }
    }
}


def test_the_loop_runs_no_optimize_for_a_caseless_eval_gap(tmp_path):
    from dspy_gate import nightly

    rows = [
        {
            "scenario_id": "known-scenario",
            "capability": "ticket-triage",
            "green": False,
            "detail": "",
            "route": "",
        }
    ]
    report = nightly.run(
        rows,
        manifest_data=MANIFEST_LIKE,
        drafts_root=tmp_path / "drafts",
        optimizer_fn=lambda program, train, val: program,
        run_fn=lambda case: ({"severity": "P0"}, []),
        budgets={},
        holdout_ratios={},
    )
    outcomes = {s["step"]: s["outcome"] for s in report["steps"]}
    assert outcomes["optimize"] == "no eval gaps"


def test_the_triage_counts_report_none_for_an_empty_run():
    from dspy_gate import nightly

    assert nightly._counts([]) == "none"


def test_the_split_keeps_one_heldout_for_two_cases():
    from dspy_gate import optimize

    cases = [
        {"scenario_id": f"s{i}", "checks": []} for i in range(2)
    ]
    train, val, heldout = optimize.split(cases, 0.3)
    assert len(heldout) == 1
    assert len(train) + len(val) == 1


def test_the_split_slices_exactly_for_ten_cases():
    from dspy_gate import optimize

    cases = [{"scenario_id": f"s{i}", "checks": []} for i in range(10)]
    train, val, heldout = optimize.split(cases, 0.3)
    assert (len(train), len(val), len(heldout)) == (6, 1, 3)


REPO_ROOT = Path(__file__).absolute().parents[2]


def test_the_source_hash_is_ten_hex_characters(tmp_path):
    from dspy_gate import scenarioparse

    change = tmp_path / "openspec" / "changes" / "demo" / "specs" / "triage"
    change.mkdir(parents=True)
    (change / "spec.md").write_text(
        "### Requirement: Triage\n\n"
        "#### Scenario: Outage [surface: dspy-eval]\n"
        "- **WHEN** the ticket arrives\n- **THEN** severity = P0\n",
        encoding="utf-8",
    )
    data = scenarioparse.parse_change(change.parent.parent)
    digest = data["requirements"][0]["scenarios"][0]["source_hash"]
    assert len(digest) == 10
    int(digest, 16)


def test_the_bridge_hook_ignores_a_bare_changes_path(tmp_path, capsys, monkeypatch):
    from dspy_gate import bridge_hook

    monkeypatch.setattr(bridge_hook, "repo_root", lambda: tmp_path)
    path = str(tmp_path / "openspec" / "changes" / "demo")
    code = bridge_hook.main(json.dumps({"tool_input": {"file_path": path}}))
    assert code == 0
    assert capsys.readouterr().out == ""


def test_the_doctor_reports_json_on_a_bad_policy_root(tmp_path, capsys):
    """A failing probe must not leak into the JSON report: the capture
    flip and the check flip both surface here."""
    import json as json_mod

    (tmp_path / "tools" / "dspy_gate").mkdir(parents=True)
    (tmp_path / "tools" / "dspy_gate" / "gates.yaml").write_text(
        "not: [valid\n", encoding="utf-8"
    )
    import sys

    sys.path.insert(0, str(REPO_ROOT / "tools" / "dspy_gate_setup"))
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "doctor_bad_policy", str(REPO_ROOT / "tools" / "dspy_gate_setup" / "dspy_gate_setup.py")
    )
    doctor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(doctor)

    code = doctor.main(["--repo-root", str(tmp_path), "--json"])
    payload = json_mod.loads(capsys.readouterr().out)
    assert code == 2
    assert payload["checks"]["gates.yaml parses with bounds"] is False


def test_bank_writes_through_a_fresh_nested_directory(tmp_path):
    path = tmp_path / "deep" / "nested" / "bank.jsonl"
    assert bank.write(path, {"scenario_id": "s", "gate_verdicts": {"A": True}}) is True
    assert len(bank.read_all(path)) == 1


def test_certify_writes_through_a_fresh_nested_ledger(tmp_path):
    path = tmp_path / "deep" / "nested" / "triage.jsonl"
    certs.record(path, pins="p", source="s")
    assert certs.read_rows(path)[0]["pins"] == "p"


def test_the_environment_error_row_is_red_and_not_deferred(tmp_path, capsys, monkeypatch):
    from test_gate_cli import make_repo, run
    import json as json_mod

    root = make_repo(tmp_path)
    run(["regen", "demo"], root, monkeypatch)
    capsys.readouterr()  # drain the human regen report
    manifest = root / "openspec" / "eval_manifest.json"
    data = json_mod.loads(manifest.read_text(encoding="utf-8"))
    data["changes"]["demo"]["eval_cases"].append(
        {
            "scenario_id": "broken-harness",
            "capability": "ghost-capability",
            "impl": "hand",
            "surface": "dspy-eval",
            "checks": [{"tier": "A", "kind": "eq", "field": "x", "value": "1"}],
            "dataset_path": "evals/triage/broken.json",
        }
    )
    manifest.write_text(json_mod.dumps(data), encoding="utf-8")
    run(["--json", "status", "demo"], root, monkeypatch)
    payload = json_mod.loads(capsys.readouterr().out)
    row = next(r for r in payload["rows"] if r["scenario_id"] == "broken-harness")
    assert row["green"] is False
    assert row["deferred"] is False


def test_evals_out_writes_twice_into_the_same_directory(tmp_path, capsys, monkeypatch):
    from test_gate_cli import make_repo, run

    root = make_repo(tmp_path)
    out = root / "target" / "gate-report" / "demo.json"
    run(["regen", "demo"], root, monkeypatch)
    capsys.readouterr()
    assert run(["evals", "demo", "--out", str(out)], root, monkeypatch) == 0
    assert run(["evals", "demo", "--out", str(out)], root, monkeypatch) == 0
    assert out.is_file()


def test_the_parser_rejects_a_missing_change_id(tmp_path):
    from test_gate_cli import run

    assert run(["lint"], tmp_path) == 2


def test_json_output_starts_with_the_exit_key(tmp_path, capsys, monkeypatch):
    from test_gate_cli import make_repo, run

    root = make_repo(tmp_path)
    run(["regen", "demo"], root, monkeypatch)
    capsys.readouterr()
    run(["--json", "evals", "demo"], root, monkeypatch)
    assert capsys.readouterr().out.startswith('{"exit"')


def test_status_json_sorts_the_change_key_first(tmp_path, capsys, monkeypatch):
    from test_gate_cli import make_repo, run

    root = make_repo(tmp_path)
    run(["regen", "demo"], root, monkeypatch)
    capsys.readouterr()
    run(["--json", "status", "demo"], root, monkeypatch)
    assert capsys.readouterr().out.startswith('{"change"')


def test_datasets_write_twice_into_the_same_directory(tmp_path):
    from dspy_gate import datasets, manifest

    from test_manifest import CHANGE, MODULES

    case = manifest.build(CHANGE, MODULES)["changes"]["demo"]["eval_cases"][0]
    datasets.write_case(tmp_path / "evals" / "triage", case, MODULES)
    datasets.write_case(tmp_path / "evals" / "triage", case, MODULES)
    assert len(list((tmp_path / "evals" / "triage").iterdir())) == 1


def test_datasets_write_through_a_fresh_nested_directory(tmp_path):
    from dspy_gate import datasets, manifest

    from test_manifest import CHANGE, MODULES

    case = manifest.build(CHANGE, MODULES)["changes"]["demo"]["eval_cases"][0]
    path = datasets.write_case(tmp_path / "deep" / "evals" / "triage", case, MODULES)
    assert path.is_file()


def test_manifest_write_twice_into_the_same_path(tmp_path):
    from dspy_gate import manifest

    path = tmp_path / "nested" / "m.json"
    manifest.write({"version": 1, "changes": {}}, path)
    manifest.write({"version": 1, "changes": {}}, path)
    assert manifest.load(path)["version"] == 1


def test_the_matrix_json_sorts_keys_before_rows():
    from dspy_gate import evals, matrix

    text = matrix.to_json(evals.Report(0, []))
    assert text.index('"exit"') < text.index('"rows"')
