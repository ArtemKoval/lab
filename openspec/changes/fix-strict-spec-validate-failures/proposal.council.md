# Council Notes: proposal.md and the delta specs

## Author Summary

The author drafted a requirement-split shape: three MODIFIED
requirements plus seven new requirements and one REMOVED entry.

## Reviewer Challenges

- The strict validator rejects the split shape: a MODIFIED block
  replaces the whole requirement, so moved scenarios would drop
  from the original at archive.
- The four effort scenarios the author listed as new already exist
  in the mainline spec.
- The refusal scenario already pins the no-gh-call behavior under a
  separate requirement, so a copy would duplicate it.
- The bare REMOVED form lacks the Reason and Migration lines the
  schema mandates.
- The lock-order scenario carries no test yet.

## Resolutions

- Accepted: the final shape keeps every requirement name and moves
  the examples into scenarios inside the same requirement.
- Accepted: the deltas slice all 26 existing scenarios verbatim
  from the mainline, once each, with no ADDED or REMOVED sections.
- Accepted: the no-gh-call copy dropped. One new lock-order
  scenario joins, and the apply phase adds its test.
- Accepted: the reviewer verified the four new row scenarios against
  the parameterized statusline table test.
- Rejected: none. All findings landed.

## Remaining Risks

- The body trims rely on scenario pins. The verbatim comparison and
  the validator arbitrate the result.
