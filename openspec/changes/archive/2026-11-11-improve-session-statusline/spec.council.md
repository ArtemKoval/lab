# Council Notes: specs/session-statusline/spec.md

## Author Summary

The delta restates the render requirement with the separator and the
coding plan mapping, carries its three live scenarios plus seven new
ones, and restates the fails-open requirement with one new degraded
separator scenario.

## Reviewer Challenges

- Blocker: the degraded line change had no delta coverage, because a
  MODIFIED requirement replaces the whole block at archive.
- Should-fix: the proposal promised scenarios that the delta did not
  carry, among them four table rows and a separator scenario.
- Taste: the case folding in the design had no spec basis.

## Resolutions

- Accepted: the delta now carries a MODIFIED restatement of
  `The tool fails open` with a degraded separator scenario.
- Accepted: the delta gained the separator scenario and the
  mixed-case scenario. The proposal wording now names the actual
  scenario set, and the unit tests cover all seven rows.
- Accepted: the mixed-case scenario pins the case folding that the
  design specifies.

## Remaining Risks

- The requirement text pins the full table. Three row scenarios and
  the tests cover it, and the table text is the authority for the
  other rows.
