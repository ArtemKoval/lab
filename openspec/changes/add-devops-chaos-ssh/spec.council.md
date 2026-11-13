# Council Notes: spec.md

## Author Summary

The author drafted six requirements with 16 scenarios over the
host-driven tutor: the list, the arm flow, the hint order, the
reveal, the stop flow, and the safety rule with five scratch
bindings. The safety requirement carried the leak reasons in the
requirement prose.

## Reviewer Challenges

- The scenario prose used inline prose lines instead of the house
  scenario blocks, and the delta missed the Purpose section.
- The safety requirement prose ran over the 500 character lint bound,
  and a scenario heading appeared twice with the same slug.
- The stop requirement carried per-id stack language that contradicts
  the one-container model.
- The start requirement was false for the scenario without an
  injection script.

## Resolutions

- Accepted: the spec now carries the Purpose section and the scenario
  blocks of the house format.
- Accepted: the safety requirement lost the leak-reason prose to
  design.md, and the duplicate heading became the hint-specific
  heading.
- Accepted: the stop requirement states the global container teardown
  with the id argument naming the scratch set.
- Accepted: the start requirement runs the injection when the
  scenario defines one, and a scenario covers the no-injection case.

## Remaining Risks

- The spec pins no scenario count and no KEX mechanism, so the
  apply-time catalog drift stays outside the spec.
- The safety requirement asserts the printed-command bindings. The
  real-file digest assertions live in the e2e lane, not in the
  hermetic spec tests.
