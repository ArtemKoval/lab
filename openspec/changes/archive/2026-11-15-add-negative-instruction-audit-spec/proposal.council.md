# Council Notes: proposal.md

## Author Summary

The author drafted the proposal with the spec-only scope, the
ownership split, and the "tests: no change" impact line. The draft
enumerated seven requirement areas and claimed the existing suite
pins the delta behavior.

## Reviewer Challenges

- Blocker: the enumeration omits the read-only requirement, so the
  requirement count disagrees with the delta.
- Blocker: the "tests: no change" claim is false. 13 scenarios lack
  coverage, and the pipeline rule needs one test per scenario.
- Major: the `--repo-root` flag is absent from the delta plan, though
  the CLI surface and the exit-2 message expose it.
- Major: the five miss-class shapes lack named test evidence.
- Minor: STE risks in the summary prose (the final prose avoided
  them).

## Resolutions

- Accepted: the enumeration now lists all nine requirement areas.
- Accepted: the Impact section declares the gap tests as an
  apply-phase deliverable with the count.
- Accepted: the delta carries the root-selection requirement.
- Accepted: the tasks carry the five miss-class shapes from the
  README.
- Rejected: none. All findings landed.
- Deferred: none.

## Remaining Risks

- The strict validator may force a requirement split at write time.
  The proposal runs validate before the pull request.
- The issue cross-references (issue 201, PR 207, the
  `human-approved` label) were verified by the primary agent with
  `gh` before the write.
