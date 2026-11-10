# Proposal: add-pipeline-fast-mode

## Why

The feature-pipeline skill runs every change through the full
discipline: spec artifacts, up to three merge gates, the test matrix,
and the quality gates. A 1-1 decomposition session needs a working
prototype in minutes, and the full discipline costs more than the
prototype is worth. No reduced mode exists, so every prototype pays
the full price.

## What Changes

### Fast mode activation

The feature-pipeline skill reads a `fast:` prefix in its arguments.
The prefix selects fast mode for one invocation. Runs without the
prefix keep the full flow. The mode never switches mid-run.

### The fast-mode flow

Fast mode skips the spec artifacts, the new test matrix, the quality
gates, and the multi-agent review. Fast mode keeps the branch, the
pull request, the smoke run, the diff secret scan, and the local
suite run. The run merges when the local suite is green and does not
wait for CI. A skipped step that applies to the task becomes one debt
item. A fast task that touches a governed capability runs the normal
flow.

### The technical debt issue

A new `tech-debt` issue template at
`.github/ISSUE_TEMPLATE/tech-debt.md` carries the debt record. The run
opens one technical debt issue before the merge. The issue lists every
skipped step, gate, and test lane. Each listed skip is one debt item
with a next action. The issue stays open until a normal-pipeline run
pays the debt.

## Capabilities

### New Capabilities

None. The mode lives in the feature-pipeline skill, a harness surface
with no capability spec.

### Modified Capabilities

- `process-issues`: the classifier rule adds the title input and the
  tech-debt skip below the gate labels.

## Out of scope

- No mid-run mode switch. A switch needs a new invocation.
- No new gate tool, hook, or registry unit. The mode removes steps.
  The template, the classifier rule, and the guard tests are the only
  new files and rules.
- No change to the normal flow. Runs without the prefix keep every
  step and gate.
- The change does not create the `tech-debt` label. The operator owns
  label creation on this host.

## Impact

- `.claude/skills/feature-pipeline/SKILL.md`: a Fast mode section
  after the intro, and the `fast:` prefix in the description.
- `.github/ISSUE_TEMPLATE/tech-debt.md`: the new debt template.
- `CLAUDE.md`: one Workflow line about fast mode.
- `adr/0016-fast-mode-delivery-contract.md`: the durable delivery
  contract.
- `tools/process_issues/process_issues/core.py`: one skip rule for
  the `tech-debt:` title prefix in `classify`.
- `tools/process_issues/README.md`: one line for the skip rule.
- `tests/process_issues/test_process_issues_core.py`: one unit test
  for the skip rule.
- `tests/claude_infra/test_pipeline_rules.py`: guard tests that pin
  the rule sentences and the template sections.
- No registry unit and no spec delta.
