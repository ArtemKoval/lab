# Design: fix-strict-spec-validate-failures

## Context

Four mainline spec items fail the strict validate: three carry
requirement bodies over the 500-character lint, and saturation-pass
carries the archive placeholder in its Purpose. Issue 221 orders the
fix, and the operator approved the propose-then-apply flow.

## Goals / Non-Goals

**Goals:** all 41 items pass `openspec validate --all --type spec
--strict`. Every scenario keeps its enforcing test.

**Non-Goals:** no code change, no new requirement names, no gates
artifacts (no governed capability), no marker or behavior change.

## Decisions

### D1. No requirement splits

The first draft split long requirements into new requirements. The
strict validator rejects that shape: a MODIFIED block replaces the
whole requirement, so scenarios moved to a new requirement would
drop from the original at archive. The final shape follows the issue
text: one behavior stays in the requirement sentence, and the
examples and edge cases move into the requirement's scenarios.

### D2. Scenario-faithful assembly

Every existing scenario copy is sliced from the mainline by a
script, never retyped. A verbatim comparison confirms all 26 existing
scenarios appear exactly once, verbatim. Four new statusline row
scenarios and one new lock-order scenario join. Each new scenario
holds a test or gets one in apply.

### D3. The saturation Purpose edit

The validator names the method: replace the placeholder by editing
`openspec/specs/saturation-pass/spec.md` directly. A delta Purpose
applies only at capability creation. The apply phase carries the
edit.

### D4. Review roles

One adversarial author round and one adversarial reviewer round ran
on the drafts. The reviewer verified the test coverage of every new
scenario and caught the split-shape fault, and it served as the
builder check for this spec-only change.

## Risks / Trade-offs

- The body trims drop sentences that scenarios already pin. The
  verbatim comparison and the validator arbitrate. A body sentence with
  no scenario and no test keeps its place.
- The lock-order scenario needs one new test in apply. The refusal
  test pattern in the same file pins call order with a stub index.

## Migration Plan

The archive sync rewrites the three requirements in the mainline
specs. The apply phase edits the saturation Purpose. No code
migration.

## Open Questions

- None. The issue answers the scope.
