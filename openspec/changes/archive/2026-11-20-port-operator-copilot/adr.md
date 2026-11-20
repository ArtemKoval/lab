# ADR Review Manifest

- Status: completed
- Review date: 2026-11-19

## Review Summary

ADR review completed for this change. The port introduces one new
architectural decision of its own: the home of the garage routing rules.
Every other engine surface the pack uses stands as it is, so the in-force
records review clean.

## In-Force ADRs Reviewed

- 0001 - add intent driven harness
- 0002 - claude code single harness
- 0003 - adopt superpowers execution mechanics
- 0004 - enforce STE in specs
- 0005 - adopt ub mode and quality tools
- 0006 - adopt handover telemetry
- 0007 - crm engine with domain packs
- 0008 - local emulator first AWS targets
- 0009 - ops automation core
- 0010 - adopt spec governed agent gates
- 0011 - pin glm 5.3 flash on every role
- 0013 - grant the loop the automation authority with a run lock
  (supersedes 0012)
- 0014 - scheduled saturation pass
- 0015 - remove the fde mutation carve out
- 0016 - fast mode delivery contract
- 0017 - self-hosted Langfuse tracing
- 0018 - library assignment history discipline
- 0019 - pack vocabulary and award units

0012 is superseded by 0013 and stays historical. No in-force record
contradicts the port. ADR 0007 fixes the pack seam the garage pack joins.
ADR 0019 owns the vocabulary feature that carries the pack's desk words.
ADR 0017 keeps the Langfuse compose profile untouched by this port.

## New Durable ADRs Created

- 0020 - garage desk policy carries the routing rules. The routing order
  and the certified EV gate live in the pack policy documents and the
  reference data, never in engine code, because the engine contract passes
  contract, plans, request, and approval limit only. The capacity planner
  of the source stays outside the pack contract, and a flag surface needs
  a superseding record under ADR 0007's vocabulary clause.
