# Council Notes: design.md

## Author Summary
The design records the three answered forks, the ASIT pass, the flow
diagram, the rule texts, the template shape, the classifier rule, the
edge cases, and the verification plan. The author round added the
classifier rule. The reviewer round pinned the rule placement, the
counting rule, and the CI-item logic.

## Reviewer Challenges
- The draft claimed a classifier unknown-state fallback that the code
  does not have. The author verified the fall-through to start at
  core.py line 74, and the primary agent confirmed it.
- The keep-set bullet contradicted the before-the-merge debt issue on
  the reduced Step 13 order.
- The conditional title prefix depended on a label the run cannot
  create on this host.
- Counting non-applying steps as debt contradicted the full-flow rule
  and made the no-skips case unreachable.
- "Below the label table" named three candidate spots, and one of
  them (after the pull-request branches) lets one `Refs #N` line flip
  the debt issue to resume.
- The CI item read as "always present" against two edge cases that
  remove or absorb it.
- No rule forbade a close keyword toward the debt issue in the PR
  body.
- The closure rule named no actor, and the loop can never close a
  permanently prefixed issue.
- The peak-hours claim overreached: the inner loop escalates to agent
  dispatches, and the gate blocks more than agents.
- Fast mode dropped the mainline resync.
- The reduced review left telemetry unstated.
- Governed capabilities had no rule.

## Resolutions
- Accepted: the classifier rule section with the optional `title`
  keyword, the skip-and-none mapping, the prefix-or-label match, and
  the exact placement after the waiting branch and before the
  pull-request branches. The reduced Step 13 order. The unconditional
  `tech-debt:` title prefix. The applies rule in the skip-set bullet.
  The CI item present except when protection waited, with the
  no-skip case writing the CI item alone. The no-close-keyword rule.
  The paying run as the closing actor. The inline review rule and the
  scoped peak-hours claim. The resync in the keep set. A Telemetry
  section in the debt template. The governed-capability rule. The
  observed no-protection fact on the mainline.
- Rejected: none.
- Deferred: the label-or-prefix OR-clause stays in scope as written,
  because it costs one branch now and closes the manual-creation hole.

## Remaining Risks
- The mutation gate on the changed `classify` branch demands a test
  that kills prefix mutants. Task 5.4 owns the unit test.
