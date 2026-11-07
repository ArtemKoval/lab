# residue_scan

A stdlib CLI that finds the branches and worktrees a finished pipeline left
behind, and deletes them behind an explicit flag. It mirrors the leak scan of
esf: every piece of pipeline state carries its origin, and a finished piece
still alive is residue.

## What counts as residue

The scan examines local branches that carry a pipeline type prefix (`feat`,
`fix`, `test`, `chore`, `docs`), the registered worktrees, and the pull
requests GitHub knows:

- A branch whose pull request is merged is residue.
- A branch with no commits ahead of the mainline is residue, because its
  content is already merged or gone.
- A branch with an open pull request stays in flight.
- A branch with unmerged commits and no pull request is unclaimed work. The
  scan never counts it as residue and never deletes it.
- Everything without a type prefix, `main` included, is invisible to the
  scan.

A residue branch whose worktree is still registered adds a worktree entry,
one per registered worktree. The open pull request list reads first, so a
branch name that a merged PR and a live open PR share stays in flight. The
pull request lists carry a limit of 500, and a list that fills the limit
refuses to classify, so a truncation can never hand a live branch to the
prune. Without gh authentication every scan exits 2 with the reason, which
is not a residue verdict. The `--repo-root` flag scopes the git calls only,
so run the tool from the repository when the pull request maps must match.

## Commands

```bash
PYTHONPATH=tools/residue_scan tools/zai_routing_audit/.venv/bin/python -m residue_scan scan
PYTHONPATH=tools/residue_scan tools/zai_routing_audit/.venv/bin/python -m residue_scan scan --json
PYTHONPATH=tools/residue_scan tools/zai_routing_audit/.venv/bin/python -m residue_scan prune --json
```

`scan` is read-only and prints one line per entry: kind, name, reason, and
the pull request when one exists. `prune` deletes the residue: the worktrees
first, because git refuses the deletion of a branch that its worktree still
holds, then the branches. Exit 0 when the repository is clean or the prune
succeeded, and 2 when residue was found, a refusal happened, or a git or gh
call failed, with the reason on stderr. `--base` names the mainline ref, and
`--repo-root` names the repository for the git calls.

## Tests and gates

```bash
PYTHONPATH=tools/residue_scan tools/zai_routing_audit/.venv/bin/python -m pytest tests/residue_scan
```

The suite is hermetic: the git and gh calls go through an injected runner.
The mutation gate runs on an out-of-tree copy, never inside the repository.
