# Rubric: The nudge reaches the session after a merge

## Source

The scenario "The nudge reaches the session after a merge" in
`specs/harness-improvement-memory/spec.md` of this change.

## Question for the judge

Does the hook's injected nudge name both the write-back of cited-lesson
outcomes and the session close?

## Pass criteria

- The nudge text names the write-back of cited-lesson outcomes.
- The nudge text names the session close of the bound thread.

## Fail criteria

- The nudge names neither the write-back nor the session close.
- The nudge changes the fixed-string security shape: it names or echoes the
  command line.

## Scoring

Score 1.0 when every pass criterion holds. Score 0.5 when the nudge names
the session close but misses the write-back. Score 0.0 when any fail
criterion holds. The ensemble of 3 votes at temperature 0, and the mean
passes the tier_b_min threshold of this change.
