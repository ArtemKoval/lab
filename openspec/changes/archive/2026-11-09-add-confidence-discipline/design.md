# Design: add-confidence-discipline

## Plan review

The review kept the report proposal as the plan. ASIT: Unification.
The working rules and the handover template exist, and the rules and
the two sections extend them. No new component enters the repository.

The placement decision: the rules live in one place. CLAUDE.md is the
conventions source of truth, and the charter hook injects it at every
session start, so a report-writing run sees the rule without a skill
lookup. The handover template carries the two lists, so the writer
sees the shape at write time. The feature-pipeline skill keeps its
existing handover step, and it gains no duplicate rule.

Alternatives the review rejected:

- The rules in the pipeline skill Step 13 only. A session that writes
  a report outside the pipeline steps would miss the rule, and the
  working rules already own the report and handover conventions.
- The authority enum from the rea Evidence model. The report defers
  it, and the lab produces no artifacts whose authority needs a class.
- A report linter. No owned gate examines prose, and the guard test
  on the rule text holds the discipline in place.

## The rule text

The bullet lands in the working rules after the version-control
bullet:

- Every finding in a report or a handover issue carries a confidence
  of observed, derived, or inferred. A limitation goes in a
  limitations list, not in the finding text. An open unknown goes in
  a list with a status and a next probe.

## Edge cases

- A report or issue with no limitations and no open unknowns keeps the
  two sections and writes `None` under each. The template comment
  names the shape.
- Handover issues and reports written before this change stay as they
  are. The rules bind new work.
- The telemetry block and the gate sections keep their rules. The new
  sections sit beside them, not inside them.

## Verification

`tests/claude_infra/test_working_rules.py` gains two tests. One
asserts the three rule sentences in the collapsed working-rules text.
One asserts the two template sections and the unknown line shape. A
removal fails the suite.
