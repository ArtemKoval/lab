# Proposal: add-confidence-discipline

## Why

Reports and handover issues state findings in prose, and an uncertain
claim looks the same as a verified one. The next run cannot tell a
measured fact from an inference, and it cannot see which questions the
run left open. Proposal P2 of
`reports/2026-11-10-issue-175-rea-analysis.md` requests the
discipline. The rea Evidence model grades every finding as observed,
derived, or inferred, keeps limitations in a list, and records an
unknown as a first-class item with a status.

## What Changes

### The confidence rules in the CLAUDE.md working rules

The working rules gain one bullet after the version-control bullet.
Every finding in a report or a handover issue carries a confidence of
observed, derived, or inferred. A limitation goes in a limitations
list, not in the finding text. An open unknown goes in a list with a
status and a next probe.

### The two lists in the handover template

The handover issue template gains two sections between Observations
and Follow-ups. `## Limitations` holds one line per limitation. `## Open
unknowns` holds one line per unknown with its question, its status,
and its next probe.

## Capabilities

### New Capabilities

None. The rules live in the working rules and the issue template, and
both are harness surfaces with no capability spec.

### Modified Capabilities

None. The `handover-telemetry` capability owns the telemetry block and
the CLI, not the issue conventions, so the change declares
`skip_specs` and carries no delta.

## Out of scope

- No authority enum. The report defers the rea authority classes,
  because the lab produces no provider artifacts to classify.
- No retrofit of existing reports and handover issues.
- No lint of report prose. The guard test pins the rule text and the
  template sections, and the suite fails on a removal.
- No change to the telemetry block. The telemetry sections keep their
  shape.

## Impact

- `CLAUDE.md`: one bullet in the working rules.
- `.github/ISSUE_TEMPLATE/handover.md`: the two new sections.
- `tests/claude_infra/test_working_rules.py`: one guard test for the
  rule bullet and one for the template sections.
- No code module, no registry unit, no README change, no spec delta.
