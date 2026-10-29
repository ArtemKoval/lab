"""Pin the tests CI workflow: it runs the root suite through the shared
repository venv, enforces the plan_exec and spec_ste_check coverage
floors, and lints both tools. Since adopt-ub-mode, CI also builds the
three gate tool venvs, runs their vendored suites, and gates the changed
repository Python: the mutator gate runs the changed product paths only,
with a worker cap and a step timeout as its budget. The gate uses
explicit diff-derived paths, never `--changed`."""

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
        "--cov plan_exec --cov spec_ste_check --cov handover_telemetry "
        "--cov-branch --cov-fail-under=100" in text
    )


def test_workflow_lints_the_tools():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "tools/zai_routing_audit/.venv/bin/ruff check tools/plan_exec" in text
    assert (
        "tools/zai_routing_audit/.venv/bin/ruff check tools/spec_ste_check" in text
    )
    assert "tools/zai_routing_audit/.venv/bin/ruff check tools/handover_telemetry" in text


def test_workflow_pins_python_3_12():
    assert "python-version: '3.12'" in WORKFLOW.read_text(encoding="utf-8")


def test_workflow_builds_the_gate_venvs_and_runs_their_suites():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "python -m venv tools/crapper/.venv" in text
    assert "python -m venv tools/dryer/.venv" in text
    assert "python -m venv tools/mutator/.venv" in text
    for tool in ("crapper", "dryer", "mutator"):
        assert f"tools/{tool}/.venv/bin/python -m pytest -q tools/{tool}/tests" in text


def test_workflow_gates_the_changed_python_with_explicit_paths():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "git diff --name-only" in text
    assert "tools/crapper/crapper --threshold 10 --use-existing-coverage $GATED_PATHS" in text
    assert "tools/dryer/dryer --threshold 0.8 --fail-above $product" in text
    # `--changed` reads the working tree, which is clean in CI.
    assert "--changed" not in text


def test_workflow_whitelists_the_gated_roots():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert (
        "grep -E '^(tools/(plan_exec|spec_ste_check|project_setup|devcontainer_init"
        "|handover_telemetry|handover_telemetry_setup)/|tests/)'"
        in text
    )
    # The whitelist is the only exclusion mechanism in the derive step.
    assert "grep -vE" not in text


def test_workflow_measures_coverage_over_the_gated_roots():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert (
        "--source=tools/plan_exec,tools/spec_ste_check,tools/project_setup,"
        "tools/devcontainer_init,tools/handover_telemetry,"
        "tools/handover_telemetry_setup,tests" in text
    )
    assert "coverage lcov" in text
    assert "-o target/coverage/python/lcov.info" in text


def test_workflow_runs_the_mutator_gate_on_product_paths():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "tools/mutator/mutator \\" in text
    assert "--use-existing-coverage" in text
    assert "--max-workers 4" in text
    assert "timeout-minutes: 20" in text
    assert (
        '--test-command "tools/zai_routing_audit/.venv/bin/python -m pytest -q tests"'
        in text
    )
    # mutmut stays out of CI; the vendored mutator owns the mutation gate.
    assert "mutmut" not in WORKFLOW.read_text(encoding="utf-8")
