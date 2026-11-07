"""Behavior tests for the residue classification in residue_scan.core."""

from residue_scan import core


def test_is_typed_knows_the_pipeline_types():
    for name in ("feat/x", "fix/y", "test/z", "chore/w", "docs/v"):
        assert core.is_typed(name) is True
    assert core.is_typed("main") is False
    assert core.is_typed("dependabot/x") is False
    assert core.is_typed("featx/y") is False


def test_a_merged_branch_is_residue_with_its_pr():
    verdict = core.classify_branch("feat/old", 3, {"feat/old": 91}, {})
    assert verdict == (core.RESIDUE, "merged", 91)


def test_an_open_pr_keeps_the_branch_in_flight():
    verdict = core.classify_branch("feat/wip", 3, {}, {"feat/wip": 95})
    assert verdict == (core.IN_FLIGHT, "open", 95)


def test_a_branch_with_no_commits_ahead_is_empty_residue():
    verdict = core.classify_branch("docs/merged-by-hand", 0, {}, {})
    assert verdict == (core.RESIDUE, "empty", None)


def test_unclaimed_commits_keep_the_branch_off_the_report():
    verdict = core.classify_branch("feat/wip", 4, {}, {})
    assert verdict == (core.UNCLAIMED, "unclaimed", None)


def test_collect_residue_names_the_branch_and_its_worktree():
    branches = [("feat/old", 2), ("main", 0)]
    worktrees = [("/repo/.claude/worktrees/feat+old", "feat/old")]
    entries = core.collect_residue(branches, worktrees, {"feat/old": 91}, {})
    assert entries == [
        {"kind": "branch", "name": "feat/old", "reason": "merged", "pr": 91},
        {
            "kind": "worktree",
            "name": "/repo/.claude/worktrees/feat+old",
            "reason": "merged",
            "pr": 91,
        },
    ]


def test_collect_residue_skips_untyped_in_flight_and_unclaimed():
    branches = [
        ("main", 0),
        ("feat/open", 2),
        ("feat/wip", 5),
        ("chore/empty", 0),
    ]
    worktrees = [("/somewhere", "main")]
    entries = core.collect_residue(
        branches, worktrees, {}, {"feat/open": 12}
    )
    assert entries == [
        {"kind": "branch", "name": "chore/empty", "reason": "empty", "pr": None}
    ]


def test_collect_residue_ignores_worktrees_of_non_residue_branches():
    branches = [("feat/wip", 4)]
    worktrees = [("/repo/.claude/worktrees/feat+wip", "feat/wip")]
    entries = core.collect_residue(branches, worktrees, {}, {})
    assert entries == []


def test_collect_residue_handles_detached_worktrees():
    branches = [("docs/empty", 0)]
    worktrees = [("/repo/.claude/worktrees/x", "")]
    entries = core.collect_residue(branches, worktrees, {}, {})
    assert entries == [{"kind": "branch", "name": "docs/empty", "reason": "empty", "pr": None}]
