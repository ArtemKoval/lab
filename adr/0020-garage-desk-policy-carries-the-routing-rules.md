# 0020 - Garage desk policy carries the routing rules

- Status: accepted
- Date: 2026-11-19

## Context

The garage pack (the port of the `operator-copilot` prototype) routes each
repair job to a garage by brand first, then specialisms, then location,
then queue capacity, with a certified EV gate. Two homes exist for those
rules. The rules module computes the authorization from contract, plans,
request, and approval limit only — the engine contract carries no garage
parameter — so code there cannot see the fleet. The pack policy documents
can. The source prototype computed the triage score in code
(`backend/ai/retrieval.py` of the source). ADR 0007 fixes the pack seam,
and the pack skill bans engine edits. The source also ran a capacity
planner that raised awareness flags (specialism shortage, EV gap) before
the queue overflows. The pack contract carries no flag surface.

## Decision

The garage pack carries the routing rules in its policy documents, and the
garage fleet as searchable facts in its reference data. The desk agent
names the chosen garage in the decision reason. The rules module computes
the authorization arithmetic only. The capacity planner stays outside the
pack contract. A flag surface is new engine vocabulary under ADR 0007's
clause, so it needs a superseding record and an engine-side proposal of its
own.

## Consequences

- The routing order evolves as a policy edit, with no engine release.
- The pack's evals pin the routing outcomes as decisions, and accuracy
  claims on those evals need human review before anyone trusts them.
- The free-slot facts of the reference data stay static numbers, with no
  live engine count behind them. The flags of the source stay a follow-up
  with its own proposal.
