## Why

Proposal 4 of `reports/2026-11-08-issue-123-saturation-testing-analysis.md`
asked for the measurement to reach the remaining owned tools. The
`add-saturation-ratchet` change delivered that measurement: its
baseline pass covered all nine Python-bearing tools and landed the
store at `reports/saturation/scores.json`. This change records the
outcome in the analysis report, so the measurement and its review sit
beside the original two-tool sample they extend.

## What Changes

- The analysis report gains a baseline section: the per-tool table,
  the weakest modules with their scores and site counts, the ratchet
  implications, and the open questions the run produced.
- The report correction section stays as it is. The baseline section
  extends the measurement, it does not revise it.
- The follow-ups the review names land in the run's handover issue,
  not in this report.

## Capabilities

### New Capabilities

None. The saturation-pass capability already carries the pass, the
store, and the ratchet.

### Modified Capabilities

None. No behavior changes.

## Impact

- One report file: `reports/2026-11-08-issue-123-saturation-testing-analysis.md`.
- No code, no tests, no workflow, no spec.
