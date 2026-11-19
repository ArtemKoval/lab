# ADR Review Manifest

- Status: completed
- Review date: 2026-11-19

## Review Summary

ADR review completed for this change. The port introduces no new
architectural decision of its own: the child repository made the durable
decisions, and this change ports them as two repository-level records. The
lab's own port choices (merge method, ADR renumbering, the compose override)
are tactical to this change and live in `design.md`.

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

0012 is superseded by 0013 and stays historical. No in-force record
contradicts the port. ADR 0007 fixes the pack seam the library pack joins,
ADR 0017 keeps the Langfuse compose profile this port preserves, and the
child's vocabulary decision names ADR 0007's vocabulary clause, which the
ported numbering keeps valid.

## New Durable ADRs Created

- `adr/0018-library-assignment-history-discipline.md` - ported from the
  child's adr/0010, renumbered, with one ported-from provenance line.
- `adr/0019-pack-vocabulary-and-award-units.md` - ported from the child's
  adr/0011, renumbered, with the status line normalized to the lab house
  syntax and one ported-from provenance line.

No other repository-level ADR was created, and no in-force ADR changed.
