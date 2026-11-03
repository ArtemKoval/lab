"""Tests for the spec-gates hooks: the deny contract on GENERATED
paths, the visual-baseline exemption, and the bridge verifier hook."""

import json
import subprocess
from pathlib import Path

from dspy_gate import bridge_hook, protect_hook

REPO_ROOT = Path(__file__).absolute().parents[2]


def event(path):
    return {"tool_name": "Edit", "tool_input": {"file_path": str(path)}}


def run_protect(path, root=None, monkeypatch=None):
    """Run the protect hook with the repo root pinned for the test."""
    if monkeypatch is not None and root is not None:
        monkeypatch.setattr(protect_hook, "repo_root", lambda: root)
    return protect_hook.main(json.dumps(event(path)))


def decision_of(capsys):
    return json.loads(capsys.readouterr().out)["hookSpecificOutput"]


def test_the_manifest_path_is_denied(tmp_path, capsys, monkeypatch):
    code = run_protect(
        tmp_path / "openspec" / "eval_manifest.json", tmp_path, monkeypatch
    )
    assert code == 0
    decision = decision_of(capsys)
    assert decision["permissionDecision"] == "deny"
    assert "regenerate" in decision["permissionDecisionReason"]


def test_a_change_evals_path_is_denied(tmp_path, capsys, monkeypatch):
    code = run_protect(
        tmp_path / "openspec" / "changes" / "demo" / "evals" / "x.json",
        tmp_path,
        monkeypatch,
    )
    assert decision_of(capsys)["permissionDecision"] == "deny"
    assert code == 0


def test_a_generated_test_path_is_denied(tmp_path, capsys, monkeypatch):
    code = run_protect(
        tmp_path / "tests" / "dspy_gate" / "generated" / "t.py",
        tmp_path,
        monkeypatch,
    )
    assert decision_of(capsys)["permissionDecision"] == "deny"
    assert code == 0


def test_an_artifacts_path_is_denied(tmp_path, capsys, monkeypatch):
    code = run_protect(
        tmp_path / "tools" / "dspy_gate" / "artifacts" / "demo" / "p.json",
        tmp_path,
        monkeypatch,
    )
    assert decision_of(capsys)["permissionDecision"] == "deny"
    assert code == 0


def test_a_visual_baseline_is_exempt(tmp_path, capsys, monkeypatch):
    code = run_protect(
        tmp_path / "openspec" / "specs" / "console" / "visual" / "b.png",
        tmp_path,
        monkeypatch,
    )
    assert code == 0
    assert capsys.readouterr().out == ""


def test_a_spec_path_passes_silent(tmp_path, capsys, monkeypatch):
    code = run_protect(
        tmp_path / "openspec" / "changes" / "demo" / "specs" / "x" / "spec.md",
        tmp_path,
        monkeypatch,
    )
    assert code == 0
    assert capsys.readouterr().out == ""


def test_malformed_input_passes_silent(capsys):
    assert protect_hook.main("not json") == 0
    assert capsys.readouterr().out == ""


def test_the_bridge_hook_reports_a_stale_generation(tmp_path, capsys, monkeypatch):
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
    code = bridge_hook.main(json.dumps(event(change / "specs" / "triage" / "spec.md")))
    out = capsys.readouterr().out
    assert code == 0
    assert "regen" in out


def test_the_bridge_hook_stays_silent_off_the_specs_tree(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(bridge_hook, "repo_root", lambda: tmp_path)
    code = bridge_hook.main(json.dumps(event(tmp_path / "tools" / "cli.py")))
    assert code == 0
    assert capsys.readouterr().out == ""


def test_the_protect_shim_denies_through_the_script(tmp_path):
    shim = REPO_ROOT / ".claude" / "hooks" / "spec-gates-protect.sh"
    payload = json.dumps(event(REPO_ROOT / "openspec" / "eval_manifest.json"))
    result = subprocess.run(
        ["bash", str(shim)],
        input=payload,
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(REPO_ROOT), "PATH": "/usr/bin:/bin"},
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_the_bridge_shim_runs_through_the_script():
    shim = REPO_ROOT / ".claude" / "hooks" / "spec-gates-bridge.sh"
    payload = json.dumps(event(Path("/unrelated/file.py")))
    result = subprocess.run(
        ["bash", str(shim)],
        input=payload,
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(REPO_ROOT), "PATH": "/usr/bin:/bin"},
    )
    assert result.returncode == 0
    assert result.stdout == ""
