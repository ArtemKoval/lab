# Design: extend-saturation-measurement

## Plan review

The change records delivered work, so the design holds one decision:
what the baseline section of the report carries. It carries the
per-tool table from the store, the eight weakest modules with scores
and site counts, the ratchet implication (the store is the floor and
the weekly pass refuses a drop), the fde carve-out open question, and
the coverage-export quirk the run hit. The follow-ups land in the
handover issue, because the report records facts and the issue owns
actions.

## ASIT pass

- Unification: the numbers come from the committed store, so the
  report cites one source of truth instead of restating scores.
- No new component. One section in one existing file.

## Bounds

Docs-only change, no governed capability, no gate thresholds.
