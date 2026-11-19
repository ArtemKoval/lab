# ADR Review Manifest

- Status: completed
- Review date: 2026-11-12

## Review Summary

ADR review completed for this change. The pack contract of ADR 0007 grows
an optional vocabulary section, and the engine gains two unit words,
`money` and `days`. ADR 0007 says new engine vocabulary beyond its nouns
needs a superseding record, so the change creates ADR 0011 to carry that
decision. ADR 0009 owns the render-from-declarations seam, and this change
extends that seam with the vocabulary. ADR 0010 is in force and names no
constraint this change touches.

## In-Force ADRs Reviewed

- ADR 0004: enforce STE in specs. The delta specs follow the mechanical
  rule set, and the SPEC-STE gate passed on every write.
- ADR 0007: crm engine with domain packs. The vocabulary section extends
  the pack contract, and ADR 0011 carries the new unit words under 0007's
  superseding-record clause.
- ADR 0008: local emulator first AWS targets. Unaffected. The demo stack's
  live-route work rides the same targets.
- ADR 0009: ops automation core. Its render-from-declarations seam is the
  seam this change extends.
- ADR 0010: library assignment history discipline. In force. The change
  touches nothing it owns.

## New Durable ADRs Created

- ADR 0011: pack vocabulary and award units. The manifest's vocabulary
  section, the pack's award unit, and the refusal family's words.
