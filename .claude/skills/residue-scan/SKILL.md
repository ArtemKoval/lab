---
name: residue-scan
description: Clean the pipeline residue: name the branches and worktrees a finished run left behind, and delete them behind an explicit flag.
---

# residue-scan

The tool at `tools/residue_scan/` finds the branches and worktrees a
finished pipeline left behind. A typed local branch (`feat`, `fix`, `test`,
`chore`, `docs`) whose pull request is merged is residue. A typed branch
with no commits ahead of `main` is residue. An open pull request keeps the
branch in flight, and unmerged commits with no pull request are unclaimed
work that the tool never deletes. Everything without a type prefix is
invisible to the scan.

## Commands

```bash
VENV=tools/zai_routing_audit/.venv/bin/python
PYTHONPATH=tools/residue_scan $VENV -m residue_scan scan
PYTHONPATH=tools/residue_scan $VENV -m residue_scan scan --json
PYTHONPATH=tools/residue_scan $VENV -m residue_scan prune
```

## Reading the report

One line per entry: kind, name, reason, and the PR number for a merged
branch. Exit 0 clean, 2 on residue, on a refusal, or on a failed call with
the reason on stderr.

## Prune

The `prune` subcommand deletes the reported worktrees first and the branches
after, because git refuses the deletion of a branch that its worktree still
holds. A refusal prints one note on stderr, the rest still run, and the
prune exits 2 when any note exists. Review the scan output before you prune.
