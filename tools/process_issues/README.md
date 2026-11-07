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

The labels carry the state. The precedence is `handover`, `blocked`,
`answered`, `human-approved`, `waiting-human-approval`, then no label.

| State | Meaning |
| --- | --- |
| `skip` | The `handover` label sits on the issue. The loop never closes it. |
| `blocked` | The run could not proceed and left one structured reason comment. The loop never retries it, and only the operator clears the label. |
| `answered` | The loop answered this informational issue. |
| `wait-approval` | The spec gate waits for `human-approved`. |
| `apply` | Approved, with change artifacts. The loop runs the apply phase. |
| `propose` | No gate label. The action names the entry: `start`, `resume`, `repair`, or `propose-then-apply`. |

## Commands

```bash
PYTHONPATH=tools/process_issues tools/zai_routing_audit/.venv/bin/python -m process_issues scan
PYTHONPATH=tools/process_issues tools/zai_routing_audit/.venv/bin/python -m process_issues scan --json
PYTHONPATH=tools/process_issues tools/zai_routing_audit/.venv/bin/python -m process_issues acquire --holder LABEL
PYTHONPATH=tools/process_issues tools/zai_routing_audit/.venv/bin/python -m process_issues release --holder LABEL
```

Exit 0 on success, 2 on operational failure, and 64 on a usage error, with
the reason on stderr. The `--json` payload is a JSON array with `number`,
`title`, `labels`, `state`, `action`, `prs`, and `changeDir` per issue.

The CLI calls `gh issue list` and `gh pr list --state all`. A PR links to an
issue when its body carries a `Refs #NN` line. The `changeDir` field names
the active change directory whose id a linked PR branch carries as its last
path segment, with an optional `archive-` prefix.

## The loop lock

`acquire --holder LABEL` takes the run lock, and `release --holder LABEL`
drops it on an exact label match. `release --force` is the operator escape
for a lock whose holder is gone or hung. The scan examines the lock before
the first `gh` call: a fresh foreign lock exits 2 with the holder details,
and a scan that carries the label of the lock in force proceeds. The CLI
also accepts the scan of the session that holds the lock, because the
record pins the calling session anchor.

The lock file sits at `.process_issues/lock.json` under the primary checkout
root, resolved from the git common directory. The record carries the schema
version, the holder label, the host, the boot id, the process id, the
process start time, and the acquire time. The two times are ISO 8601 UTC
strings, and the version is the integer 1.

A stale lock never wedges the loop. The lock is stale when the record does
not parse, the schema version is unknown, the boot id differs from this
boot, the recorded process id no longer runs, the recorded start time
differs, or the acquire time is older than 24 hours. A stale lock draws a
report on stderr, the scan proceeds, and the next acquire clears it and
takes the lock. A lock with no recorded process id behaves like a foreign
host: fresh while young, stale at the age rule. A live but wedged holder
needs the operator: read the stderr details, stop the holder, and run
`release --force`.

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
