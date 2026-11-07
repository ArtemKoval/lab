# Design: add-residue-scan

## Plan review

The inner-loop review consulted the esf report, the house tool template
(`process_issues`), and the residue state of this repository. The review
settled these decisions:

- Residue needs a definition that never deletes live work. Three facts
  decide: the merged pull request list, the open pull request list, and the
  commit count against the mainline. The open list reads first, so a branch
  whose name a merged PR and a live open PR share stays in flight. A merged
  branch is residue. A branch with no commits ahead is residue, because a
  rebase or a reset left nothing unique on it. A squash merge shows up in
  the merged list instead. Unmerged commits with no pull request are
  unclaimed, and the tool leaves them alone.
- The pull request lists page through the full list with `--paginate`, so a
  page size can never hide a live open pull request and hand its branch to
  the prune.
- A failed worktree list fails the scan like the other fact calls, because a
  silently missing worktree entry would let the operator prune without
  seeing it.
- The prune removes worktrees before branches, because git refuses the
  deletion of a branch that its registered worktree still holds. The tool
  prints one refusal note per failed removal and exits 2 when any note
  exists.
- The exit contract follows the house findings shape: 0 clean or pruned, 2
  on residue, on a refusal, or on a failed git or gh call, with the reason
  on stderr. The scan names the PR number for merged branches, so the
  operator can trace every entry.
- The runner seam mirrors `process_issues`: the CLI takes one dispatchable
  runner over git and gh argv, so the tests stay hermetic with no network
  and no real git.
- No registry unit: the tool needs git, gh, and the shared venv interpreter,
  and the registry already carries all three. The project-setup completeness
  test stays green.

## ASIT pass

- Unification: the package shape, the runner seam, the conftest, and the
  mutmut config come from the `process_issues` template. The scan follows
  the `factory sandboxes` idea with the house exit shape.
- Division: pure classification (`core.py`) separates from the fact
  gathering (`cli.py`), so the verdicts test without I/O.
- Breaking symmetry: `scan` and `prune` are distinct subcommands, because
  reads and deletes sit at a trust boundary.
- No new dependency and no new component kind beyond one tool package.

## Spec delta

One new capability, `residue-scan`, with three requirements: the scan, the
prune, and the sources.
