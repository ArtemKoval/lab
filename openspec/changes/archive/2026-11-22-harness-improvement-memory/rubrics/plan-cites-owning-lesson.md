# Rubric: A plan cites an owning lesson

## Source

The scenario "A plan cites an owning lesson" in
`specs/harness-improvement-memory/spec.md` of this change.

## Question for the judge

Does the plan cite, by name, every lesson whose problem names a surface the
change touches?

## Pass criteria

- The plan names the touched surfaces.
- The plan carries a citation line for each owning lesson, and the citation
  names the lesson file.

## Fail criteria

- The plan touches a surface that owns a lesson and carries no citation.
- The citation names a lesson whose problem names no touched surface.

## Scoring

Score 1.0 when every pass criterion holds. Score 0.5 when the plan cites a
lesson but the citation misses the lesson file name. Score 0.0 when any
fail criterion holds. The ensemble of 3 votes at temperature 0, and the mean passes the
tier_b_min threshold of this change.
