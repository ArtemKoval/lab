# Design: add-crm-ops-abstraction

## Source

The user's direction: abstract crm into generic operations automation. A user
acts. the backoffice pipeline is generic. actions and side effects are
declared by the domain during setup. an award is a configurable piece of a
domain, not a core type.

## Plan review

A decision tournament ran: three independent designs (opaque outcome,
action registry, capability protocol), adversarially judged on genericity,
migration safety, and pack-authoring ease. Winner: capability protocol
(genericity 8, migration 7, ease 7). Grafts: the outcome payload stays opaque
at the seam with a pack-supplied metric (from opaque-outcome), and per-stage
aliases keep old names working (from the tournament's shared lesson).

## Key decisions

- The pack ships `protocol.py` with four verbs the core calls:
  `resolve(case, config, request) -> Outcome`, `gate(outcome, config) -> bool`,
  `execute(case, outcome) -> Result`, `summarize(outcome) -> str`.
- The manifest declares: `resolutions` (the decision kinds), `outcomes` (the
  declared outcome kinds and their protocol bindings), `config` (the settings
  keys), and `effects` (the side effects and their gates).
- The core owns: the queue, the decision record, one stored outcome per case
  and effect (unique), the gate hold and its answers, the runs, the versions,
  and the pack protocol loader.
- The pack owns: the outcome meaning and payload shape, the gate predicate,
  the effect handlers, the request schemas, the metric for scoring, and the
  config.
- `opsdemo`, a third pack with no money (escalations), proves a new domain
  needs no core edit.
- Stage aliases: old tool names and routes keep working until the removal
  stage, then go.

## Failure modes

- The core reading the payload: forbidden. scoring reads the pack metric.
- A pack bypassing one-execution-per-effect: the core owns the unique index.
- A protocol contract break: the loader validates the verbs at startup.
