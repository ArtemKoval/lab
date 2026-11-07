# Council Notes: design.md

## Author Summary

The author revision settled the status table, the auth probe, the
output shape, the recipe action table, the cron registration, and the
module split. The reviewer folded three blockers and six fixes: the
recipe keys on the level and the code, the recipe order runs status
first, the pipeline stop rules govern the issue work, the proposal
names `gh auth token` with the empty-token rule, the unreadable-lock
row is exit 2 while a corrupt record stays stale, the blocked
detection reuses the scan classifier, the halt rows cover both
locations, and the cron carries a UTC fallback.

## Reviewer Challenges

- BLOCKER: the exit-2 action contradicted the settled decision, the
  recipe omitted the status step it gates on, and the unqualified
  gate stop contradicted the propose-then-apply requirement.
- SHOULD-FIX: the auth command mismatch, the unreadable-record
  ambiguity, the blocked detection versus the label precedence, the
  halt two-location rule, the exit-2 widening wording, the JSON field
  rules, the cron timezone fallback, and two STE trips.

## Resolutions

- Accepted: every blocker and fix, with the recipe keyed on the level
  and the code and the pipeline stop rules named in the delta.
- Accepted: the null rules for the unreached components, and the UTC
  fallback for the cron.
- Rejected: a peak-window component in status, because the window is
  a clock condition and the gate command already owns the math.
- Rejected: halt logic in the CLI beyond the status read. The recipe
  and the hook keep their roles, and status only reports.

## Remaining Risks

- Cron liveness is unmonitored, and a dead cron looks like a quiet
  healthy loop. Accepted in writing in the failure modes.
- A blocked issue past the 200-issue bound stays unreported. Same
  bound as the scan.
