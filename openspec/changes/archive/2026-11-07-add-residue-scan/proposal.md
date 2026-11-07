# Proposal: add-residue-scan

## Why

esf tags every sandbox with origin and run id, and its leak scan exits
non-zero while a factory sandbox is alive. Cleanup in the feature pipeline is
manual today, and residue recurred: the worktree shared-ref lesson sits in
memory, and finished branches pile up across runs. Proposal P6 of
`reports/2026-11-07-issue-100-esf-analysis.md` asks for a stdlib CLI that
names the residue and exits non-zero while any of it is alive.

## What changes

- A new `tools/residue_scan/` package with the house CLI contract: pure
  classification in `core.py`, an injected runner in `cli.py`, exit 0 clean
  and 2 on residue or on a failed call. The scan is read-only. A `prune`
  subcommand deletes the reported worktrees first and the branches after.
- The classification: a typed local branch (`feat`, `fix`, `test`, `chore`,
  `docs`) whose pull request is merged is residue. A typed branch with no
  commits ahead of the mainline is residue. An open pull request keeps the
  branch in flight. Unmerged commits with no pull request are unclaimed work
  that the scan reports nowhere and never deletes.
- `tests/residue_scan/` covers the classification, the precedence, and the
  CLI paths through a fake runner.
- The `residue-scan` skill gives the commands, and the feature-pipeline
  skill names the scan in its cleanup step.
- CLAUDE.md gains the Projects line.

## Out of scope

- No remote deletion. The scan reads only local state and the gh PR lists.
- No registry unit. The tool needs only the existing git, gh, and the shared
  venv interpreter.
