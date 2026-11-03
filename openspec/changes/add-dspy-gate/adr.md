# ADR Review Manifest

- Status: completed
- Review date: 2026-11-03

## Review Summary

Two durable decisions. The change adopts the spec-governed gate machinery as the
behavior-governance layer of this repo, and it pins a flash-everywhere model policy that
deviates from the adopted guide. Each decision lands as its own record at archive.

## In-Force ADRs Reviewed

- `adr/0004-enforce-ste-in-specs.md` - accepted, in force. The bridge emits only JSON,
  JSONL, or Python as GENERATED artifacts, so the STE scan never reads generated files.
- `adr/0005-adopt-ub-mode-and-quality-tools.md` - accepted, in force. The new Python
  passes the same three gates, crapper, dryer, and mutator, on changed paths.
- `adr/0001-add-intent-driven-harness.md` - accepted, in force. The change extends the
  schema templates and the pipeline skill instead of adding a second workflow.
- `adr/0009-ops-automation-core.md` - accepted, in force. No overlap: the ops core serves
  the crm engine, and the gate system serves openspec artifacts.

## New Durable ADRs Created

### 0010 - Adopt the spec-governed agent gates

- Status: proposed
- Date: 2026-11-03

#### Context

OpenSpec holds intent as scenarios, but nothing proved that code matches those
scenarios. The guide at issue 77 gives the machinery: a bridge that compiles scenarios
into eval artifacts, six gates along the lifecycle, a harness with four assertion
tiers, and a nightly learning loop behind safety rails. The alternatives: keep manual
verification (drift between spec and code stays invisible), or adopt only phase 0
(governance starts, but behavior iterations stay unproven and the guide's leverage
arrives late).

#### Decision

Adopt the full machinery, phases 0 through 4, as `tools/dspy_gate/` plus hooks, CI, and
pipeline steps. The root suite stays hermetic. Live paths sit behind `ZAI_API_KEY` and
`DSPY_GATE_E2E=1`. The nightly run ships default-off. Rejected: the guide's repo-root
layout (this repo nests per-project trees under `tools/`), and an always-on nightly cron
(spend needs a switch).

#### Consequences

Every behavior change now carries compiled eval cases and conformance results. The
coverage floor covers the new tool from the first pull request. Model or judge upgrades
route through Gate 5 re-certification. The nightly loop can spend on GLM only after the
operator flips the repository variable.

### 0011 - Pin glm-5.3-flash on every text role

- Status: proposed
- Date: 2026-11-03

#### Context

The guide's role policy pins glm-5.3 for hard signatures, reflection, and judges, and
glm-5.3-flash for the cheap runtime role. The user directed glm-5.3-flash everywhere
instead of the bigger model. The guide warns that thinking plus low temperature loops,
and that flash runs with thinking disabled.

#### Decision

Pin glm-5.3-flash on the runtime, hard runtime, reflection, and judge roles with
thinking disabled. Keep glm-4.5v on the vision judge. Record the deviation in
`gates.yaml` comments. Any pin change routes through Gate 5 re-certification.

#### Consequences

Cost per run drops, and one model profile serves every text role. Hard reasoning tasks
lose the bigger model's reasoning budget. The held-out certification and the Tier-B
ensembles carry the residual risk. A future upgrade is a `gates.yaml` edit plus a
Gate 5 run, never a code change.
