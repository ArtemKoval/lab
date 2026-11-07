"""Behavior tests for the residue_scan CLI, with a fake runner."""

import json

from residue_scan import cli

MERGED_PRS = json.dumps(
    [{"number": 91, "headRefName": "feat/old"}]
)
OPEN_PRS = json.dumps([{"number": 95, "headRefName": "feat/open"}])

WT_PORCELAIN = (
    "worktree /repo\nbranch refs/heads/main\n"
    "worktree /repo/.claude/worktrees/feat+old\n"
    "branch refs/heads/feat/old\n"
)


class FakeRunner:
    """Answer calls by program and marker, in fixed order per key."""

    def __init__(self, answers):
        self.answers = answers
        self.calls = []

    def __call__(self, argv):
        self.calls.append(list(argv))
        program = argv[0]
        rest = " ".join(argv[1:])
        for marker, replies in self.answers.items():
            if marker in rest:
                if len(replies) > 1:
                    return replies.pop(0)
                return replies[0]
        return 1, "", f"no stub for {program}: {rest}"


def _repo_runner(extra=None):
    answers = {
        "for-each-ref": [
            (0, "feat/old\nfeat/open\nfeat/wip\nmain\ndocs/empty\nchore/empty\n", "")
        ],
        "rev-list --count main..feat/old": [(0, "2\n", "")],
        "rev-list --count main..feat/open": [(0, "3\n", "")],
        "rev-list --count main..feat/wip": [(0, "5\n", "")],
        "rev-list --count main..docs/empty": [(0, "0\n", "")],
        "rev-list --count main..chore/empty": [(0, "0\n", "")],
        "worktree": [(0, "worktree /repo\nbranch refs/heads/main\n", "")],
        "pr list --state merged": [(0, MERGED_PRS, "")],
        "pr list --state open": [(0, OPEN_PRS, "")],
    }
    if extra:
        answers.update(extra)
    return FakeRunner(answers)


def test_scan_json_reports_the_residue_entries(capsys):
    fake = _repo_runner()
    code = cli.main(["scan", "--json"], run=fake, repo_root="/repo")
    entries = json.loads(capsys.readouterr().out)
    assert code == 2
    assert entries == [
        {"kind": "branch", "name": "feat/old", "reason": "merged", "pr": 91},
        {"kind": "branch", "name": "docs/empty", "reason": "empty", "pr": None},
        {"kind": "branch", "name": "chore/empty", "reason": "empty", "pr": None},
    ]


def test_scan_plain_lines_carry_kind_name_and_reason(capsys):
    fake = _repo_runner()
    code = cli.main(["scan"], run=fake, repo_root="/repo")
    out = capsys.readouterr().out
    assert code == 2
    assert "branch\tfeat/old\tmerged (PR #91)" in out
    assert "branch\tdocs/empty\tempty" in out
    assert "feat/open" not in out
    assert "feat/wip" not in out


def test_a_clean_repository_exits_0(capsys):
    fake = _repo_runner(
        {
            "for-each-ref": [(0, "main\n", "")],
        }
    )
    code = cli.main(["scan"], run=fake, repo_root="/repo")
    assert code == 0
    assert "No residue." in capsys.readouterr().out


def test_a_failed_branch_list_exits_2_with_the_reason(capsys):
    fake = FakeRunner({"for-each-ref": [(128, "", "fatal: bad")]})
    code = cli.main(["scan"], run=fake, repo_root="/repo")
    assert code == 2
    assert "residue_scan" in capsys.readouterr().err


def test_a_failed_gh_call_exits_2_with_the_reason(capsys):
    fake = _repo_runner({"pr list --state merged": [(1, "", "auth required")]})
    code = cli.main(["scan"], run=fake, repo_root="/repo")
    assert code == 2
    assert "auth required" in capsys.readouterr().err


def test_a_failed_commit_count_exits_2_and_names_the_branch(capsys):
    fake = _repo_runner(
        {"rev-list --count main..feat/old": [(128, "", "bad revision")]}
    )
    code = cli.main(["scan"], run=fake, repo_root="/repo")
    assert code == 2
    assert "feat/old" in capsys.readouterr().err


def test_prune_deletes_the_branches_and_reports_success(capsys):
    fake = _repo_runner(
        {
            "branch -D feat/old": [(0, "", "")],
            "branch -D docs/empty": [(0, "", "")],
            "branch -D chore/empty": [(0, "", "")],
        }
    )
    code = cli.main(["prune"], run=fake, repo_root="/repo")
    out = capsys.readouterr().out
    assert code == 0
    assert "branch\tfeat/old" in out
    deletes = [call for call in fake.calls if "branch -D" in " ".join(call)]
    assert ["git", "-C", "/repo", "branch", "-D", "feat/old"] in deletes
    assert ["git", "-C", "/repo", "branch", "-D", "docs/empty"] in deletes
    assert ["git", "-C", "/repo", "branch", "-D", "chore/empty"] in deletes
    touched = " ".join(" ".join(call) for call in deletes)
    assert "feat/open" not in touched
    assert "feat/wip" not in touched
    assert "main" not in touched


def test_prune_removes_the_worktree_before_the_branch(capsys):
    fake = _repo_runner(
        {
            "worktree": [
                (0, WT_PORCELAIN, ""),
                (0, "", ""),
            ],
            "branch -D feat/old": [(0, "", "")],
            "branch -D docs/empty": [(0, "", "")],
            "branch -D chore/empty": [(0, "", "")],
        }
    )
    code = cli.main(["prune"], run=fake, repo_root="/repo")
    assert code == 0
    removes = [call for call in fake.calls if "worktree remove" in " ".join(call)]
    deletes = [call for call in fake.calls if "branch -D feat/old" in " ".join(call)]
    assert ["git", "-C", "/repo", "worktree", "remove", "/repo/.claude/worktrees/feat+old"] in removes
    assert ["git", "-C", "/repo", "branch", "-D", "feat/old"] in deletes
    assert fake.calls.index(removes[0]) < fake.calls.index(deletes[0]), (
        "the worktree removal must come before the branch deletion"
    )


def test_prune_reports_a_refused_removal_and_exits_2(capsys):
    fake = _repo_runner(
        {
            "branch -D feat/old": [(1, "", "error: the branch is checked out")],
            "branch -D docs/empty": [(0, "", "")],
            "branch -D chore/empty": [(0, "", "")],
        }
    )
    code = cli.main(["prune"], run=fake, repo_root="/repo")
    assert code == 2
    assert "checked out" in capsys.readouterr().err


def test_prune_reports_a_refused_worktree_and_exits_2(capsys):
    fake = _repo_runner(
        {
            "worktree": [
                (0, WT_PORCELAIN, ""),
                (1, "", "fatal: contains modified files"),
            ],
            "branch -D feat/old": [(0, "", "")],
            "branch -D docs/empty": [(0, "", "")],
            "branch -D chore/empty": [(0, "", "")],
        }
    )
    code = cli.main(["prune"], run=fake, repo_root="/repo")
    assert code == 2
    assert "modified files" in capsys.readouterr().err


def test_a_non_numeric_count_fails_the_scan(capsys):
    fake = _repo_runner(
        {"rev-list --count main..feat/old": [(0, "not-a-number\n", "")]}
    )
    code = cli.main(["scan"], run=fake, repo_root="/repo")
    assert code == 2
    assert "feat/old" in capsys.readouterr().err


def test_the_default_runner_dispatches_by_program(monkeypatch):
    seen = []

    def fake_tool(program, args):
        seen.append((program, list(args)))
        return 0, "", ""

    monkeypatch.setattr(cli, "_run_tool", fake_tool)
    assert cli.runner(["git", "--version"])[0] == 0
    assert cli.runner(["gh", "--version"])[0] == 0
    assert seen == [("git", ["--version"]), ("gh", ["--version"])]


def test_a_failed_worktree_list_fails_the_scan(capsys):
    fake = _repo_runner({"worktree": [(1, "", "fatal: not a repo")]})
    code = cli.main(["scan"], run=fake, repo_root="/repo")
    assert code == 2
    assert "worktree" in capsys.readouterr().err


def test_a_reused_branch_with_a_live_open_pr_stays_in_flight(capsys):
    fake = _repo_runner(
        {
            "pr list --state merged": [
                (0, json.dumps([{"number": 91, "headRefName": "feat/old"}]), "")
            ],
            "pr list --state open": [
                (0, json.dumps([{"number": 95, "headRefName": "feat/old"}]), "")
            ],
            "branch -D docs/empty": [(0, "", "")],
            "branch -D chore/empty": [(0, "", "")],
        }
    )
    code = cli.main(["prune", "--json"], run=fake, repo_root="/repo")
    entries = json.loads(capsys.readouterr().out)
    assert code == 0
    assert [entry["name"] for entry in entries] == ["docs/empty", "chore/empty"]
    deletes = [call for call in fake.calls if "branch -D" in " ".join(call)]
    assert all("feat/old" not in " ".join(call) for call in deletes), (
        "a branch with a live open PR must never be deleted"
    )
