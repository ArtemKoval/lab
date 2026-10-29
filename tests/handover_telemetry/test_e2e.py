"""Opt-in live checks. Both tests skip without HANDOVER_TELEMETRY_E2E=1.
The first reads the real transcript directory. The second opens and
closes a throwaway issue when HANDOVER_TELEMETRY_E2E_E2E_REPO names a
repository, so the gh path sees a live round trip."""

import os
import subprocess

import pytest

from handover_telemetry import cli

GATE = "HANDOVER_TELEMETRY_E2E"
REPO_GATE = "HANDOVER_TELEMETRY_E2E_REPO"

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(os.environ.get(GATE) != "1", reason=f"opt-in through {GATE}=1"),
]


def test_real_transcript_scan_builds_a_report(capsys):
    code = cli.main(["build", "--json"])
    out = capsys.readouterr().out
    assert code == 0
    assert '"fingerprint"' in out


def test_live_gh_round_trip(tmp_path, monkeypatch, capsys):
    repo = os.environ.get(REPO_GATE)
    if not repo:
        pytest.skip(f"opt-in through {REPO_GATE}")
    monkeypatch.setenv("PATH", os.environ["PATH"])
    report = "# e2e\n\nThrowaway handover telemetry issue.\n"
    body = tmp_path / "body.md"
    body.write_text(report, encoding="utf-8")
    create = subprocess.run(
        [
            "gh",
            "issue",
            "create",
            "-R",
            repo,
            "--title",
            "handover-telemetry e2e throwaway",
            "--body-file",
            str(body),
        ],
        capture_output=True,
        text=True,
        timeout=60,
        shell=False,
    )
    assert create.returncode == 0, create.stderr
    url = create.stdout.strip()
    close = subprocess.run(
        ["gh", "issue", "close", "-R", repo, url],
        capture_output=True,
        text=True,
        timeout=60,
        shell=False,
    )
    assert close.returncode == 0, close.stderr
    assert url
