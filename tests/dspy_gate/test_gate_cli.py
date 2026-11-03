"""Tests for the CLI contract: subcommands, --json, and the exit
codes 0 on success and 2 on operational failure."""

import json
import textwrap

import pytest

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


def make_repo(tmp_path, spec_text=SPEC, policy_text=POLICY):
    change = tmp_path / "openspec" / "changes" / "demo"
    specs = change / "specs" / "triage"
    specs.mkdir(parents=True)
    (specs / "spec.md").write_text(textwrap.dedent(spec_text), encoding="utf-8")
    (tmp_path / "tools" / "dspy_gate" / "gates.yaml").parent.mkdir(parents=True)
    (tmp_path / "tools" / "dspy_gate" / "gates.yaml").write_text(
        textwrap.dedent(policy_text), encoding="utf-8"
    )
    return tmp_path


def run(argv, cwd, monkeypatch=None, validate_ok=True):
    """Run the CLI with the openspec subprocess stubbed out."""
    if monkeypatch is not None:
        monkeypatch.setattr(
            cli.lint,
            "openspec_validate",
            lambda change_dir: (validate_ok, "" if validate_ok else "bad"),
        )
        monkeypatch.setattr(
            cli, "_load_modules", lambda root: {"triage": {"module": "Triage"}}
        )
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
    assert run(["check-manifest", "demo"], root) == 2
    assert "no eval manifest" in capsys.readouterr().out


def test_verify_exits_2_when_generation_is_stale(tmp_path, capsys):
    root = make_repo(tmp_path)
    assert run(["verify", "demo"], root) == 2
    assert "stale" in capsys.readouterr().out


def test_unknown_command_exits_2(tmp_path):
    assert run(["frobnicate"], tmp_path) == 2


def test_lint_names_a_missing_change(tmp_path, capsys, monkeypatch):
    root = make_repo(tmp_path)
    assert run(["lint", "ghost"], root, monkeypatch) == 2
    assert "ghost" in capsys.readouterr().out
