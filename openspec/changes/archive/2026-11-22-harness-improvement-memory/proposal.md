## Why

The harness improves itself through a loop that forgets its own attempts.
A lesson carries its rule and one anecdote, but no ledger of the attempts
that followed it: what the rule predicted, what happened, and in which
setting. The pipe lesson of 2026-11-07 re-bit on 2026-11-20 through a
background-chain shape, and the ledger that would have caught the new shape
was absent. Consultation stays a nudge in the inner-loop text, so plans
touch surfaces whose lessons they never cite. The paper arXiv 2611.18856
showed the cost of this shape. Memory that carries diagnoses without
evidence scores below no memory in one setting. The full record beats
harness-only continuation in all ten tested transfer settings. The analysis
report `reports/2026-11-20-sim-harness-adoption.md` mapped the paper onto
this harness and the operator approved its adoption design.

## What Changes

- Lesson records gain an attempt ledger. Each lesson names its recurring
  problem in one line. Each attempt records the date, the session, the
  trigger, the prediction, the observation, the setting, and a verdict of
  holds, misled, or superseded.
- Inner-loop step 2 names the consultation act: the plan pulls every lesson
  whose problem names the touched surface and cites it. The review round
  holds the teeth: a plan that cites no lesson while it touches a surface
  that owns one is a review finding.
- The inner-loop result review and the merge-time hook carry the write-back:
  the next occurrence of a problem records the observed outcome on the
  lesson it cited, with a verdict.
- Step 14 amends its skip rule for this write-back, so the pipeline carries
  no step that contradicts its own skip text.
- The agent-memory kit's Mode 5 gains the recurrence rule for store lessons:
  the first recurrence appends the attempt to the lesson issue body.
- The ten oldest host-memory lessons convert to the ledger format, and their
  index lines gain the problem and the setting. The conversion runs
  host-side during apply, outside this repository.

## Capabilities

### New Capabilities

- `harness-improvement-memory`: the lesson-record format and the
  consultation, write-back, and skip-rule discipline of the harness
  improvement loop, across the feature-pipeline text, the agent-memory kit,
  and the merge-time hook.

### Modified Capabilities

- None. No existing capability covers these surfaces, and the
  negative-instruction-audit scan stays read-only with no repo-count pins.

## Impact

- `.claude/skills/feature-pipeline/SKILL.md` — inner-loop step 2, result
  review step 4, and the Step 14 Reflect sub-step and its header skip rule.
- `.claude/skills/agent-memory/SKILL.md` — Mode 5 gains the recurrence
  append rule.
- `.claude/hooks/agent-memory-task-complete.sh` — the fixed nudge string
  gains the write-back line. The path sits inside the protected set of
  `tests/claude_infra/test_gate_integrity.py`, so the pull request body
  carries `gate-integrity: acknowledged` at creation time.
- Host memory (outside this repository): ten lesson files and ten MEMORY.md
  index lines convert during apply. No repo file pins their format. The
  agent-memory kit text and this capability own the convention.
- `adr/0021-harness-lessons-carry-attempt-ledgers.md` — the new ADR lands
  with the implementation.
- No code, no dependencies, and no governed dspy-gate module changes. The
  negative-instruction-audit report grows by the new sentences, with no
  failing pin.
