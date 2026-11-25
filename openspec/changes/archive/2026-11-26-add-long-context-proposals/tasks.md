# Tasks: add-long-context-proposals

## 1. The pipeline rules

- [x] 1.1 Add the ledger rule to the inner loop of
  `.claude/skills/feature-pipeline/SKILL.md`: a run that crosses
  several steps starts a `plan_exec` ledger and appends one entry at
  each step boundary. The rule names the obligation and points at the
  openspec-apply-change skill for the commands, which keep their
  authority.
- [x] 1.2 Add the selective-reading rule to the same skill: a task
  with a long input saves the input to a file and reads it with
  targeted, bounded reads, and never pastes whole documents into the
  conversation.
- [x] 1.3 Add the dispatch checklist to the inner loop: every agent
  brief carries the task verbatim, the state, the rejected options,
  the file pointers, the expected output shape, and one narrow
  retrieval command.
- [x] 1.4 Pin the three rules in
  `tests/claude_infra/test_pipeline_rules.py`.

## 2. The charter lines

- [x] 2.1 Add the two lines to `.claude/hooks/charter.md`. The first
  line sits in the Delivery contract section: after a compaction,
  re-establish the task state from the plan_exec ledger when one
  exists, from the change artifacts, and from git log before the next
  action. The second line sits in the Quality gates section: keep tool
  output small, and read a large output from a file in bounded
  windows.
- [x] 2.2 Pin the two lines section-scoped in
  `tests/claude_infra/test_harness_charter.py`.

## 3. The handover template

- [x] 3.1 Add the `## Dead ends` section to
  `.github/ISSUE_TEMPLATE/handover.md` after Observations and before
  Limitations, with a comment that names what a dead end records. The
  keep-list of the `intent-driven-harness` template requirement stays
  whole.
- [x] 3.2 Extend the Observations comment so it separates verified
  facts from unverified ideas.
- [x] 3.3 Pin the section and the comment line in
  `tests/claude_infra/test_working_rules.py`.

## 4. The telemetry context block

- [x] 4.1 Add the per-call input-token median and peak to
  `tools/handover_telemetry`, reading the `usage.input_tokens` field
  of the assistant messages.
- [x] 4.2 Render the context-size block in the markdown report and
  carry the fields in the JSON output.
- [x] 4.3 Add or extend the tests under `tests/handover_telemetry/`
  for the median, the peak, the empty-usage case, and the render. The
  empty-usage test pins the unit the median spans: the session's
  assistant messages, read as the run turns.

## 5. Gates and merge

- [x] 5.1 `openspec validate add-long-context-proposals --type change
  --strict` passes.
- [x] 5.2 `tools/spec_ste_check` passes on every artifact of this
  change.
- [x] 5.3 The root suite passes in the worktree. The lock-class
  `process_issues` failures the memory note names, counted at run
  time, do not count against this change.
- [x] 5.4 `python -m dspy_gate lint add-long-context-proposals` runs
  only when the registry governs a touched capability. Today the
  registry governs none of them, so the gate is not applicable.
