# Proposal: add-long-context-proposals

## Why

The issue 95 analysis of the paper arXiv 2611.05306 on long context
ordered six proposals for the harness. The repository carries none of
the six. Issue 261 orders the adoption, and the analysis sits at
`reports/2026-11-07-issue-95-long-context-paper.md`. The paper shows
that carried semantic state and bounded reads hold accuracy at a high
compaction frequency, and every proposal is a small edit to a surface
this harness already carries. Confidence: observed.

## What Changes

- The `feature-pipeline` skill gains the ledger rule: a run that
  crosses several steps starts a `plan_exec` ledger and appends one
  entry at each step boundary.
- The `feature-pipeline` skill gains the selective-reading rule: a
  task with a long input saves the input to a file and reads it with
  targeted, bounded reads.
- The `feature-pipeline` inner loop gains the dispatch checklist:
  task verbatim, state and rejected options, file pointers, expected
  output shape, and one narrow retrieval command.
- `.claude/hooks/charter.md` gains two lines: re-establish the task
  state after a compaction, and keep tool output small.
- `.github/ISSUE_TEMPLATE/handover.md` gains the `## Dead ends`
  section, and the Observations comment separates verified facts from
  unverified ideas.
- `handover_telemetry` gains the context-size block: the per-call
  input-token median and peak beside the token sums. The transcripts
  carry per-call `input_tokens` fields, so the field set is final.
  Confidence: observed.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `intent-driven-harness`: one new requirement puts the ledger rule
  and the selective-reading rule in the pipeline. One modified
  requirement adds the dispatch checklist to the model-selection and
  dispatch rule. Two scenarios carry them.
- `handover-telemetry`: the report requirement gains the context-size
  block sentences, with two scenarios.

The charter lines and the handover-template section carry no new
delta. The `intent-driven-harness` template requirement pins a
minimum keep-list that the new section keeps, and no spec pins the
charter text. The enforcing tests pin both.

## Impact

- `openspec/specs/intent-driven-harness/spec.md` and
  `openspec/specs/handover-telemetry/spec.md` change through the
  archive sync of this change.
- `openspec/eval_manifest.json` changes through the bridge regen of
  this change.
- `.claude/skills/feature-pipeline/SKILL.md`,
  `.claude/hooks/charter.md`, and
  `.github/ISSUE_TEMPLATE/handover.md` change in the apply phase.
- `tools/handover_telemetry/` gains the median and peak computation
  and the report section, with its tests and a spec delta.
- `tests/claude_infra/` gains the pins for the pipeline rules, the
  charter lines, and the template section.
- The diff touches `.claude/hooks/charter.md`, a protected gate path,
  so the pull request body carries `gate-integrity: acknowledged`.
- The analysis orders the proposals as separate changes. Issue 261
  aggregates them, and the loop carries one change per issue, so this
  change reviews the batch as one unit, with one work area and one
  enforcing test set per proposal.
