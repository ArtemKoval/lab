# 0003 - Adopt the superpowers execution mechanics

- Status: accepted
- Date: 2026-10-24

## Context

The harness discipline lived only in skill text a session invokes, so compaction and long sessions lost the contract. Long apply runs kept progress and rulings only in conversation memory. Debugging, completion claims, skill authoring, and review replies followed no written procedure. The obra/superpowers project (MIT, commit 2ce8aa15d05bd57213e6f746f953aafb7ded7a8b) ships small, field-proven mechanics for each gap.

## Decision

Adopt seven mechanics from obra/superpowers as vendored, owned code: a SessionStart charter hook; a stdlib plan-execution CLI (task brief, review package, append-only ledger); the systematic-debugging, verification-before-completion, and writing-skills skills; review-reception and model-selection rules in the delivery pipeline; and the designation of upstream `diagnosing-superpowers` as the reference design for the pipeline's future Analyse sub-step. Do not install the plugin itself: no marketplace machinery, no telemetry, no multi-harness porting layer.

## Consequences

Every session start carries the charter text in context. Long apply runs gain a per-run scratch ledger outside version control; the durable record stays in tasks.md and git. Three more skill directories join the harness surface. A CI job starts running the root suite on pull requests. A later change adopts the transcript-analysis tooling for the Analyse sub-step, using the designated reference design.
