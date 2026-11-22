# 0021 - Harness lessons carry attempt ledgers

- Status: accepted
- Date: 2026-11-22

## Context

The harness lessons carried a rule and one anecdote, with no record of the
attempts that followed. A rule that failed in one setting kept no trace of
the failure, so the next session re-applied it blind. The pipe lesson of
2026-11-07 re-bit on 2026-11-20 through a background-chain shape that no
ledger forced into the record. The analysis report
`reports/2026-11-20-sim-harness-adoption.md` mapped the finding of arXiv
2611.18856 onto this harness: memory that carries diagnoses without
evidence scores below no memory in one setting, and the full record beats
harness-only continuation in all ten tested transfer settings.

## Decision

A harness lesson names its recurring problem in one line, and carries an
attempt ledger. One attempt lands per exercised recurrence of the rule,
and each attempt records the date, the session, the trigger, the
prediction, the observation, the setting, and a verdict of holds, misled,
or superseded. The ledger appends only. The plan review pulls lessons from
the memory index by problem, the plan cites them, and the review round
raises one finding per plan when a touched surface owns a cited-to-be
lesson that the plan does not cite. The result review and the merge-hook
nudge carry the write-back. The consultation teeth ride the review round.

The rejected options, with their reasons: a repo guard test and a
plan-file convention for mechanical enforcement lost, because plans are
not consistently files here and the convention adds a component for thin
value. Diagnosis-only records, without the outcome ledger, lost, because
the paper showed that shape can score below no memory. A retrieval system
and a nightly learner lost, because the index reads whole in every session
and the nightly loop already covers governed modules.

## Consequences

- Positive: a misleading lesson shows its failed attempts with settings, so
  the next session reads the evidence before it applies the rule. The
  index lines name problems and settings, so the plan review can pull by
  meaning.
- Negative: lesson files grow by one attempt per exercised recurrence, and
  the conversion of the existing lessons costs one apply run.
- Follow-up: the ledger query tool stays deferred until an index line
  first hides a problem a session needed.
