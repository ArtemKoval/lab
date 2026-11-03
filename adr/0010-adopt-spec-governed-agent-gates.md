# 0010 - Adopt the spec-governed agent gates

- Status: accepted
- Date: 2026-11-03

## Context

OpenSpec holds intent as scenarios, but nothing proved that code matches those
scenarios. The guide at issue 77 gives the machinery: a bridge that compiles
scenarios into eval artifacts, six gates along the lifecycle, a harness with
four assertion tiers, and a nightly learning loop behind safety rails. The
alternatives: keep manual verification (drift between spec and code stays
invisible), or adopt only phase 0 (governance starts, but behavior iterations
stay unproven and the guide's leverage arrives late).

## Decision

Adopt the full machinery, phases 0 through 4, as `tools/dspy_gate/` plus
hooks, CI, and pipeline steps. The root suite stays hermetic. Live paths sit
behind `ZAI_API_KEY` and `DSPY_GATE_E2E=1`. The nightly run ships default-off.
Rejected: the guide's repo-root layout (this repo nests per-project trees
under `tools/`), and an always-on nightly cron (spend needs a switch).

## Consequences

Every behavior change now carries compiled eval cases and conformance
results. The coverage floor covers the new tool from the first pull request.
Model or judge upgrades route through Gate 5 re-certification. The nightly
loop can spend on GLM only after the operator flips the repository variable.
