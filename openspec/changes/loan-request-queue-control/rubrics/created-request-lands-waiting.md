# Rubric: A created request lands in the queue as waiting

## Source

The scenario "A created request lands in the queue as waiting" in
`specs/crm-engine/spec.md` of this change.

## Question for the judge

Does the created request carry the generated pack-prefix id, the waiting
status, and a visible place in the queue, from the API evidence alone?

## Pass criteria

- The POST reply carries a case id with the pack prefix and status
  `waiting`.
- A following `GET /api/cases` lists the new case.

## Fail criteria

- The reply carries no pack-prefix id or a non-waiting status.
- The queue read misses the new case.

## Scoring

Score 1.0 when every pass criterion holds. Score 0.5 when the id carries
the prefix but the status is wrong. Score 0.0 when any fail criterion
holds. The ensemble of 3 votes at temperature 0, and the mean passes the
tier_b_min threshold of this change.
