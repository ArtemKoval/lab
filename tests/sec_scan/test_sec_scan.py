"""The scanner's examinations, on synthetic same-shape fixture secrets.

Every provider-shaped fixture is assembled at test time from concatenated
fragments, so no provider-shaped literal ever lands in this repository for
push protection to block.
"""

import json
import subprocess
from pathlib import Path

import pytest

from tools.sec_scan.sec_scan import Report, scan_text, shannon_entropy

# Assembled at test time: the fragments never sit next to each other in a
# committed file.
OPENROUTER_KEY = "sk-or-v1-" + "a" * 64
AWS_KEY = "AKIA" + "IOSFODNN7EXAMPLE"[:16]
GITHUB_TOKEN = "ghp_" + "x" * 40
SLACK_TOKEN = "xoxb-" + "1234-" + "5678-" + "abcdefghijklmnop"


def scan(tmp_path: Path, body: str, name: str = "app.py") -> Report:
    target = tmp_path / name
    target.write_text(body, encoding="utf-8")
    report = Report()
    scan_text(name, body, report)
    return report


def test_an_openrouter_key_is_found_and_named(tmp_path):
    report = scan(tmp_path, f"key = {OPENROUTER_KEY!r}\n")
    [finding] = report.findings
    assert (finding.provider, finding.line) == ("OpenRouter", 1)
    assert finding.revoke_path.startswith("OpenRouter")


def test_an_aws_access_key_is_found(tmp_path):
    report = scan(tmp_path, f"id = {AWS_KEY!r}\n")
    assert report.findings[0].provider == "AWS access key"


def test_a_github_token_is_found(tmp_path):
    report = scan(tmp_path, f"token = {GITHUB_TOKEN!r}\n")
    assert report.findings[0].provider == "GitHub token"


def test_a_slack_token_is_found(tmp_path):
    report = scan(tmp_path, f"token = {SLACK_TOKEN!r}\n")
    assert report.findings[0].provider == "Slack token"


def test_a_private_key_block_is_found(tmp_path):
    report = scan(tmp_path, "-----BEGIN RSA PRIVATE KEY-----\nabc\n-----END-----\n")
    assert report.findings[0].provider == "private key"


def test_a_high_entropy_assignment_is_suspected(tmp_path):
    report = scan(tmp_path, 'API_KEY = "Zx9Q2mK7vLp4Rt8W1yB3nC6dF0gH5jSe"\n')
    [finding] = report.findings
    assert finding.provider == "unknown"
    assert "API_KEY" in finding.kind


def test_low_entropy_values_are_not_suspects(tmp_path):
    report = scan(tmp_path, "SECRET_NAME = 'the-support-team'\n")
    assert report.findings == []


def test_prose_is_not_a_finding(tmp_path):
    report = scan(tmp_path, "The API KEY name is long, but this line is prose.\n")
    assert report.findings == []


def test_line_numbers_count_from_one(tmp_path):
    report = scan(tmp_path, "one\ntwo\n" + f"key = {AWS_KEY!r}\n")
    assert report.findings[0].line == 3


def test_vendored_paths_are_skipped_by_the_walk(tmp_path):
    vendored = tmp_path / "node_modules" / "left-pad"
    vendored.mkdir(parents=True)
    (vendored / "index.js").write_text(f"key = {AWS_KEY!r}\n")
    from tools.sec_scan.sec_scan import scan_tree

    report = Report()
    scan_tree(tmp_path, report)
    assert report.findings == []


def test_history_finds_a_gone_key_with_its_commit(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    key_file = repo / "leaked.txt"

    def git(*args: str) -> None:
        subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)

    git("init")
    git("config", "user.email", "t@example")
    git("config", "user.name", "t")
    key_file.write_text(f"key = {AWS_KEY!r}\n")
    git("add", ".")
    git("commit", "-m", "the leak")
    key_file.unlink()
    git("add", "-A")
    git("commit", "-m", "remove the leak")

    from tools.sec_scan.sec_scan import scan_history

    report = Report()
    scan_history(repo, report)
    assert report.findings
    assert report.findings[0].commit
    assert report.findings[0].provider == "AWS access key"


def test_entropy_threshold_discriminates():
    assert shannon_entropy("aaaaaaaaaaaaaaaa") < 1.0
    assert shannon_entropy("Zx9Q2mK7vLp4Rt8W1yB3nC6dF0gH5jSe") > 3.5
