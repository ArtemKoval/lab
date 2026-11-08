# 0014 - Schedule the saturation pass outside pull requests

- Status: accepted
- Date: 2026-11-08

## Context

ADR 0005 vendored the mutator and made it the per-pull-request gate on
changed paths, and it rejected whole-tree mutation on every pull
request because the runtime is unbounded. The saturation measurement
of issue 123 then showed that the diff-scoped gate cannot see the
whole surface: it missed the one survivor the full pass found in
`spec_ste_check`. Proposal 2 of the saturation report asks for a
scheduled saturation pass with a ratchet, and the operator approved
both placements: a stdlib CLI and a scheduled workflow.

## Decision

Run the whole-tool mutation pass on a schedule, outside the pull
request path. The pass lives in `tools/saturation_pass` and reuses the
vendored mutator as its only engine. The workflow
`.github/workflows/saturation.yml` runs weekly on
`37 4 * * 1`, carries a `timeout-minutes: 90` budget and a concurrency
group, and runs unless the repository variable
`SATURATION_PASS_ENABLED` is exactly `false`. The per-pull-request
gate stays diff-scoped with the root suite; the scheduled pass runs
each tool's area suite per mutant, which is the only cost shape the
whole-tree runtime budget can hold. The pass enforces only: it never
writes the committed score store, and no CI step pushes. The store at
`reports/saturation/scores.json` moves only through pull requests,
under the normal review gates. A per-module score drop fails the
scheduled run, and the operator lands the fix or the store update
through review.

## Consequences

CI gains a weekly job whose runtime is bounded by the timeout budget,
so the ADR 0005 rejection of unbounded per-pull-request runtime stays
intact. Ratchet drops surface on the schedule instead of hiding
outside diffs. The ratchet baseline starts from the area-suite
killing power, which is weaker than the per-pull-request root-suite
gate, so the two numbers measure different things on purpose. A fresh
fork runs the pass out of the box, because the variable defaults to
on; the operator sets it to `false` to stop it. The store's history
in git records the saturation of the harness over time.
