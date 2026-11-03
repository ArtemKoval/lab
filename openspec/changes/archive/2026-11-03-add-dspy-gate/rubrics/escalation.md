# Rubric: escalation before reply

## Source

The scenario "Escalation happens before reply" in `specs/ticket-triage/spec.md` of this change.

## Question for the judge

Did the triage flow escalate the P0 ticket before any customer-facing reply text was produced?

## Pass criteria

- The trace shows the escalate tool call before the reply step.
- The escalation record names the ticket and the P0 severity.
- No reply text appears in the trace before the escalation record.

## Fail criteria

- The reply step ran first, or the trace holds no escalation call.
- The escalation record lacks the severity.

## Scoring

Score 1.0 when every pass criterion holds. Score 0.5 when the escalation ran first but its record misses the ticket or the severity. Score 0.0 when any fail criterion holds. The ensemble of 3 votes at temperature 0, and the mean passes the tier_b_min threshold of this change.
