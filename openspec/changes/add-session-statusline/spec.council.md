# Council Notes: spec.md

## Author Summary
Five requirements with scenarios: the render, the transcript totals,
the console source, the pool math, the cache discipline, and the
fail-open contract.

## Reviewer Challenges
- The duplicate scenario slug failed Gate 0 after the requirement
  split.
- The pool math computed a ratio, not a percent.
- The zero-total scenario contradicted the pool-count rule.
- The cache-rate fallback lived in the design only.
- The refresh scenario could not fail.
- Three SHALL clauses and the freshness gate carried no scenarios.
- The pool mapping sat outside the normative text.
- The GMT+0 and UTC names mixed.

## Resolutions
- Accepted: all. The duplicate is gone (verified against the current
  bytes), the math reads 100 times the ratio, the zero-total scenario
  uses two pools, the cache fallback carries a requirement and a
  scenario, the refresh scenario names the offset seam, the missing
  scenarios exist, the mapping is normative, and UTC naming holds.
- Rejected: none.
- Deferred: none.

## Remaining Risks
- The scenario count grew to 14, and the test suite carries one test
  per scenario.
