"""The diff scan: parser, rule reuse, literals, and the failure posture.

The fixtures are the same synthesized fragments the tree-scan tests use,
assembled at test time so no scanner-matching literal sits in this
repository.
"""

import hashlib
import subprocess

import pytest

from tools.sec_scan.sec_scan import (
    DiffScanError,
    Report,
    _env_literals,
    parse_diff,
    scan_diff,
)

OPENROUTER_KEY = "sk-or-v1-" + "b" * 64


class FakeRunner:
    def __init__(self, code, out, err=""):
        self.returncode = code
        self.stdout = out
        self.stderr = err

    def __call__(self, argv, cwd=None):
        self.argv = argv
        self.cwd = cwd
        return self


def test_parse_diff_collects_added_lines_with_new_numbers():
    text = (
        "diff --git a/app.py b/app.py\n"
        "index 111..222 100644\n"
        "--- a/app.py\n"
        "+++ b/app.py\n"
        "@@ -3,2 +12,2 @@\n"
        "-old line\n"
        "+new line one\n"
        "+new line two\n"
    )
    rows = parse_diff(text)
    assert rows == [
        ("app.py", 12, "new line one"),
        ("app.py", 13, "new line two"),
    ]


def test_parse_diff_skips_deletions_and_advances_on_context():
    text = (
        "--- a/app.py\n"
        "+++ b/app.py\n"
        "@@ -5 +7 @@\n"
        "-removed secret\n"
        "+kept line\n"
        " context line\n"
        "+after context\n"
    )
    rows = parse_diff(text)
    assert rows == [
        ("app.py", 7, "kept line"),
        ("app.py", 9, "after context"),
    ]


def test_parse_diff_skips_header_noise_between_files():
    text = (
        "diff --git a/one.py b/one.py\n"
        "--- a/one.py\n"
        "+++ b/one.py\n"
        "@@ -1 +1 @@\n"
        "+first\n"
        "diff --git a/two.py b/two.py\n"
        "index 1..2\n"
        "--- a/two.py\n"
        "+++ b/two.py\n"
        "@@ -40,1 +40,1 @@\n"
        "+second\n"
    )
    rows = parse_diff(text)
    assert rows == [
        ("one.py", 1, "first"),
        ("two.py", 40, "second"),
    ]


def test_parse_diff_ignores_deletion_files_and_newline_markers():
    text = (
        "--- a/gone.py\n"
        "+++ /dev/null\n"
        "@@ -1 +0,0 @@\n"
        "-gone line with sk-or-v1-value\n"
        "\\ No newline at end of file\n"
        "--- /dev/null\n"
        "+++ b/new.py\n"
        "@@ -0,0 +1 @@\n"
        "+born here\n"
    )
    rows = parse_diff(text)
    assert rows == [("new.py", 1, "born here")]


def test_parse_diff_handles_no_hunk_guard():
    text = (
        "--- a/app.py\n"
        "+++ b/app.py\n"
        "+early line with no hunk\n"
        "@@ -1 +5 @@\n"
        "+real line\n"
    )
    rows = parse_diff(text)
    assert rows == [("app.py", 5, "real line")]


def test_env_literals_split_and_drop_blanks():
    assert _env_literals(None) == []
    assert _env_literals("") == []
    assert _env_literals("  \n") == []
    assert _env_literals("one\n\ntwo\n") == ["one", "two"]


def test_scan_diff_finds_a_planted_key_on_its_added_line(tmp_path):
    diff = (
        "--- a/app.py\n"
        f"+++ b/app.py\n"
        "@@ -0,0 +12 @@\n"
        f"+token = '{OPENROUTER_KEY}'\n"
    )
    report = Report()
    scan_diff(tmp_path, "origin/main", report, literals=[], runner=FakeRunner(0, diff))
    [finding] = report.findings
    assert (finding.file, finding.line) == ("app.py", 12)
    assert finding.provider == "OpenRouter"


def test_scan_diff_ignores_a_key_outside_the_added_lines(tmp_path):
    diff = (
        "--- a/app.py\n"
        "+++ b/app.py\n"
        "@@ -1,2 +1,2 @@\n"
        f"-token = '{OPENROUTER_KEY}'\n"
        "+token = 'clean value'\n"
    )
    report = Report()
    scan_diff(tmp_path, "origin/main", report, literals=[], runner=FakeRunner(0, diff))
    assert report.findings == []


def test_scan_diff_reports_an_operator_literal_by_hash(tmp_path):
    literal = "zz-operator-literal-fixture-0000"
    diff = (
        "--- a/env.txt\n"
        "+++ b/env.txt\n"
        "@@ -0,0 +3 @@\n"
        f"+export APP_KEY={literal}\n"
    )
    report = Report()
    scan_diff(tmp_path, "origin/main", report, literals=[literal], runner=FakeRunner(0, diff))
    literal_findings = [f for f in report.findings if f.provider == "operator literal"]
    assert len(literal_findings) == 1
    finding = literal_findings[0]
    digest = hashlib.sha256(literal.encode("utf-8")).hexdigest()[:12]
    assert finding.kind == f"sha256:{digest}"
    assert literal not in finding.preview
    assert literal not in finding.kind


def test_scan_diff_fails_closed_when_git_fails(tmp_path):
    report = Report()
    with pytest.raises(DiffScanError):
        scan_diff(tmp_path, "origin/missing", report, literals=[], runner=FakeRunner(128, "", "bad ref"))


def test_cli_diff_mode_exits_2_on_a_finding(tmp_path, capsys, monkeypatch):
    from tools.sec_scan import sec_scan

    diff = (
        "--- a/app.py\n"
        "+++ b/app.py\n"
        "@@ -0,0 +1 @@\n"
        f"+key = {OPENROUTER_KEY}\n"
    )
    monkeypatch.delenv("SECRET_SCAN_LITERALS", raising=False)
    code = sec_scan.main(
        ["--root", str(tmp_path), "--diff", "origin/main"],
        runner=FakeRunner(0, diff),
    )
    assert code == 2
    assert "app.py:1" in capsys.readouterr().out


def test_cli_diff_mode_exits_0_on_a_clean_diff(tmp_path, capsys, monkeypatch):
    from tools.sec_scan import sec_scan

    monkeypatch.delenv("SECRET_SCAN_LITERALS", raising=False)
    code = sec_scan.main(
        ["--root", str(tmp_path), "--diff", "origin/main"],
        runner=FakeRunner(0, "--- a/x.py\n+++ b/x.py\n@@ -1 +1 @@\n+plain\n"),
    )
    assert code == 0
    assert "No findings." in capsys.readouterr().out


def test_cli_diff_mode_fails_closed_on_git_error(tmp_path, capsys):
    from tools.sec_scan import sec_scan

    code = sec_scan.main(
        ["--root", str(tmp_path), "--diff", "origin/missing"],
        runner=FakeRunner(128, "", "unknown revision"),
    )
    assert code == 2
    assert "diff scan failed" in capsys.readouterr().err


def test_default_runner_is_the_real_subprocess(tmp_path):
    from tools.sec_scan.sec_scan import _default_git_runner

    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    result = _default_git_runner(["git", "rev-parse", "--is-inside-work-tree"], cwd=str(tmp_path))
    assert result.returncode == 0
    assert result.stdout.strip() == "true"


def test_parse_diff_ignores_the_no_newline_marker_inside_a_hunk():
    text = (
        "--- a/env.txt\n"
        "+++ b/env.txt\n"
        "@@ -5 +5,2 @@\n"
        "-old_key = old\n"
        "\\ No newline at end of file\n"
        "+token = 'clean'\n"
        "+export NEW_KEY=0123456789abcdef\n"
    )
    rows = parse_diff(text)
    assert rows == [
        ("env.txt", 5, "token = 'clean'"),
        ("env.txt", 6, "export NEW_KEY=0123456789abcdef"),
    ]


def test_parse_diff_tracks_two_hunks_in_one_file_with_a_deletion_between():
    text = (
        "--- a/app.py\n"
        "+++ b/app.py\n"
        "@@ -2,1 +2,1 @@\n"
        "-gone\n"
        "+first add\n"
        "@@ -9,2 +10,2 @@\n"
        "-dropped\n"
        "+second add\n"
    )
    rows = parse_diff(text)
    assert rows == [
        ("app.py", 2, "first add"),
        ("app.py", 10, "second add"),
    ]


def test_scan_diff_matches_a_literal_with_regex_metacharacters(tmp_path):
    literal = "v1.key)(.*^$really"
    diff = (
        "--- a/env.txt\n"
        "+++ b/env.txt\n"
        "@@ -0,0 +1 @@\n"
        f"+value={literal}\n"
    )
    report = Report()
    scan_diff(tmp_path, "origin/main", report, literals=[literal], runner=FakeRunner(0, diff))
    literal_findings = [f for f in report.findings if f.provider == "operator literal"]
    assert len(literal_findings) == 1


def test_env_literals_deduplicate():
    assert _env_literals("one\none\ntwo\n") == ["one", "two"]


def test_new_path_strips_c_style_quotes():
    from tools.sec_scan.sec_scan import _new_path

    assert _new_path('+++ "b/quoted path.py"') == "quoted path.py"
    assert _new_path("+++ b/plain.py") == "plain.py"


def test_scan_history_returns_silently_when_git_fails(tmp_path):
    from tools.sec_scan.sec_scan import Report, scan_history

    report = Report()
    scan_history(tmp_path, report, runner=FakeRunner(128, "", "not a repo"))
    assert report.findings == []


def test_parse_diff_accepts_a_header_without_the_b_prefix():
    rows = parse_diff("--- a/app.py\n+++ app.py\n@@ -1 +1 @@\n+kept\n")
    assert rows == [("app.py", 1, "kept")]


def test_parse_diff_ignores_a_hunk_header_it_cannot_read():
    text = (
        "--- a/app.py\n"
        "+++ b/app.py\n"
        "@@ garbage @@\n"
        "+no hunk line number\n"
        "@@ -1 +4 @@\n"
        "+real line\n"
    )
    rows = parse_diff(text)
    assert rows == [("app.py", 4, "real line")]
