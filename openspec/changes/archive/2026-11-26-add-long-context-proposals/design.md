# Design: add-long-context-proposals

## Cited lessons

- `worktree-shared-venv`: the worktree has no venvs. The apply phase
  runs the root suite with the main checkout zai interpreter, and the
  telemetry tests the same way.
- `spec-ste-gate-scope`: the STE gate scans every `.md` under the
  change dir. Every artifact passes `tools/spec_ste_check` before the
  push.
- `process-issues-live-lock-vs-suite`: the loop lock is live, so the
  worktree root suite shows the lock-class `process_issues` failures
  the memory note names, counted at run time. The run reads them as
  environmental, not as regressions.
- `mechanical-edit-verification`: one authority per identifier. Each
  rule text lands once, and the pin test arbitrates.

## Decisions

1. **One change, six work areas.** The analysis orders one change per
   proposal. Issue 261 aggregates the six, and the loop carries one
   change per issue. The batch reviews as one unit at the human gate.
   Each proposal keeps its own work area, its own enforcing test, and
   its own task. The rejection procedure at the gate: the operator
   names the rejected item on the issue, and the apply phase folds the
   edit into the deltas, because the newest human text wins. P1 and P4
   share the ADDED requirement, so the fold removes one item's
   sentences and keeps the other, and removes the whole requirement
   with its scenario only when the operator rejects both. P5's
   checklist sentence leaves the MODIFIED requirement body. P6's
   sentences and its two scenarios leave the telemetry block.
2. **Content surfaces carry no new delta.** The `intent-driven-harness`
   requirement at spec line 142 pins a minimum keep-list for the
   handover template: Task, Logs, Metrics, Observations, and
   Follow-ups. The `## Dead ends` section keeps that list whole, so no
   delta is needed. The section sits after Observations and before
   Limitations, because `test_working_rules.py` pins the Limitations,
   Open-unknowns, and Follow-ups block as one contiguous string. The
   charter text carries no spec pin either: the spec pins the script
   mechanics alone, and `test_harness_charter.py` pins the drift
   markers and the 40 to 60 line bound, which two added lines keep.
   The charter lines land inside the Delivery contract section and the
   Quality gates section, so the pin asserts section-scoped text.
3. **The pipeline rules land on `intent-driven-harness`.** That
   capability already carries two pipeline-governance requirements
   with reader-scan scenarios. The new requirement follows the same
   style, and the dispatch checklist joins the existing
   model-selection requirement, because the checklist governs the
   same dispatch act.
4. **The context block joins the report requirement.** The
   `handover-telemetry` report requirement already owns the token
   reporting. The per-call `input_tokens` field exists in every
   assistant message of the transcripts (verified on this host), so
   the median and peak need no parser change beyond reading that
   field. The median spans the session's assistant messages, which the
   implementation reads as the run turns, and the empty-usage test
   pins that unit.
5. **The ledger rule states the rule once.** The pipeline skill states
   the ledger obligation, and the openspec-apply-change skill keeps
   owning the `plan_exec` commands. One authority per surface: the
   skill rule names the obligation and links the apply skill, and no
   command guidance duplicates.
6. **P6 keeps the apply-phase verification.** The analysis asks the
   implementer to confirm the field before the field set is final.
   This propose phase confirmed it on the session transcript of
   2026-11-25, and the proposal records the confidence.

## Surface map

| Proposal | Surface | Change | Pin |
| --- | --- | --- | --- |
| P1 ledger rule | `.claude/skills/feature-pipeline/SKILL.md` | one rule in the inner loop | `test_pipeline_rules.py` |
| P2 charter lines | `.claude/hooks/charter.md` | two lines | `test_harness_charter.py` |
| P3 dead ends | `.github/ISSUE_TEMPLATE/handover.md` | one section, one comment line | `test_working_rules.py` |
| P4 reading rule | `.claude/skills/feature-pipeline/SKILL.md` | one rule | `test_pipeline_rules.py` |
| P5 dispatch checklist | `.claude/skills/feature-pipeline/SKILL.md` | one checklist in the inner loop | `test_pipeline_rules.py` |
| P6 context block | `tools/handover_telemetry/` | median, peak, report section, JSON fields | `tests/handover_telemetry/` |
