# 0011 - Pin glm-5.3-flash on every role

- Status: accepted
- Date: 2026-11-03

## Context

The guide's role policy pins glm-5.3 for hard signatures, reflection, and
judges, glm-5.3-flash for the cheap runtime role, and glm-4.5v for vision.
The user directed glm-5.3-flash everywhere instead of the bigger models, in
two directives dated 2026-11-02 and 2026-11-03. The guide warns that thinking
plus low temperature loops, and that flash runs with thinking disabled.

## Decision

Pin glm-5.3-flash on every role in `tools/dspy_gate/gates.yaml` — runtime,
hard runtime, reflection, judge, and vision judge — with thinking disabled.
Record the deviation in the `gates.yaml` comments. Any pin change routes
through Gate 5 re-certification against the frozen suites.

## Consequences

Cost per run drops, and one model profile serves every role. Hard reasoning
tasks lose the bigger models' reasoning budget; the held-out certification
and the Tier-B ensembles carry the residual risk. A future upgrade is a
`gates.yaml` edit plus a Gate 5 run, never a code change.
