# Proposal: fix-strict-spec-validate-failures

## Why

`openspec validate --all --type spec --strict` fails on 4 of the 41
mainline spec items. Issue 221 orders the fix. The operator approved
the propose-then-apply flow for it.

Three failures are length faults. The strict lint limits one
requirement body to 500 characters. `handover-telemetry` carries one
body of 921 characters. `process-issues` carries three bodies of
1085, 698, and 749 characters. `session-statusline` carries one body
of 887 characters.

The fourth failure is not a length fault. The `saturation-pass` spec
still carries the archive placeholder in its Purpose. The validator
asks for a direct edit of the main spec, because a delta Purpose
applies only at capability creation.

A long body mixes several behaviors in one requirement. The split
keeps one behavior in the requirement sentence and moves the
examples into the requirement's scenarios. No requirement name
changes, so every scenario keeps its enforcing test.

## What Changes

- The change carries spec text only. No production code changes.
- `handover-telemetry`: the body of `The CLI names the run sources`
  shrinks to the source selection, the search order, the tie-break,
  and the exit 2 rule. All five scenarios stay in the requirement.
- `process-issues`: the bodies of `The scan CLI reports the queue`
  and `The status operator rows examine the loop` shrink to the
  print and exit rules and the operator rows. All eleven scenarios
  stay in their requirements. One new scenario `The lock gates the
  first fetch` pins the read order of the scan.
- `session-statusline`: the body of `The status line renders the
  session summary` shrinks to the payload read, the field rule, the
  separator, and the effort table. All ten scenarios stay in the
  requirement. Four new scenarios pin the table rows that no
  scenario carried: `none`, `low`, `high`, and `max`.
- Every existing scenario moves verbatim. No scenario text changes.
  The apply phase adds one test for the new lock-order scenario.
- `saturation-pass` gets no delta file. The apply phase replaces the
  placeholder Purpose through one direct edit of
  `openspec/specs/saturation-pass/spec.md`, exactly as the validator
  message instructs. This proposal documents the edit only.

## Capabilities

### New Capabilities

None. The change modifies three existing capabilities.

### Modified Capabilities

- `handover-telemetry`: the requirement body of `The CLI names the
  run sources` shrinks under the 500-character lint. The scenarios
  stay whole.
- `process-issues`: the requirement bodies of `The scan CLI reports
  the queue` and `The status operator rows examine the loop` shrink
  under the lint. One scenario joins the queue requirement.
- `session-statusline`: the requirement body of `The status line
  renders the session summary` shrinks under the lint. Four row
  scenarios join the requirement.

## Impact

- `openspec/specs/handover-telemetry/spec.md`,
  `openspec/specs/process-issues/spec.md`, and
  `openspec/specs/session-statusline/spec.md` change through the
  archive sync of this change.
- `openspec/specs/saturation-pass/spec.md` gets the real Purpose
  through one direct edit in the apply phase. No delta file carries
  that edit.
- No code change. The apply phase adds one test for the new
  lock-order scenario in `tests/process_issues/`, beside the
  existing refusal test.
- No `.claude/settings.json` change. The diff touches no protected
  gate path, so the pull request needs no `gate-integrity:
  acknowledged` line.
- No new unit in `tools/project_setup/registry.json`. All touched
  items exist in the clone.
- No dspy-gate `gates.yaml` and no rubrics. The harness registry
  declares no module for these three capabilities.
- Gate: after the archive merge, `openspec validate --all --type spec
  --strict` reports 0 failed.
