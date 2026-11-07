# Proposal: add-blocked-state

## Why

esf makes "I cannot do this task" a first-class reported outcome, because
impossible tasks plus persistent agents produce out-of-bounds probing. The
loop equivalent is an issue that the loop retries without progress. Proposal
P3 of `reports/2026-11-07-issue-100-esf-analysis.md` asks for a `blocked`
state that the loop never retries and only the operator clears.

## What changes

- `tools/process_issues/process_issues/core.py` carries the `blocked` label
  in a table-driven precedence, between `handover` and `answered`. The scan
  reports the state `blocked` with the action `blocked`. The CLI needs no
  change, because the classification is label-driven.
- The process-issues skill carries the rule: when a run cannot proceed, it
  writes one structured reason comment on the issue and sets the label. The
  loop never retries a blocked issue. Only the operator clears the label.
- The skill's stale spec path moves to `openspec/specs/process-issues/`,
  where the archive of the original change put it.
- The spec gains the delta, and `tests/process_issues/` gains the cases.

## Out of scope

- No new CLI subcommand. The scan contract keeps its shape.
- No automatic clearing. Only the operator removes the label.
