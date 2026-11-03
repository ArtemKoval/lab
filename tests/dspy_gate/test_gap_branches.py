"""Gap-filling tests: the tier C and D runners, the lint subprocess
body, the hook env branches, the CLI error paths, and the judge
helpers. One behavior per test."""

import json
import subprocess
import types

import pytest

from dspy_gate import bridge_hook, checks, compile as compile_mod, evals, judge, lint, matrix, protect_hook, surface


def test_tier_c_passes_on_the_right_order():
    trace = [{"tool": "escalate"}, {"step": "reply"}]
    result = checks.run_tier_c(
        [{"tier": "C", "kind": "call_order", "before": "escalate", "after": "reply"}],
        trace,
    )
    assert result.passed


def test_tier_c_fails_when_the_order_reverses():
    trace = [{"step": "reply"}, {"tool": "escalate"}]
    result = checks.run_tier_c(
        [{"tier": "C", "kind": "call_order", "before": "escalate", "after": "reply"}],
        trace,
    )
    assert not result.passed
    assert "must precede" in result.detail


def test_tier_c_fails_when_a_call_is_missing():
    result = checks.run_tier_c(
        [{"tier": "C", "kind": "call_order", "before": "escalate", "after": "reply"}],
        [],
    )
    assert not result.passed
    assert "no escalate call" in result.detail


def test_tier_c_reports_the_missing_step():
    result = checks.run_tier_c(
        [{"tier": "C", "kind": "call_order", "before": "escalate", "after": "reply"}],
        [{"tool": "escalate"}],
    )
    assert not result.passed
    assert "no reply step" in result.detail


def test_a_judged_scenario_without_a_rubric_is_refused():
    scenario = {
        "scenario_id": "s",
        "capability": "c",
        "thens": ["severity = P0"],
        "judged": True,
        "rubric": None,
    }
    with pytest.raises(compile_mod.CompileError) as exc:
        compile_mod.compile_scenario(scenario)
    assert "without a rubric" in str(exc.value)


def test_a_scenario_that_compiles_to_nothing_is_refused():
    scenario = {
        "scenario_id": "s",
        "capability": "c",
        "thens": [],
        "judged": False,
        "rubric": None,
    }
    with pytest.raises(compile_mod.CompileError) as exc:
        compile_mod.compile_scenario(scenario)
    assert "no assertions" in str(exc.value)


def test_an_unformal_then_with_an_inline_judge_compiles_to_the_reference():
    scenario = {
        "scenario_id": "s",
        "capability": "c",
        "thens": ["the response should be helpful [judge: rubric = r.md]"],
        "judged": False,
        "rubric": None,
    }
    checks = compile_mod.compile_scenario(scenario)
    assert checks == [
        {"tier": "B", "kind": "judge", "rubric": "r.md", "ensemble": 3}
    ]


def test_the_lint_subprocess_body_reports_a_clean_run(tmp_path, monkeypatch):
    change = tmp_path / "openspec" / "changes" / "demo"
    change.mkdir(parents=True)
    completed = types.SimpleNamespace(returncode=0, stdout="", stderr="")
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: completed)
    ok, output = lint.openspec_validate(change)
    assert ok is True
    assert output == ""


def test_the_lint_subprocess_body_reports_a_failure(tmp_path, monkeypatch):
    change = tmp_path / "openspec" / "changes" / "demo"
    change.mkdir(parents=True)
    completed = types.SimpleNamespace(returncode=1, stdout="bad", stderr="worse")
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: completed)
    ok, output = lint.openspec_validate(change)
    assert ok is False
    assert "bad" in output and "worse" in output


def test_protect_hook_repo_root_takes_the_env(tmp_path, monkeypatch):
    (tmp_path / "tools" / "dspy_gate").mkdir(parents=True)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    assert protect_hook.repo_root() == tmp_path


def test_protect_hook_repo_root_falls_back_to_the_package(monkeypatch):
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    assert (protect_hook.repo_root() / "tools" / "dspy_gate").is_dir()


def test_bridge_hook_repo_root_takes_the_env(tmp_path, monkeypatch):
    (tmp_path / "tools" / "dspy_gate").mkdir(parents=True)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    assert bridge_hook.repo_root() == tmp_path


def test_bridge_hook_survives_a_payload_without_a_path(capsys, monkeypatch):
    monkeypatch.setattr(bridge_hook, "repo_root", lambda: None)
    assert bridge_hook.main(json.dumps({"tool_name": "Edit"})) == 0
    assert capsys.readouterr().out == ""


def test_an_optimized_module_routes_a_failure_to_reoptimize():
    case = {
        "scenario_id": "s",
        "capability": "c",
        "surface": "dspy-eval",
        "impl": "optimized",
        "checks": [{"tier": "A", "kind": "eq", "field": "x", "value": "1"}],
    }

    def run_fn(case):
        return {"x": "2"}, []

    report = evals.run_delta([case], budget={}, run_fn=run_fn)
    assert report.rows[0]["route"] == "re-optimize"


def test_a_green_usage_record_passes_tier_d():
    case = {
        "scenario_id": "s",
        "capability": "c",
        "surface": "dspy-eval",
        "checks": [{"tier": "A", "kind": "eq", "field": "x", "value": "1"}],
    }

    def run_fn(case):
        return {"x": "1"}, []

    report = evals.run_delta(
        [case], budget={"p95_tokens_per_scenario": 100}, usage={"p95_tokens": 10}, run_fn=run_fn
    )
    assert report.exit == 0
    assert report.rows[0]["tiers"]["D"] is True


def test_matrix_renders_an_empty_report():
    report = evals.Report(0, [])
    assert matrix.render(report) == "| scenario | status | tier | route |\n|---|---|---|---|"


def test_the_rubric_text_reads_the_file_when_it_exists(tmp_path):
    rubric = tmp_path / "rubrics" / "x.md"
    rubric.parent.mkdir()
    rubric.write_text("pass criteria here", encoding="utf-8")
    text = judge._rubric_text(str(rubric))
    assert text == "pass criteria here"


def test_the_visual_gate_passes_on_a_majority():
    votes = [1.0, 0.0, 1.0]
    assert judge.visual_gate({}, lambda case: votes.pop(0)) is True


def test_the_visual_gate_fails_on_a_minority():
    votes = [0.0, 0.0, 1.0]
    assert judge.visual_gate({}, lambda case: votes.pop(0)) is False


def test_harness_run_defaults_to_the_real_registry():
    from dspy_gate import harness

    case = {
        "capability": "ticket-triage",
        "scenario_id": "outage-keywords-route-to-on-call",
    }
    pred, trace = harness.run(case)
    assert pred["severity"] == "P0"
    assert trace


def test_evict_on_a_missing_store_removes_nothing(tmp_path):
    from dspy_gate import bank

    assert bank.evict(tmp_path / "absent.jsonl", "x") == 0


def event(path):
    return {"tool_name": "Edit", "tool_input": {"file_path": str(path)}}


def test_a_red_tier_c_failure_routes_through_the_suite():
    case = {
        "scenario_id": "s",
        "capability": "c",
        "surface": "dspy-eval",
        "checks": [{"tier": "C", "kind": "call_order", "before": "a", "after": "b"}],
    }

    def run_fn(case):
        return {}, [{"step": "b"}, {"tool": "a"}]

    report = evals.run_delta([case], budget={}, run_fn=run_fn)
    assert report.exit == 2
    assert report.rows[0]["tiers"]["C"] is False


def test_lint_reports_a_parse_error(tmp_path):
    change = tmp_path / "openspec" / "changes" / "demo"
    (change / "specs" / "triage").mkdir(parents=True)
    (change / "specs" / "triage" / "spec.md").write_text(
        "### Requirement: Broken\n\n"
        "#### Scenario: broken [surface: dspy-eval]\n- **THEN** nothing\n",
        encoding="utf-8",
    )
    policy = tmp_path / "p.yaml"
    policy.write_text("version: 1\n", encoding="utf-8")
    from dspy_gate import gatepolicy

    found = lint.lint_change(
        change, gatepolicy.load(policy), {}, validate=lambda d: (True, "")
    )
    assert any("Unparseable scenario" in v for v in found)


def test_bridge_hook_falls_back_to_the_package_root(monkeypatch):
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    assert (bridge_hook.repo_root() / "openspec" / "changes").is_dir()


def test_bridge_hook_ignores_a_non_specs_change_path(capsys, monkeypatch):
    monkeypatch.setattr(bridge_hook, "repo_root", lambda: None)
    path = "/repo/openspec/changes/demo/notes.md"
    assert bridge_hook.main(json.dumps({"tool_input": {"file_path": path}})) == 0
    assert capsys.readouterr().out == ""


def test_bridge_hook_stays_silent_when_generation_is_fresh(
    tmp_path, capsys, monkeypatch
):
    change = tmp_path / "openspec" / "changes" / "demo"
    (change / "specs" / "triage").mkdir(parents=True)
    (change / "specs" / "triage" / "spec.md").write_text(
        "## ADDED Requirements\n\n### Requirement: Triage\n\n"
        "#### Scenario: Outage [surface: dspy-eval]\n"
        "- **WHEN** the ticket arrives\n- **THEN** severity = P0\n",
        encoding="utf-8",
    )
    (tmp_path / "tools" / "dspy_gate" / "gates.yaml").parent.mkdir(parents=True)
    (tmp_path / "tools" / "dspy_gate" / "gates.yaml").write_text(
        "version: 1\npolicy_bounds:\n  tier_b_min: {min: 0.6, max: 1.0}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(bridge_hook, "repo_root", lambda: tmp_path)
    from dspy_gate import cli

    cli.cmd_regen(str(tmp_path), "demo", cli._load_modules(str(tmp_path)))
    code = bridge_hook.main(json.dumps(event(change / "specs" / "triage" / "spec.md")))
    assert code == 0
    assert capsys.readouterr().out == ""


def test_harness_run_without_a_registry_example_falls_back_to_when():
    from dspy_gate import harness

    case = {"capability": "ticket-triage", "scenario_id": "no-such-example"}
    with pytest.raises(TypeError):
        harness.run(case)


def test_freeze_skips_a_capability_absent_from_the_change(tmp_path):
    from dspy_gate import freeze

    change = tmp_path / "openspec" / "changes" / "demo"
    (change / "evals" / "triage").mkdir(parents=True)
    case_file = change / "evals" / "triage" / "s.json"
    case_file.write_text("{}", encoding="utf-8")
    manifest = {"changes": {"demo": {"eval_cases": [
        {"scenario_id": "s", "capability": "triage", "surface": "dspy-eval"}
    ]}}}
    (tmp_path / "openspec" / "eval_manifest.json").parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / "openspec" / "eval_manifest.json").write_text(json.dumps(manifest))
    (change / "gates.yaml").write_text(
        "version: 1\ncapabilities:\n  other-cap:\n    gate_2: {tier_a: 1.0}\n",
        encoding="utf-8",
    )
    report = freeze.run(tmp_path, "demo")
    assert report == {"triage": {"evals": 1, "gates": False}}


def test_bank_read_skips_blank_lines(tmp_path):
    from dspy_gate import bank

    path = tmp_path / "bank.jsonl"
    bank.write(path, {"scenario_id": "s", "gate_verdicts": {"A": True}})
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    assert len(bank.read_all(path)) == 1


def test_evict_keeps_entries_across_a_blank_line(tmp_path):
    from dspy_gate import bank

    path = tmp_path / "bank.jsonl"
    bank.write(path, {"scenario_id": "s", "gate_verdicts": {"A": True}})
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    bank.evict(path, "other-scenario")
    assert len(bank.read_all(path)) == 1


def test_a_deferred_case_loops_after_the_judge_branch():
    case = {
        "scenario_id": "s",
        "capability": "c",
        "surface": "dspy-eval",
        "checks": [
            {"tier": "B", "kind": "judge", "rubric": "r.md", "ensemble": 3},
            {"tier": "A", "kind": "eq", "field": "x", "value": "1"},
        ],
    }

    def run_fn(case):
        return {"x": "1"}, []

    report = evals.run_delta([case], budget={}, run_fn=run_fn)
    assert report.exit == 0
    assert report.rows[0]["deferred"] is True
    assert report.rows[0]["tiers"]["A"] is True


def test_an_unknown_tier_in_the_checks_loops_on():
    case = {
        "scenario_id": "s",
        "capability": "c",
        "surface": "dspy-eval",
        "checks": [
            {"tier": "D", "kind": "budget"},
            {"tier": "A", "kind": "eq", "field": "x", "value": "1"},
        ],
    }

    def run_fn(case):
        return {"x": "1"}, []

    report = evals.run_delta([case], budget={}, run_fn=run_fn)
    assert report.exit == 0


def test_judge_defaults_the_ensemble_without_a_tier_b_check():
    scores = iter([1.0, 1.0, 0.5])
    result = judge.judge_case(
        {"rubric": "r.md", "checks": [{"tier": "A", "kind": "eq"}]},
        lambda case: next(scores),
        threshold=0.80,
    )
    assert "of 3 votes" in result.detail


def test_gatepolicy_skips_non_numeric_thresholds(tmp_path):
    from dspy_gate import gatepolicy

    policy = tmp_path / "p.yaml"
    policy.write_text("version: 1\npolicy_bounds:\n  tier_b_min: {min: 0.6, max: 1.0}\n")
    change = tmp_path / "c.yaml"
    change.write_text(
        "version: 1\ncapabilities:\n  triage:\n    gate_2: {tier_a: 1.0, mode: fast}\n"
    )
    found = gatepolicy.violations(gatepolicy.load(policy), gatepolicy.load(change))
    assert found == []


def test_matrix_renders_a_row_without_tiers():
    report = evals.Report(0, [{"scenario_id": "s", "green": True, "deferred": False, "route": "", "tiers": {}}])
    assert "| - |" in matrix.render(report)


def test_surface_ignores_a_capability_without_a_visual_dir(tmp_path):
    (tmp_path / "openspec" / "specs" / "console").mkdir(parents=True)
    found = surface.baseline_violations({"changes": {}}, tmp_path)
    assert found == []


def test_surface_ignores_a_baseline_with_a_bad_name(tmp_path):
    visual = tmp_path / "openspec" / "specs" / "console" / "visual"
    visual.mkdir(parents=True)
    (visual / "not-a-baseline.png").write_bytes(b"png")
    found = surface.baseline_violations({"changes": {}}, tmp_path)
    assert found == []


def test_a_judge_only_tag_sets_judged_without_a_surface(tmp_path):
    from dspy_gate import scenarioparse

    tags = scenarioparse.parse_tags("[judge]")
    assert tags[1] is True
    assert tags[0] is None


def test_mcp_main_builds_and_runs_the_server(monkeypatch):
    from dspy_gate import mcp_server

    ran = []
    monkeypatch.setattr(
        mcp_server, "build_server", lambda: types.SimpleNamespace(run=lambda: ran.append(1))
    )
    mcp_server.main()
    assert ran == [1]


def test_matrix_renders_a_deferred_row():
    report = evals.Report(0, [
        {"scenario_id": "s", "green": True, "deferred": True, "route": "re-optimize", "tiers": {"B": None}}
    ])
    assert "deferred" in matrix.render(report)


def test_freeze_runs_without_a_change_gates_file(tmp_path):
    from dspy_gate import freeze

    change = tmp_path / "openspec" / "changes" / "demo" / "evals" / "triage"
    change.mkdir(parents=True)
    (change / "s.json").write_text("{}", encoding="utf-8")
    manifest = {"changes": {"demo": {"eval_cases": [
        {"scenario_id": "s", "capability": "triage", "surface": "dspy-eval"}
    ]}}}
    (tmp_path / "openspec").mkdir(parents=True, exist_ok=True)
    (tmp_path / "openspec" / "eval_manifest.json").write_text(json.dumps(manifest))
    report = freeze.run(tmp_path, "demo")
    assert report == {"triage": {"evals": 1, "gates": False}}


def test_lint_without_a_registry_lints_every_scenario(tmp_path):
    change = tmp_path / "openspec" / "changes" / "demo"
    (change / "specs" / "triage").mkdir(parents=True)
    (change / "specs" / "triage" / "spec.md").write_text(
        "### Requirement: Triage\n\n"
        "#### Scenario: broken [surface: dspy-eval]\n"
        "- **WHEN** a ticket arrives\n- **THEN** nothing\n",
        encoding="utf-8",
    )
    policy = tmp_path / "p.yaml"
    policy.write_text("version: 1\n", encoding="utf-8")
    from dspy_gate import gatepolicy

    found = lint.lint_change(change, gatepolicy.load(policy), validate=lambda d: (True, ""))
    assert any("Uncompilable THEN" in v for v in found)


def test_lint_skips_scenarios_outside_the_registry(tmp_path):
    change = tmp_path / "openspec" / "changes" / "demo"
    (change / "specs" / "triage").mkdir(parents=True)
    (change / "specs" / "triage" / "spec.md").write_text(
        "### Requirement: Triage\n\n"
        "#### Scenario: broken [surface: dspy-eval]\n"
        "- **WHEN** a ticket arrives\n- **THEN** nothing\n",
        encoding="utf-8",
    )
    policy = tmp_path / "p.yaml"
    policy.write_text("version: 1\n", encoding="utf-8")
    from dspy_gate import gatepolicy

    found = lint.lint_change(
        change, gatepolicy.load(policy), {"other-cap": {}}, validate=lambda d: (True, "")
    )
    assert found == []


def test_a_passing_tier_c_check_loops_the_suite_green():
    case = {
        "scenario_id": "s",
        "capability": "c",
        "surface": "dspy-eval",
        "checks": [{"tier": "C", "kind": "call_order", "before": "a", "after": "b"}],
    }

    def run_fn(case):
        return {}, [{"tool": "a"}, {"step": "b"}]

    report = evals.run_delta([case], budget={}, run_fn=run_fn)
    assert report.exit == 0
    assert report.rows[0]["tiers"]["C"] is True


def test_parse_tags_skip_a_token_that_matches_neither_name():
    from dspy_gate import scenarioparse

    surface, judged, rubric = scenarioparse.parse_tags("[surface: dspy-eval, other]")
    assert surface == "dspy-eval"
    assert judged is False
    assert rubric is None
