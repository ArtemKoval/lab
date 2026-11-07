# Council Notes: proposal.md

## Author Summary

The author revision settled the status table (halt, auth, list,
blocked, lock rows in a fixed order), the local `gh auth token` probe,
the level-keyed recipe actions, the cron registration in the harness
with the UTC fallback, and the status module split with a pure decide
table.

## Reviewer Challenges

- BLOCKER: the exit-2 action contradicted the settled decisions, the
  recipe omitted the status step, and the unqualified gate stop
  contradicted the propose-then-apply requirement.
- SHOULD-FIX: the auth command mismatch, the unreadable-record
  ambiguity, the blocked detection versus the label precedence, the
  halt two-location rule, the exit-2 widening wording, the JSON field
  rules, the cron timezone fallback, and two STE trips.

## Resolutions

- Accepted: every blocker and fix, with the recipe keyed on the level
  and the code and the pipeline stop rules named in the proposal.
- Accepted: the null rules for the unreached components and the UTC
  fallback.
- Rejected: a peak-window component in status, because the gate
  command owns the window math and the recipe runs it.
- Rejected: status-side writes. Status stays a read-only diagnostic.

## Remaining Risks

- Cron liveness is unmonitored. Accepted in the failure modes.
- The 200-issue bound applies to the blocked row. Same bound as the
  scan.
