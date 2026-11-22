# Rubric: A held lesson gains an attempt

## Source

The scenario "A held lesson gains an attempt" in
`specs/harness-improvement-memory/spec.md` of this change.

## Question for the judge

Does the cited lesson's ledger carry the new attempt with every ledger
field after the run confirmed the rule?

## Pass criteria

- The ledger carries one new attempt dated in this session.
- The attempt records the trigger, the prediction, the observation, the
  setting, and the verdict holds.

## Fail criteria

- The ledger carries no new attempt.
- The attempt misses one of the seven fields.

## Scoring

Score 1.0 when every pass criterion holds. Score 0.5 when the attempt
carries all fields but the setting names no host or model. Score 0.0 when
any fail criterion holds. The ensemble of 3 votes at temperature 0, and the mean passes the
tier_b_min threshold of this change.
