# Proposal: add-crm-ops-abstraction

## Why

The engine still carries insurance-shaped types in its core: `Award`,
`Benefit`, `Plan`, `DecisionKind`, and the money sign-off. The user's
direction: the crm becomes generic operations automation — a user acts, the
backoffice pipeline is generic, and the actions and side effects are declared
by the domain during setup. An award is one such declared effect, not a core
type.

## What Changes

- The core vocabulary becomes generic: a `Resolution` (the pack declares the
  kinds), an `Outcome` (an opaque payload computed by the pack, plus a
  pack-supplied metric), an `Effect` (a side effect the pack declares:
  pay, credit, grant, notify), and a `Gate` (the pack's hold predicate).
- Each pack ships a `protocol.py` with the four verbs the core calls:
  `resolve`, `gate`, `execute`, `summarize`. The manifest declares the
  resolutions, the outcomes, the effects, and the config keys.
- The engine keeps the backoffice pipeline: the queue, the decision record,
  the hold and its answers, one execution per effect, the runs, and the
  versions. Every insurance- and helpdesk-shaped type leaves the core.
- Both packs (insurance, helpdesk) move onto the protocol. A third pack,
  `opsdemo` (escalations, no money), proves the genericity.
- The dashboard and the agent render from the declarations, with per-stage
  aliases so old tool names and routes keep working until the last stage.

## Capabilities

### New Capabilities

- `crm-ops-core`: The generic pipeline — resolutions, outcome storage, the
  gate hold, effect execution, and the pack protocol the core calls.

### Modified Capabilities

- `crm-domain-pack`: The pack contract grows the protocol module and the
  manifest declarations. the rules contract is replaced by the protocol verbs.
- `crm-engine`, `crm-durable-state`, `crm-swarm`, `crm-self-improvement`:
  their award- and decision-shaped requirements are restated over the generic
  vocabulary.

## Impact

- `backend/models.py`, `main.py`, `database.py`, and `agent/tools.py` are
  reshaped. both packs and the new `opsdemo` pack move onto the protocol.
- The dashboard renders outcome summaries and actions from the pack
  declarations.
- Staged delivery: five stages, each leaving the suite green. per-stage
  aliases keep old tool names and routes working until the removal stage.
