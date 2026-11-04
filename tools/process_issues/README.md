# process_issues

A stdlib CLI that scans the open GitHub issues of this repo and classifies
each issue into one loop state. The `process-issues` skill reads the queue
and runs the `feature-pipeline` steps for one actionable issue at a time.
The capability spec lives at
`openspec/changes/add-process-issues/specs/process-issues/spec.md` until the
archive moves it under `openspec/specs/process-issues/`.

## Why

The operator files ideas as GitHub issues and wants one human spec-approval
gate per spec-carrying change. The scan makes the queue mechanical, so the
loop needs judgment only for the per-issue pipeline phases.

## States

The labels carry the state. The precedence is `handover`, `answered`,
`human-approved`, `waiting-human-approval`, then no label.

| State | Meaning |
| --- | --- |
| `skip` | The `handover` label sits on the issue. The loop never closes it. |
| `answered` | The loop answered this informational issue. |
| `wait-approval` | The spec gate waits for `human-approved`. |
| `apply` | Approved, with change artifacts. The loop runs the apply phase. |
| `propose` | No gate label. The action names the entry: `start`, `resume`, `repair`, or `propose-then-apply`. |

## Commands

```bash
PYTHONPATH=tools/process_issues tools/zai_routing_audit/.venv/bin/python -m process_issues scan
PYTHONPATH=tools/process_issues tools/zai_routing_audit/.venv/bin/python -m process_issues scan --json
```

Exit 0 on success and 2 on operational failure, with the reason on stderr.
The `--json` payload is a JSON array with `number`, `title`, `labels`,
`state`, `action`, `prs`, and `changeDir` per issue.

The CLI calls `gh issue list` and `gh pr list --state all`. A PR links to an
issue when its body carries a `Refs #NN` line. The `changeDir` field names
the active change directory whose id a linked PR branch carries as its last
path segment, with an optional `archive-` prefix.

## Known limits

The fetch window is 200 issues and 200 pull requests. Past that size, old
proposal PRs drop out of the scan, and repair and artifact detection degrade
silently.

The `gh label create` calls that the loop's label repair makes need the
label-write authority on the GitHub token. The tokens on this host lack that
authority, so the operator creates or repairs labels in the GitHub UI, or
grants the scope.

## Dependencies

Python 3.12 or newer, the Python standard library only, and the `gh` CLI
authenticated for this repo. The `gh-cli` unit in
`tools/project_setup/registry.json` carries the setup contract.

## Tests and gates

```bash
tools/zai_routing_audit/.venv/bin/python -m pytest tests/process_issues -o addopts=
tools/zai_routing_audit/.venv/bin/ruff check tools/process_issues
```

The mutation run works on an out-of-tree copy of this directory, never
inside the repository. The `tools/process_issues/pyproject.toml` file
carries the mutmut config.
