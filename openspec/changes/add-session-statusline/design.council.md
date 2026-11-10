# Council Notes: design.md

## Author Summary
The design records the two answered forks, the ASIT pass, the render
pipeline, the cache and timeout discipline, the formats, the edge
cases, and the verification plan.

## Reviewer Challenges
- The field list named a field the design does not read, with a stray
  comma.
- The edge case invented a `thinking.enabled` field.
- The pool math, the percentage formula, the cache paths, the session
  key, the cache file names, and the statusLine command template were
  unpinned.
- The console call had no timeout number and no atomic-write rule.
- The transcript fault rule read as a whole-file condition.
- The formats were example-pinned only.
- The doctor path repair per checkout was unstated.

## Resolutions
- Accepted: all, plus the builder reconciliations (the exact console
  command line, the telemetry usage-row rule, the cache file names,
  the sums record shape, the doctor template).
- Rejected: none.
- Deferred: none.

## Remaining Risks
- A console reorder of the pool rows silently swaps the two
  percentages. The per-window payload fallback bounds the damage.
- The line blanks while the shared venv interpreter rebuilds. The
  README names it.
