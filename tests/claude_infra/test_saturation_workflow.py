"""Pin the saturation workflow: it runs the saturation pass CLI on a
weekly cron and on dispatch with a tools input, inside a timeout budget
and a concurrency group, behind the SATURATION_PASS_ENABLED escape
variable. The workflow enforces only: it uploads the JSON run report
and never writes the store, because the store moves only through pull
requests."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "saturation.yml"


def test_workflow_exists():
    assert WORKFLOW.is_file()


def test_workflow_triggers_on_the_weekly_cron_and_dispatch():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "cron: '37 4 * * 1'" in text
    assert "workflow_dispatch" in text
    assert "tools:" in text
    assert "--tool $tool" in text
    assert "TOOLS_INPUT: ${{ github.event.inputs.tools }}" in text


def test_workflow_carries_the_escape_variable():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "vars.SATURATION_PASS_ENABLED != 'false'" in text


def test_workflow_carries_the_timeout_and_concurrency():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "timeout-minutes: 90" in text
    assert "saturation-" in text
    assert "cancel-in-progress: false" in text


def test_workflow_builds_the_gate_venvs_and_the_shared_venv():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "python -m venv tools/zai_routing_audit/.venv" in text
    assert "python -m venv tools/crapper/.venv" in text
    assert "python -m venv tools/dryer/.venv" in text
    assert "python -m venv tools/mutator/.venv" in text


def test_workflow_runs_the_pass_with_the_json_report():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "--json target/saturation/report.json" in text


def test_workflow_uploads_the_report():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "target/saturation/report.json" in text
    assert "if: always()" in text
    assert "if-no-files-found: ignore" in text


def test_workflow_never_writes_the_store():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "git push" not in text
    assert "git commit" not in text
    assert "--init" not in text
    assert "--update" not in text
    assert "reports/saturation" not in text
