# Design: add-negative-instruction-audit-spec

## Context

The CLI at `tools/negative_instruction_audit/` shipped as a fast-mode
prototype and graduated through PR 207. It carries tests, CI wiring,
a README, and a CLAUDE.md Projects line. It carries no OpenSpec
capability spec. Issue 201 debt item 1 orders the spec change before
any wide harness-text conversion. The operator approved the change
with the `human-approved` label, so the loop runs propose and apply
in one pass.

## Goals / Non-Goals

**Goals:**

- One capability spec that pins the shipped behavior: the surface
  selection, the sentence split, the marker detection, the pin
  classification, the report, the outputs, the root selection, the
  exit codes, and the read-only guarantee.
- Every delta scenario maps to one test in the apply phase.
- `openspec validate ... --strict` stays green on the change and on
  the merged mainline.

**Non-Goals:**

- No behavioral eval for the core opinion. It waits until the
  operator orders a wide harness-text conversion.
- No wide conversion, no marker-set expansion, no code change, no
  registry unit, no `gates.yaml`/`rubrics/` (the harness registry
  declares no such capability), no CI change.

## Decisions

### D1. Spec-only change

The delta records observed behavior. The source file and the test
suite are the ground truth. The author round verified every claim
against the source. The review round verified the claims again and
counted 13 uncovered scenarios. The apply phase closes them.

### D2. The operator class map, recorded per debt item 1

Issue 201 debt item 1 asks design.md to record the operator's
class-by-class decision. The decision that the approval carries:

- Explicit prohibitions (`never`, `do not`, `don't`, `should not`,
  `must not`, `shall not`, `cannot`, `avoid`, and sentence-start
  `no`) sit in recall.
- The five miss classes (the bare-not contrast, the verb plus `no`,
  the positively-phrased prohibition, the only-conditional, and the
  before-conditional) stay out of recall by design. The README
  limits section owns the examples.
- Descriptive sentences that carry a marker word surface as
  candidates. The operator filters them.
- No conversion runs in the tool. The operator owns every conversion
  decision, class by class, when a wide conversion is ordered.

### D3. Root selection joins the delta

The review round found the `--repo-root` flag absent from the draft.
The flag is part of the CLI surface and the exit-2 message names it.
The delta carries one root-selection requirement with two scenarios.

### D4. Gap tests are an apply deliverable

The proposal no longer claims full test coverage. The apply phase
maps every scenario to a test and adds the 13 missing tests. The
tests-only diff keeps the production gate surface unchanged.

### D5. Builder-check settlements for the test author

The builder check raised 12 minor questions. Four landed in the
delta as tightenings. The rest settle by observation of the shipped
code:

- The 110-character cut covers the sentence text alone, with no
  ellipsis. The marker prefix stays outside the cut.
- The text totals line carries the five labels from the source
  format string. The tests assert the labels.
- The JSON `files` array carries every scanned file. The delta now
  pins it.
- The bullet-marker set is `-`, `*`, `+`, and digits with `.` or `)`
  after optional leading whitespace. The four markers in the scenario
  are examples, not the full set.
- The fence rule removes only triple-backtick fences. Inline code
  spans stay in the text. The charter hook goes through the same
  generic extraction.
- The sort key is the full path. The skill glob is one level deep.
- A bad `--repo-root` path exits 2 through the missing-tests rule.
  An unreadable surface file can raise outside the two pinned exit
  paths. No repo surface triggers it today. The delta pins the two
  paths the CLI owns.

### D6. Lightweight C4 context diagram

Format and rigor had no operator answer mid-loop. This design keeps
a lightweight C4-inspired ASCII context diagram and records the
assumption here.

```
                ┌────────────────────────────────────────────┐
                │        negative-instruction-audit          │
                │                [software system]           │
   [person]    │  ┌──────────────┐        ┌──────────────┐  │
  Operator ────┼─▶│ scan: harness│        │  pins from   │  │
   runs CLI    │  │ text files   │        │  tests/ tree │  │
   and reads   │  └──────┬───────┘        └──────┬───────┘  │
   report      │         │        sentences + pins │         │
                │         ▼                        │         │
                │  ┌──────────────────┐            │         │
                │  │  report: records │◀───────────┘         │
                │  │  totals, findings│                      │
                │  └────────┬─────────┘                      │
                └───────────┼────────────────────────────────┘
                            ▼
                 unpinned candidates
                            │
                            ▼
                   [person] Operator judges
                the candidates class by class
```

Boundaries: the CLI is one system. The operator sits outside it with
the judgment role. Responsibilities: the tool detects and
classifies, the operator judges. Assumption: lightweight rigor,
ASCII format, no operator answer on format mid-loop.

## Risks / Trade-offs

- The strict 500-character requirement lint may force a requirement
  split at write time. Mitigation: the bodies sit well under the
  bound, and validate runs before the proposal PR.
- The STE gate may reject a sentence at write time. Mitigation: the
  author and review rounds ran the mechanical rules, and the write
  passed the spec-ste hook.
- The miss-class scenario names the classes without examples. The
  README limits section owns the examples. The apply tests use the
  README shapes.

## Migration Plan

The archive step copies the delta into
`openspec/specs/negative-instruction-audit/spec.md`. No code
migration exists. The apply phase adds only tests.

## Open Questions

- None. The issue answers the scope. The conditional debt items stay
  open on issue 201 until the operator orders a wide conversion.
