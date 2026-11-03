"""Gap-filling tests: the tier C and D runners, the lint subprocess
body, the hook env branches, the CLI error paths, and the judge
helpers. One behavior per test."""

import json
import subprocess
import types

import pytest

from dspy_gate import bridge_hook, checks, compile as compile_mod, evals, harness, judge, lint, matrix, protect_hook, surface
from dspy_gate import nightly


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


def test_check_manifest_names_a_missing_baseline(tmp_path, monkeypatch):
    from test_gate_cli import make_repo, run
    import json

    root = make_repo(tmp_path)
    run(["regen", "demo"], root, monkeypatch)
    manifest = root / "openspec" / "eval_manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["changes"]["demo"]["eval_cases"].append(
        {
            "scenario_id": "banner-is-legible",
            "capability": "triage",
            "surface": "e2e-visual",
            "checks": [],
            "dataset_path": "evals/triage/banner-is-legible.json",
        }
    )
    manifest.write_text(json.dumps(data), encoding="utf-8")
    assert run(["check-manifest", "demo"], root, monkeypatch) == 2


def test_the_bridge_hook_survives_a_policy_import_error(tmp_path, capsys, monkeypatch):
    from test_gate_cli import make_repo, run
    from dspy_gate import cli

    root = make_repo(tmp_path)
    run(["regen", "demo"], root, monkeypatch)
    change = root / "openspec" / "changes" / "demo" / "specs" / "triage" / "spec.md"
    monkeypatch.setattr(bridge_hook, "repo_root", lambda: root)
    monkeypatch.setattr(
        cli, "cmd_verify", lambda *a, **k: (_ for _ in ()).throw(ImportError("no yaml"))
    )
    capsys.readouterr()  # drain the regen report
    code = bridge_hook.main(json.dumps(event(change)))
    assert code == 0
    assert capsys.readouterr().out == ""


def test_freeze_refuses_when_a_visual_baseline_is_missing(tmp_path):
    from dspy_gate import freeze

    change = tmp_path / "openspec" / "changes" / "demo" / "evals" / "triage"
    change.mkdir(parents=True)
    (change / "s.json").write_text("{}", encoding="utf-8")
    (tmp_path / "openspec").mkdir(parents=True, exist_ok=True)
    (tmp_path / "openspec" / "eval_manifest.json").write_text(json.dumps({
        "changes": {"demo": {"eval_cases": [
            {"scenario_id": "s", "capability": "triage", "surface": "e2e-visual"}
        ]}}
    }))
    with pytest.raises(ValueError) as exc:
        freeze.run(tmp_path, "demo")
    assert "baseline" in str(exc.value)


def test_optimize_certifies_an_optimized_module(tmp_path, capsys, monkeypatch):
    import textwrap
    from dspy_gate import cli

    root = tmp_path
    specs = root / "openspec" / "changes" / "demo" / "specs" / "triage"
    specs.mkdir(parents=True)
    (specs / "spec.md").write_text(textwrap.dedent("""
        ## ADDED Requirements

        ### Requirement: Triage assigns severity

        #### Scenario: Outage routes to on-call [surface: dspy-eval]
        - **WHEN** the ticket text contains the phrase production down
        - **THEN** severity = P0

        #### Scenario: Billing routes to billing [surface: dspy-eval]
        - **WHEN** the ticket mentions a refund
        - **THEN** team = billing
        """), encoding="utf-8")
    tool = root / "tools" / "dspy_gate"
    tool.mkdir(parents=True)
    (tool / "gates.yaml").write_text(
        "version: 1\npolicy_bounds:\n  tier_b_min: {min: 0.6, max: 1.0}\n",
        encoding="utf-8",
    )
    artifacts = tool / "artifacts" / "demo"
    artifacts.mkdir(parents=True)
    (artifacts / "pointer.json").write_text("{}", encoding="utf-8")
    optimized_registry = {
        "triage": {
            "module": "Triage",
            "impl": "optimized",
            "entry": "dspy_gate.harness.triage::triage",
            "artifacts": str(artifacts),
            "examples": {
                "outage-routes-to-on-call": {"ticket": "production down"},
                "billing-routes-to-billing": {"ticket": "refund please"},
            },
        }
    }
    from test_gate_cli import run

    run(["regen", "demo"], root, monkeypatch, modules=optimized_registry)
    capsys.readouterr()
    assert run(["optimize", "demo"], root, monkeypatch, modules=optimized_registry) == 0
    assert "certified" in capsys.readouterr().out


def test_optimize_reports_the_missing_manifest(tmp_path, capsys, monkeypatch):
    from test_gate_cli import make_repo, run

    root = make_repo(tmp_path)
    assert run(["optimize", "demo"], root, monkeypatch) == 2
    assert "no eval manifest" in capsys.readouterr().out


def test_evals_out_writes_the_report_file(tmp_path, capsys, monkeypatch):
    import json
    from test_gate_cli import make_repo, run

    root = make_repo(tmp_path)
    run(["regen", "demo"], root, monkeypatch)
    capsys.readouterr()
    out = root / "target" / "gate-report" / "demo.json"
    assert run(["evals", "demo", "--out", str(out)], root, monkeypatch) == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["exit"] == 0
    assert payload["rows"][0]["case"]["scenario_id"] == "outage-routes-to-on-call"


def test_pin_drift_passes_without_any_manifest(tmp_path, capsys, monkeypatch):
    from test_gate_cli import make_repo, run

    root = make_repo(tmp_path)
    assert run(["pin-drift"], root, monkeypatch) == 0


def test_run_refuses_an_optimized_module_with_no_artifacts_name():
    modules = {
        "ghost-cap": {
            "module": "Ghost",
            "impl": "optimized",
            "entry": "dspy_gate.harness.triage::triage",
        }
    }
    case = {"capability": "ghost-cap", "scenario_id": "s"}
    with pytest.raises(FileNotFoundError) as exc:
        harness.run(case, modules)
    assert "names no artifacts directory" in str(exc.value)


def test_the_loop_promotes_without_frozen_suites_and_notes_it(tmp_path):
    def case_payload(scenario_id):
        return {
            "scenario_id": scenario_id,
            "capability": "ticket-triage",
            "surface": "dspy-eval",
            "checks": [{"tier": "A", "kind": "eq", "field": "severity", "value": "P0"}],
        }

    manifest_data = {
        "changes": {
            "demo": {
                "eval_cases": [
                    {"scenario_id": "held-one", "capability": "ticket-triage",
                     "surface": "dspy-eval", "checks": []},
                ]
            }
        }
    }

    rows = [
        {
            "scenario_id": "known-scenario",
            "capability": "ticket-triage",
            "green": False,
            "detail": "",
            "route": "",
            "case": case_payload("held-one"),
        },
        {
            "scenario_id": "known-scenario",
            "capability": "ticket-triage",
            "green": False,
            "detail": "",
            "route": "",
            "case": case_payload("held-two"),
        },
    ]
    report = nightly.run(
        rows,
        manifest_data=manifest_data,
        drafts_root=tmp_path / "drafts",
        optimizer_fn=lambda program, train, val: program,
        run_fn=lambda case: ({"severity": "P0"}, []),
        budgets={},
        holdout_ratios={},
        artifacts_root=tmp_path / "artifacts",
    )
    outcomes = {s["step"]: s["outcome"] for s in report["steps"]}
    assert "no frozen suites yet" in outcomes["certify"]
    assert "candidates/nightly" in outcomes["promote"]


def test_lint_rejects_a_duplicated_scenario_id(tmp_path):
    spec = (
        "### Requirement: Triage\n\n"
        "#### Scenario: Same name [surface: dspy-eval]\n"
        "- **WHEN** a ticket arrives\n- **THEN** severity = P0\n\n"
        "#### Scenario: Same name [surface: dspy-eval]\n"
        "- **WHEN** a ticket arrives\n- **THEN** severity = P0\n"
    )
    change = tmp_path / "openspec" / "changes" / "demo"
    (change / "specs" / "triage").mkdir(parents=True)
    (change / "specs" / "triage" / "spec.md").write_text(spec, encoding="utf-8")
    policy = tmp_path / "p.yaml"
    policy.write_text("version: 1\n", encoding="utf-8")
    from dspy_gate import gatepolicy

    found = lint.lint_change(change, gatepolicy.load(policy), {}, validate=lambda d: (True, ""))
    assert any("appears 2 times" in v for v in found)
