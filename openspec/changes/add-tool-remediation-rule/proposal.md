# Proposal: add-tool-remediation-rule

## Why

The CLI contract in Step 2 of the feature-pipeline skill fixes exit
codes but says nothing about the failure text. A user who sees exit 2
does not always see the next action. Proposal P1 of
`reports/2026-11-10-issue-175-rea-analysis.md` requests the rule. The
rea error contract carries a remediation action that the producer
owns, and the report maps that discipline to the house tool contract.

## What Changes

### The remediation rule in Step 2 of the feature-pipeline skill

The CLI contract bullet list gains one rule. Every operational failure
names one next action in its message. A `--json` failure carries a
`remediation` field beside the exit code. New and touched tools adopt
the rule, so the house tools converge as the pipeline touches them.

## Capabilities

### New Capabilities

None. The rule lives in the feature-pipeline skill, and the skill is a
harness surface with no capability spec.

### Modified Capabilities

None. No spec-level behavior changes, so the change declares
`skip_specs` and carries no delta.

## Out of scope

- No retrofit of existing tools in this change. A tool adopts the rule
  when a change touches it.
- No error taxonomy. The report defers the rea tag algebra and the 27
  error tags, because the lab has no workload for them.
- No retryability field. The rea recovery union keeps retryability
  separate from remediation, and the house tools carry no retry
  machinery today.
- No mechanical enforcement in the gate tools. The guard test pins the
  rule text, and the suite fails on a removal.

## Impact

- `.claude/skills/feature-pipeline/SKILL.md`: one rule bullet in
  Step 2, after the CLI contract bullet.
- `tests/claude_infra/test_pipeline_rules.py`: one guard test with one
  assertion per rule sentence.
- No code module, no registry unit, no README change, no spec delta.
