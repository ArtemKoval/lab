# 0009 - The crm core is a generic operations automation engine

- Status: proposed
- Date: 2026-10-30

## Context

The crm core still carries insurance-shaped types: `Award`, `Benefit`,
`Plan`, the `approve|decline|refer` decision kinds, and the money
sign-off. The helpdesk pack already fakes a trip cost to satisfy them,
which shows entity shapes are as domain-shaped as the award. The user's
direction: a user acts, the backoffice pipeline is generic, and the actions
and side effects are declared by the domain during setup.

## Decision

The core speaks a generic vocabulary. A `Resolution` is one of the decision
kinds the pack declares. An `Outcome` is an opaque payload the pack's
protocol computes, with a pack-supplied metric for scoring. An `Effect` is a
side effect the pack declares — pay, credit, grant, notify — behind a `Gate`
the pack defines. The pack ships `protocol.py` with four verbs: `resolve`,
`gate`, `execute`, `summarize`. The manifest declares the resolutions, the
outcomes, the effects, and the config keys. The core owns the queue, the
decision record, one stored outcome per case and effect, the gate hold, the
runs, and the versions. It never parses an outcome payload. Awards become
the insurance pack's declared outcome. Rejected options:

- Keep money in the core and rename it. A rename moves the vocabulary but
  keeps the meaning. The helpdesk pack would still fake a trip cost.
- Interpret actions from the manifest alone (declarations without a
  protocol). Declarative for tools, but the award arithmetic would still
  live in the core behind a fixed request shape.
- Store typed outcome columns. Every new domain would need a migration.

## Consequences

Both existing packs and every future pack move onto the protocol. The
dashboard and the agent render from the declarations. A staged migration
keeps the app green: types move, then the execute seam, then the payload,
then the declarations, then the removal of the old shapes. Scoring reads
the pack metric, so the judge and the scoreboard keep their numbers.
