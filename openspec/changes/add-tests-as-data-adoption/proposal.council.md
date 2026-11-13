# Council Notes: proposal.md

## Author Summary

The author drafted the proposal in the bench-adoption-plan shape: the
issue request in Why, the analysis pointer, three adoption candidates
with future change ids, the rejections, no capabilities, and an
artifacts-only impact. The author flagged five concerns for the
reviewer: the YAML dependency home, the thin customer seat, the guard
order, the port oracle noise, and the property-based testing reason.

## Reviewer Challenges

- The intent-driven schema lists adr.md and tasks.md in the artifact
  set. The draft covered only proposal.md and design.md.
- The repo-wide parametrize claim failed a recount: the root tests
  tree holds 8 files under the strict pattern, and crm holds 36 more.
- The draft held three incompatible YAML positions at once.
- Two sentences exceeded the 25 word STE limit, and one rejection
  carried a four-word noun cluster.
- The article date needed a source, because the bench precedent names
  no date.

## Resolutions

- Accepted: the primary agent wrote adr.md and tasks.md as the
  mechanical artifacts outside the author round.
- Accepted: the analysis pointer now names no count at repo scope, and
  the design table scopes the counts to each tree after a recount.
- Accepted: one position survives. CSV only for the first delivery,
  with structured YAML behind the test dependency policy.
- Accepted: the primary agent split the long sentences, and the noun
  cluster became "customer tests for a browser UI".
- Rejected as a change: the date stays. The primary agent verified it
  against the article metadata field og:article:modified_time at
  fetch time.

## Remaining Risks

- The proposal carries the plan only. The substance and its risks sit
  in design.md and its council notes.
