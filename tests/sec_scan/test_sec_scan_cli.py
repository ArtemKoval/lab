"""The CLI of the scanner: argv in, report out, exits as documented."""

import sys
from pathlib import Path

import pytest

from tools.sec_scan import sec_scan


@pytest.fixture
def cli(monkeypatch):
    """Call main() with the argv given, returning its exit code."""

    def run(*argv: str) -> int:
        monkeypatch.setattr(sys, "argv", ["sec_scan", *argv])
        return sec_scan.main()

    return run


def test_the_cli_reports_a_planted_key_and_exits_2(cli, tmp_path):
    (tmp_path / "app.py").write_text(
        "key = " + repr("sk-or-v1-" + "a" * 64) + "\n"
    )
    assert cli("--json", "--root", str(tmp_path)) == 2


def test_the_cli_is_clean_on_an_empty_tree(cli, tmp_path):
    assert cli("--json", "--root", str(tmp_path)) == 0


def test_the_cli_prints_findings_as_text(cli, tmp_path, capsys):
    (tmp_path / "app.py").write_text(
        "key = " + repr("sk-or-v1-" + "a" * 64) + "\n"
    )
    cli("--root", str(tmp_path))
    out = capsys.readouterr().out
    assert "OpenRouter" in out and "revoke:" in out


def test_the_cli_names_a_missing_root(cli, tmp_path):
    assert cli("--root", str(tmp_path / "absent")) == 2


def test_history_on_a_non_repo_returns_nothing(cli, tmp_path):
    assert cli("--history", "--root", str(tmp_path)) == 0
