# ADR Review Manifest

- Status: completed
- Review date: 2026-11-23

## Review Summary

ADR review completed for this change. No new durable ADR is needed, and
no in-force ADR conflicts.

## In-Force ADRs Reviewed

- ADR 0007 (the crm engine with domain packs) and ADR 0009 (the ops
  automation core): the route stays inside the engine-generic seam, and
  the words stay in the pack. No conflict.
- ADR 0004 (STE in specs): the delta specs follow it. No conflict.
- ADR 0021 (harness lessons carry attempt ledgers): governs the harness
  lesson records, not the crm engine. No conflict.

## New Durable ADRs Created

- None. The id-series decision and the picker reads are design-level
  choices recorded in design.md D2 and D3. They bind no future
  architecture.
