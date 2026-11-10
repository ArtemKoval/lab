# Council Notes: proposal.md

## Author Summary
The proposal states the why, the payload-first tool, the console
fallback, the protected settings wiring, and the impact set. The
author and reviewer rounds tightened every claim.

## Reviewer Challenges
- The Why sentence ran two topics over the limit.
- The out-of-scope line was passive voice.
- The impact list missed the doctor, the README, and the CI workflow
  edit.
- "It calls no other program outside its own directory" contradicted
  the console call.
- "Session cache hit rate" stacked four nouns.
- The time naming mixed GMT+0 and UTC.

## Resolutions
- Accepted: all six. The Why split, the active voice, the three
  impact lines, "no program other than that one", "session cache
  rate", and UTC naming everywhere.
- Rejected: none.
- Deferred: none.

## Remaining Risks
- The pool-to-window mapping follows console display order, an
  undocumented endpoint behavior. The design records the assumption.
