"""Pin the spec-gates and dspy-nightly workflows: Gate 0 and Gate 1
on pull requests, the env-gated live suites, and the default-off
nightly learning run with the key refusal step."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_GATES = REPO_ROOT / ".github" / "workflows" / "spec-gates.yml"
NIGHTLY = REPO_ROOT / ".github" / "workflows" / "dspy-nightly.yml"


def test_the_spec_gates_workflow_exists():
    assert SPEC_GATES.is_file()


def test_the_spec_gates_workflow_runs_the_structural_gates():
    text = SPEC_GATES.read_text(encoding="utf-8")
    assert "openspec validate --changes --strict" in text
    assert "-m dspy_gate lint" in text
    assert "-m dspy_gate check-manifest" in text


def test_the_spec_gates_workflow_triggers_on_governed_paths():
    text = SPEC_GATES.read_text(encoding="utf-8")
    assert "pull_request" in text
    assert "'openspec/**'" in text
    assert "'tools/dspy_gate/**'" in text
    assert "workflow_dispatch" in text


def test_the_live_job_stays_env_gated():
    text = SPEC_GATES.read_text(encoding="utf-8")
    assert "vars.DSPY_GATE_LIVE == 'true'" in text
    assert "DSPY_GATE_E2E: '1'" in text
    assert "-m e2e tests/dspy_gate/test_journeys.py" in text
    assert "playwright install chromium" in text


def test_the_nightly_workflow_exists_and_is_default_off():
    text = NIGHTLY.read_text(encoding="utf-8")
    assert "cron:" in text
    assert "workflow_dispatch" in text
    assert "vars.DSPY_NIGHTLY_ENABLED == 'true'" in text


def test_the_nightly_workflow_refuses_a_missing_key():
    text = NIGHTLY.read_text(encoding="utf-8")
    assert "Refuse to run without the provider key" in text
    assert "secrets.ZAI_API_KEY" in text
    assert "-m dspy_gate nightly" in text
