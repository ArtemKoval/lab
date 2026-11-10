# ADR Review Manifest

- Status: completed
- Review date: 2026-11-10

## Review Summary

The review walked the supersession graph of `adr/` (0001 through 0016,
and 0013 supersedes 0012). No new ADR follows. The status line is a
tool-level capability, and its trade-offs live in design.md.

## In-Force ADRs Reviewed

- `adr/0002-claude-code-single-harness.md` - accepted, in force. The
  line renders inside Claude Code sessions, and no second harness
  enters.
- `adr/0006-adopt-handover-telemetry.md` - accepted, in force. The
  token totals reuse the transcript-sum pattern and the definitions
  the telemetry tool established.
- `adr/0016-fast-mode-delivery-contract.md` - accepted, in force.
  This delivery runs the normal flow, and no fast run reads it.

## New Durable ADRs Created

None.
