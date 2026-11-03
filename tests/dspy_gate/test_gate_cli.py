"""Tests for the CLI contract: subcommands, --json, and the exit
codes 0 on success and 2 on operational failure. Also the status
command and the MCP wrapper parity."""

import json
import textwrap

from dspy_gate import cli

SPEC = """
    ## ADDED Requirements

    ### Requirement: Triage assigns severity

    #### Scenario: Outage routes to on-call [surface: dspy-eval]
    - **WHEN** the ticket text contains the phrase production down
    - **THEN** severity = P0
    """

POLICY = """
    version: 1
    policy_bounds:
      tier_b_min: { min: 0.60, max: 1.00 }
    """

REGISTRY = {
    "triage": {
        "module": "Triage",
        "impl": "hand",
        "entry": "dspy_gate.harness.triage::triage",
        "examples": {"outage-routes-to-on-call": {"ticket": "production down"}},
    }
}


def make_repo(tmp_path, spec_text=SPEC, policy_text=POLICY):
    change = tmp_path / "openspec" / "changes" / "demo"
    specs = change / "specs" / "triage"
    specs.mkdir(parents=True)
    (specs / "spec.md").write_text(textwrap.dedent(spec_text), encoding="utf-8")
    (tmp_path / "tools" / "dspy_gate" / "gates.yaml").parent.mkdir(parents=True)
    (tmp_path / "tools" / "dspy_gate" / "gates.yaml").write_text(policy_text, encoding="utf-8")
    return tmp_path


def run(argv, cwd, monkeypatch=None, validate_ok=True):
    """Run the CLI with the openspec subprocess stubbed out."""
    if monkeypatch is not None:
        monkeypatch.setattr(
            cli.lint,
            "openspec_validate",
            lambda change_dir: (validate_ok, "" if validate_ok else "bad"),
        )
        monkeypatch.setattr(cli, "_load_modules", lambda root: dict(REGISTRY))
    return cli.main(["--repo-root", str(cwd)] + argv)


def test_lint_exits_0_on_a_clean_change(tmp_path, capsys, monkeypatch):
    root = make_repo(tmp_path)
    assert run(["lint", "demo"], root, monkeypatch) == 0
    assert "demo" in capsys.readouterr().out


def test_lint_exits_2_on_a_violation(tmp_path, capsys, monkeypatch):
    root = make_repo(tmp_path, spec_text=SPEC.replace("[surface: dspy-eval]", ""))
    assert run(["lint", "demo"], root, monkeypatch) == 2
    assert "no surface tag" in capsys.readouterr().out


def test_lint_json_carries_the_violations(tmp_path, capsys, monkeypatch):
    root = make_repo(tmp_path, spec_text=SPEC.replace("[surface: dspy-eval]", ""))
    run(["--json", "lint", "demo"], root, monkeypatch)
    payload = json.loads(capsys.readouterr().out)
    assert payload["exit"] == 2
    assert any("no surface tag" in v for v in payload["violations"])


def test_check_manifest_exits_2_when_the_manifest_is_missing(tmp_path, capsys):
    root = make_repo(tmp_path)
    assert run(["check-manifest", "demo"], tmp_path) == 2
    assert "no eval manifest" in capsys.readouterr().out


def test_verify_exits_2_when_generation_is_stale(tmp_path, capsys, monkeypatch):
    root = make_repo(tmp_path)
    assert run(["verify", "demo"], root, monkeypatch) == 2
    assert "stale" in capsys.readouterr().out


def test_unknown_command_exits_2(tmp_path):
    assert run(["frobnicate"], tmp_path) == 2


def test_lint_names_a_missing_change(tmp_path, capsys, monkeypatch):
    root = make_repo(tmp_path)
    assert run(["lint", "ghost"], root, monkeypatch) == 2
    assert "ghost" in capsys.readouterr().out


def test_regen_then_verify_exits_0(tmp_path, capsys, monkeypatch):
    root = make_repo(tmp_path)
    assert run(["regen", "demo"], root, monkeypatch) == 0
    assert run(["verify", "demo"], root, monkeypatch) == 0
    assert "verified" in capsys.readouterr().out


def test_status_is_green_after_a_regen(tmp_path, capsys, monkeypatch):
    root = make_repo(tmp_path)
    run(["regen", "demo"], root, monkeypatch)
    capsys.readouterr()  # drain the human regen report
    assert run(["--json", "status", "demo"], root, monkeypatch) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["gates"]["gate_0"] == "green"
    assert payload["gates"]["gate_1"] == "green"
    assert payload["gates"]["generated"] == "green"


def test_status_is_red_when_generation_is_stale(tmp_path, capsys, monkeypatch):
    root = make_repo(tmp_path)
    run(["regen", "demo"], root, monkeypatch)
    capsys.readouterr()  # drain the human regen report
    manifest = root / "openspec" / "eval_manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["changes"]["demo"]["eval_cases"] = []
    manifest.write_text(json.dumps(data), encoding="utf-8")
    assert run(["--json", "status", "demo"], root, monkeypatch) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["gates"]["gate_1"] == "red"


def test_evals_reports_the_missing_manifest(tmp_path, capsys, monkeypatch):
    root = make_repo(tmp_path)
    assert run(["evals", "demo"], root, monkeypatch) == 2
    assert "no eval manifest" in capsys.readouterr().out


def test_evals_json_carries_the_rows(tmp_path, capsys, monkeypatch):
    root = make_repo(tmp_path)
    run(["regen", "demo"], root, monkeypatch)
    capsys.readouterr()
    assert run(["--json", "evals", "demo"], root, monkeypatch) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["report"]["rows"][0]["scenario_id"] == "outage-routes-to-on-call"


def test_status_reports_red_gates_before_the_first_regen(tmp_path, capsys, monkeypatch):
    root = make_repo(tmp_path)
    assert run(["--json", "status", "demo"], root, monkeypatch) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["gates"]["generated"] == "red"


def test_nightly_direct_call_without_a_report_is_refused(tmp_path, monkeypatch):
    root = make_repo(tmp_path)
    code, payload = cli.cmd_nightly(str(root), "demo", dict(REGISTRY))
    assert code == 2
    assert "needs --from-report" in payload["error"]


def test_a_frozen_inputs_fallback_runs_from_the_registry(tmp_path, capsys, monkeypatch):
    root = make_repo(tmp_path)
    run(["regen", "demo"], root, monkeypatch)
    dataset = (
        root / "openspec" / "changes" / "demo" / "evals" / "triage"
        / "outage-routes-to-on-call.json"
    )
    dataset.unlink()
    capsys.readouterr()
    assert run(["evals", "demo"], root, monkeypatch) == 0


def test_regen_names_a_missing_change(tmp_path, capsys, monkeypatch):
    root = make_repo(tmp_path)
    assert run(["regen", "ghost"], root, monkeypatch) == 2
    assert "ghost" in capsys.readouterr().out


def test_regen_reports_verify_violations_and_writes_nothing(tmp_path, capsys, monkeypatch):
    root = make_repo(tmp_path)
    monkeypatch.setattr(cli.manifest, "verify", lambda *a, **k: ["broken coverage"])
    assert run(["regen", "demo"], root, monkeypatch) == 2
    assert "broken coverage" in capsys.readouterr().out
    assert not (root / "openspec" / "eval_manifest.json").exists()


def test_verify_names_a_missing_change(tmp_path, capsys, monkeypatch):
    root = make_repo(tmp_path)
    assert run(["verify", "ghost"], root, monkeypatch) == 2
    assert "ghost" in capsys.readouterr().out


def test_verify_detects_real_staleness_after_a_regen(tmp_path, capsys, monkeypatch):
    root = make_repo(tmp_path)
    run(["regen", "demo"], root, monkeypatch)
    capsys.readouterr()
    manifest = root / "openspec" / "eval_manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["changes"]["demo"]["eval_cases"][0]["scenario_id"] = "renamed-scenario"
    manifest.write_text(json.dumps(data), encoding="utf-8")
    assert run(["verify", "demo"], root, monkeypatch) == 2
    assert "stale" in capsys.readouterr().out


def test_check_manifest_is_green_after_a_regen(tmp_path, capsys, monkeypatch):
    root = make_repo(tmp_path)
    run(["regen", "demo"], root, monkeypatch)
    capsys.readouterr()
    assert run(["check-manifest", "demo"], root, monkeypatch) == 0


def test_status_names_a_missing_change(tmp_path, capsys, monkeypatch):
    root = make_repo(tmp_path)
    assert run(["status", "ghost"], root, monkeypatch) == 2
    assert "ghost" in capsys.readouterr().out


def test_status_skips_non_dspy_eval_cases_and_reports_red_rows(tmp_path, capsys, monkeypatch):
    root = make_repo(tmp_path)
    run(["regen", "demo"], root, monkeypatch)
    capsys.readouterr()  # drain the human regen report
    manifest = root / "openspec" / "eval_manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    cases = data["changes"]["demo"]["eval_cases"]
    cases.append(
        {
            "scenario_id": "visual-scenario",
            "capability": "triage",
            "surface": "e2e-visual",
            "checks": [],
            "dataset_path": "evals/triage/visual-scenario.json",
        }
    )
    cases.append(
        {
            "scenario_id": "broken-harness",
            "capability": "ghost-capability",
            "surface": "dspy-eval",
            "checks": [{"tier": "A", "kind": "eq", "field": "x", "value": "1"}],
            "dataset_path": "evals/triage/broken-harness.json",
        }
    )
    manifest.write_text(json.dumps(data), encoding="utf-8")
    run(["--json", "status", "demo"], root, monkeypatch)
    payload = json.loads(capsys.readouterr().out)
    ids = [row["scenario_id"] for row in payload["rows"]]
    assert "visual-scenario" not in ids
    assert "broken-harness" in ids
    assert payload["rows"][-1]["route"] == "repair the environment"


def test_find_repo_root_refuses_a_bare_directory(tmp_path, capsys):
    bare = tmp_path / "bare"
    bare.mkdir()
    assert cli.main(["--repo-root", str(bare), "lint", "x"]) == 2
    assert "no openspec/changes" in capsys.readouterr().out


def test_load_modules_survives_a_blocked_registry_import(monkeypatch, tmp_path):
    import sys

    monkeypatch.setitem(sys.modules, "dspy_gate.harness.registry", None)
    import dspy_gate.harness as harness_pkg

    monkeypatch.delattr(harness_pkg, "registry", raising=False)
    assert cli._load_modules(str(tmp_path)) == {}


def test_a_handler_error_reports_and_exits_2(tmp_path, capsys, monkeypatch):
    root = make_repo(tmp_path)
    monkeypatch.setattr(
        cli, "cmd_freeze", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
    )
    assert run(["freeze", "demo"], root, monkeypatch) == 2
    assert "boom" in capsys.readouterr().out


def test_the_mcp_wrapper_registers_two_tools(monkeypatch):
    from dspy_gate import mcp_server

    captured = {}
    monkeypatch.setattr(
        mcp_server, "FastMCP", lambda name: _RecordingMcp(name, captured)
    )
    mcp_server.build_server()
    assert set(captured["tools"]) == {"gate_status", "conformance_matrix"}


def test_the_mcp_tool_returns_the_cli_payload(tmp_path, monkeypatch):
    from dspy_gate import mcp_server

    root = make_repo(tmp_path)
    run(["regen", "demo"], root, monkeypatch)
    payload = mcp_server.gate_status(str(root), "demo")
    assert payload["exit"] == 0
    matrix = mcp_server.conformance_matrix(str(root), "demo")
    assert "rows" in matrix


def test_evals_runs_the_delta_suite_green(tmp_path, capsys, monkeypatch):
    root = make_repo(tmp_path)
    run(["regen", "demo"], root, monkeypatch)
    assert run(["evals", "demo"], root, monkeypatch) == 0
    assert "outage-routes-to-on-call" in capsys.readouterr().out


def test_evals_exits_2_on_a_red_scenario(tmp_path, capsys, monkeypatch):
    root = make_repo(tmp_path, spec_text=SPEC.replace("severity = P0", "severity = P3"))
    run(["regen", "demo"], root, monkeypatch)
    capsys.readouterr()
    assert run(["evals", "demo"], root, monkeypatch) == 2
    assert "fix the harness" in capsys.readouterr().out


def test_matrix_renders_the_table(tmp_path, capsys, monkeypatch):
    root = make_repo(tmp_path)
    run(["regen", "demo"], root, monkeypatch)
    assert run(["matrix", "demo"], root, monkeypatch) == 0
    out = capsys.readouterr().out
    assert "| scenario |" in out
    assert "green" in out


def test_freeze_copies_the_frozen_suite(tmp_path, monkeypatch):
    root = make_repo(tmp_path)
    run(["regen", "demo"], root, monkeypatch)
    (root / "openspec" / "changes" / "demo" / "gates.yaml").write_text(
        "version: 1\ncapabilities:\n  triage:\n    gate_2: {tier_a: 1.0, tier_b_min: 0.8}\n",
        encoding="utf-8",
    )
    assert run(["freeze", "demo"], root, monkeypatch) == 0
    frozen = root / "openspec" / "specs" / "triage" / "evals"
    assert any(frozen.iterdir())


def test_nightly_runs_the_seven_steps(tmp_path, capsys, monkeypatch):
    root = make_repo(tmp_path)
    run(["regen", "demo"], root, monkeypatch)
    capsys.readouterr()  # drain the human regen report
    report = root / "target" / "nightly-report.json"
    report.parent.mkdir(parents=True)
    report.write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "scenario_id": "outage-routes-to-on-call",
                        "capability": "triage",
                        "green": False,
                        "detail": "",
                        "route": "fix the harness",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    assert run(["--json", "nightly", "demo", "--from-report", str(report)], root, monkeypatch) == 0
    payload = json.loads(capsys.readouterr().out)
    steps = [s["step"] for s in payload["steps"]]
    assert steps == [
        "collect", "triage", "expand", "optimize", "certify", "promote", "escalate",
    ]


class _RecordingMcp:
    """Stand-in for FastMCP that records the registered tools."""

    def __init__(self, name, captured):
        self.name = name
        self._captured = captured
        self._captured["tools"] = {}

    def tool(self, **kwargs):
        def register(fn):
            self._captured["tools"][fn.__name__] = fn
            return fn

        return register

    def run(self):  # pragma: no cover - never started in tests
        raise RuntimeError("the server never starts under test")
