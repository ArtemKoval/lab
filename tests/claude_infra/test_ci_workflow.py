"""Pin the tests CI workflow: it runs the root suite through the shared
repository venv, enforces the plan_exec coverage floor, and lints the
tool. Mutation stays a local gate and appears nowhere here."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "tests.yml"


def test_workflow_exists():
    assert WORKFLOW.is_file()


def test_workflow_triggers_without_an_fde_allowlist():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "pull_request" in text
    assert "workflow_dispatch" in text
    assert "paths-ignore" in text
    assert "'fde/**'" in text
    assert "'llm_ops/**'" in text


def test_workflow_runs_the_suite_through_the_repo_venv():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "python -m venv tools/zai_routing_audit/.venv" in text
    assert "pip install -r tools/zai_routing_audit/requirements-dev.txt" in text
    assert (
        "tools/zai_routing_audit/.venv/bin/python -m pytest "
        "--cov plan_exec --cov-branch --cov-fail-under=100" in text
    )


def test_workflow_lints_plan_exec():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "tools/zai_routing_audit/.venv/bin/ruff check tools/plan_exec" in text


def test_workflow_pins_python_3_12():
    assert "python-version: '3.12'" in WORKFLOW.read_text(encoding="utf-8")


def test_workflow_does_not_run_mutation():
    text = WORKFLOW.read_text(encoding="utf-8").lower()
    assert "mutmut" not in text
    assert "mutation" not in text
