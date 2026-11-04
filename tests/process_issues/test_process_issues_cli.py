"""Behavior tests for the scan CLI in process_issues.cli."""

import json
from types import SimpleNamespace

from process_issues import cli

ISSUES_JSON = json.dumps(
    [
        {
            "number": 86,
            "title": "Process Issues Skill",
            "createdAt": "2026-11-04T08:00:00Z",
            "labels": [{"name": "human-approved"}],
        },
        {
            "number": 85,
            "title": "cc-logging hook writes no logs",
            "createdAt": "2026-11-04T07:00:00Z",
            "labels": [],
        },
    ]
)

PRS_JSON = json.dumps(
    [
        {
            "number": 88,
            "state": "MERGED",
            "headRefName": "feat/add-process-issues",
            "body": "Refs #86",
        },
        {
            "number": 90,
            "state": "OPEN",
            "headRefName": "fix/cc-logging",
            "body": "Refs #85",
        },
    ]
)


class FakeGh:
    def __init__(self, calls):
        self.calls = calls
        self.index = 0

    def __call__(self, args):
        if self.index >= len(self.calls):
            return 1, "", "no more stubbed calls"
        code, out, err = self.calls[self.index]
        self.index += 1
        return code, out, err


def test_scan_json_reports_queue_oldest_first(capsys):
    fake = FakeGh([(0, ISSUES_JSON, ""), (0, PRS_JSON, "")])
    code = cli.main(["scan", "--json"], runner=fake, repo_root=".")
    out = capsys.readouterr().out
    assert code == 0
    entries = json.loads(out)
    assert isinstance(entries, list)
    assert [e["number"] for e in entries] == [85, 86]
    assert entries[0]["state"] == "propose"
    assert entries[0]["action"] == "resume"
    assert entries[0]["prs"] == [{"number": 90, "state": "open", "branch": "fix/cc-logging"}]
    assert entries[1]["state"] == "apply"
    assert entries[1]["action"] == "apply"
    assert entries[1]["changeDir"] == "add-process-issues"


def test_scan_plain_lines_carry_state_and_links(capsys):
    fake = FakeGh([(0, ISSUES_JSON, ""), (0, PRS_JSON, "")])
    code = cli.main(["scan"], runner=fake, repo_root=".")
    out = capsys.readouterr().out
    assert code == 0
    assert "86\tapply" in out
    assert "#88 merged" in out
    assert "#90 open" in out


def test_scan_plain_lines_carry_state(capsys):
    fake = FakeGh(
        [
            (0, json.dumps([{"number": 12, "title": "T", "createdAt": "x", "labels": [{"name": "handover"}]}]), ""),
            (0, "[]", ""),
        ]
    )
    code = cli.main(["scan"], runner=fake, repo_root=".")
    out = capsys.readouterr().out
    assert code == 0
    assert "12" in out and "skip" in out


def test_pr_body_match_respects_number_boundary(capsys):
    issues = json.dumps(
        [{"number": 8, "title": "T", "createdAt": "x", "labels": []}]
    )
    prs = json.dumps(
        [{"number": 86, "state": "open", "headRefName": "b", "body": "Refs #86"}]
    )
    fake = FakeGh([(0, issues, ""), (0, prs, "")])
    code = cli.main(["scan", "--json"], runner=fake, repo_root=".")
    entries = json.loads(capsys.readouterr().out)
    assert code == 0
    assert entries[0]["prs"] == []
    assert entries[0]["action"] == "start"


def test_artifact_link_comes_from_branch_name(capsys, tmp_path):
    changes = tmp_path / "openspec" / "changes"
    (changes / "add-process-issues").mkdir(parents=True)
    (changes / "archive").mkdir()
    issues = json.dumps(
        [{"number": 30, "title": "T", "createdAt": "x", "labels": [{"name": "human-approved"}]}]
    )
    prs = json.dumps(
        [
            {
                "number": 31,
                "state": "merged",
                "headRefName": "feat/add-process-issues",
                "body": "Refs #30",
            }
        ]
    )
    fake = FakeGh([(0, issues, ""), (0, prs, "")])
    code = cli.main(["scan", "--json"], runner=fake, repo_root=str(tmp_path))
    entries = json.loads(capsys.readouterr().out)
    assert code == 0
    assert entries[0]["changeDir"] == "add-process-issues"
    assert entries[0]["state"] == "apply"


def test_gh_failure_exits_2_and_names_the_failure(capsys):
    fake = FakeGh([(1, "", "gh: auth error")])
    code = cli.main(["scan"], runner=fake, repo_root=".")
    err = capsys.readouterr().err
    assert code == 2
    assert "gh: auth error" in err


def test_bad_issue_json_exits_2(capsys):
    fake = FakeGh([(0, "not json", ""), (0, "[]", "")])
    code = cli.main(["scan"], runner=fake, repo_root=".")
    assert code == 2


def test_bad_pr_json_exits_2(capsys):
    fake = FakeGh([(0, "[]", ""), (0, "not json", "")])
    code = cli.main(["scan"], runner=fake, repo_root=".")
    assert code == 2


def test_run_gh_builds_the_argv_and_returns_the_tuple(monkeypatch):
    seen = {}

    def fake_run(argv, **kwargs):
        seen["argv"] = argv
        seen["kwargs"] = kwargs
        return SimpleNamespace(returncode=3, stdout="out", stderr="err")

    monkeypatch.setattr(cli.subprocess, "run", fake_run)
    code, out, err = cli.run_gh(["issue", "list"])
    assert seen["argv"] == ["gh", "issue", "list"]
    assert seen["kwargs"]["capture_output"] is True
    assert seen["kwargs"]["text"] is True
    assert seen["kwargs"]["check"] is False
    assert (code, out, err) == (3, "out", "err")


def test_scan_without_openspec_dir_reports_no_change_dir(capsys, tmp_path):
    fake = FakeGh([(0, "[]", ""), (0, "[]", "")])
    code = cli.main(["scan", "--json"], runner=fake, repo_root=str(tmp_path))
    entries = json.loads(capsys.readouterr().out)
    assert code == 0
    assert entries == []


def test_scan_defaults_repo_root_to_cwd(capsys):
    fake = FakeGh([(0, "[]", ""), (0, "[]", "")])
    code = cli.main(["scan", "--json"], runner=fake)
    assert code == 0


def test_scan_excludes_archive_and_hidden_change_dirs(capsys, tmp_path):
    changes = tmp_path / "openspec" / "changes"
    (changes / "archive").mkdir(parents=True)
    (changes / ".stash").mkdir()
    (changes / "add-x").mkdir()
    (changes / "notes.md").touch()
    prs = json.dumps(
        [
            {
                "number": 40,
                "state": "merged",
                "headRefName": "feat/archive-x",
                "body": "Refs #40",
            },
            {
                "number": 41,
                "state": "open",
                "headRefName": "chore/.stash-cleanup",
                "body": "Refs #41",
            },
            {
                "number": 42,
                "state": "open",
                "headRefName": "feat/notes.md",
                "body": "Refs #42",
            },
        ]
    )
    issues = json.dumps(
        [
            {"number": 40, "title": "A", "createdAt": "x", "labels": []},
            {"number": 41, "title": "B", "createdAt": "y", "labels": []},
            {"number": 42, "title": "C", "createdAt": "z", "labels": []},
        ]
    )
    fake = FakeGh([(0, issues, ""), (0, prs, "")])
    code = cli.main(["scan", "--json"], runner=fake, repo_root=str(tmp_path))
    entries = json.loads(capsys.readouterr().out)
    assert code == 0
    assert all(entry["changeDir"] is None for entry in entries)


def test_scan_rejects_a_branch_that_only_extends_the_change_id(capsys, tmp_path):
    changes = tmp_path / "openspec" / "changes"
    (changes / "add-x").mkdir(parents=True)
    issues = json.dumps(
        [{"number": 50, "title": "T", "createdAt": "x", "labels": []}]
    )
    prs = json.dumps(
        [
            {
                "number": 51,
                "state": "MERGED",
                "headRefName": "feat/add-x-other",
                "body": "Refs #50",
            }
        ]
    )
    fake = FakeGh([(0, issues, ""), (0, prs, "")])
    code = cli.main(["scan", "--json"], runner=fake, repo_root=str(tmp_path))
    entries = json.loads(capsys.readouterr().out)
    assert code == 0
    assert entries[0]["changeDir"] is None


def test_gh_missing_binary_exits_2_and_names_the_failure(capsys, monkeypatch):
    def raising_run(argv, **kwargs):
        raise FileNotFoundError(2, "No such file", "gh")

    monkeypatch.setattr(cli.subprocess, "run", raising_run)
    code = cli.main(["scan"], repo_root=".")
    err = capsys.readouterr().err
    assert code == 2
    assert "the gh call failed" in err


def test_normalize_pr_states_skips_entries_without_a_state():
    prs = [{"state": "MERGED"}, {"number": 1}, "not-a-dict"]
    cli.normalize_pr_states(prs)
    assert prs[0]["state"] == "merged"
    assert prs[1] == {"number": 1}
    assert prs[2] == "not-a-dict"
