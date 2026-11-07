"""Pure classification for the residue scan. No I/O lives here."""

BRANCH_TYPES = ("feat", "fix", "test", "chore", "docs")

RESIDUE = "residue"
IN_FLIGHT = "in-flight"
UNCLAIMED = "unclaimed"


def is_typed(name, types=BRANCH_TYPES):
    """Return True when the branch name carries a known type prefix."""
    if "/" not in name:
        return False
    return name.split("/", 1)[0] in types


def classify_branch(name, ahead, merged, opened):
    """Return (verdict, reason, pr_number) for one typed branch.

    `merged` and `opened` map branch name to PR number. The open map
    reads first, so a branch whose name a merged PR and a live open PR
    share stays in flight and the prune never touches it. A branch with
    no commits ahead of the mainline is residue, because a rebase or a
    reset left nothing unique on it. Anything else with unmerged commits
    is unclaimed work the operator may still want.
    """
    if name in opened:
        return IN_FLIGHT, "open", opened[name]
    if name in merged:
        return RESIDUE, "merged", merged[name]
    if ahead == 0:
        return RESIDUE, "empty", None
    return UNCLAIMED, "unclaimed", None


def collect_residue(branches, worktrees, merged, opened, types=BRANCH_TYPES):
    """Return the residue entries.

    `branches` carries (name, ahead_count) pairs, `worktrees` carries
    (path, branch) pairs, and `merged` and `opened` map branch name to
    PR number. A residue branch emits a branch entry, and every
    registered worktree of the branch emits a worktree entry after it.
    Untyped branches, in-flight branches, and unclaimed branches never
    appear.
    """
    entries = []
    residue_names = set()
    for name, ahead in branches:
        if not is_typed(name, types):
            continue
        verdict, reason, pr = classify_branch(name, ahead, merged, opened)
        if verdict != RESIDUE:
            continue
        entries.append({"kind": "branch", "name": name, "reason": reason, "pr": pr})
        residue_names.add(name)
    for path, branch in worktrees:
        if branch in residue_names:
            entries.append(
                {
                    "kind": "worktree",
                    "name": path,
                    "reason": "merged" if branch in merged else "empty",
                    "pr": merged.get(branch),
                }
            )
    return entries
