"""Pin the secret-scan workflow contract, as substring asserts."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _workflow_text():
    return (REPO_ROOT / ".github" / "workflows" / "secret-scan.yml").read_text(encoding="utf-8")


def test_the_workflow_has_no_paths_filter():
    text = _workflow_text()
    assert "pull_request:" in text
    assert "workflow_dispatch:" in text
    assert "paths-ignore" not in text
    assert "paths:" not in text.split("permissions:", 1)[0]
    assert "branches:" not in text.split("permissions:", 1)[0]


def test_the_scan_job_runs_the_diff_mode():
    text = _workflow_text()
    assert "timeout-minutes: 5" in text
    assert "fetch-depth: 0" in text
    assert "SECRET_SCAN_LITERALS: ${{ secrets.SECRET_SCAN_LITERALS }}" in text
    assert "python3 tools/sec_scan/sec_scan.py --root . --diff " in text
    assert "origin/$base" in text
    assert 'BASE_REF: ${{ github.base_ref }}' in text
    assert 'DISPATCH_BASE: ${{ inputs.base }}' in text
