# ADR Review Manifest

- Status: completed
- Review date: 2026-10-29

## Review Summary

ADR review completed for this change. The change carries one durable decision: the telemetry mandate for handover issues with the redaction contract. It landed as a new repository-level record. The implementation choices stay in design.md as change-local decisions.

## In-Force ADRs Reviewed

- `adr/0001-add-intent-driven-harness.md` - accepted, in force. The change adds a capability through the schema flow.
- `adr/0002-claude-code-single-harness.md` - accepted, in force. The telemetry targets Claude Code only.
- `adr/0003-adopt-superpowers-execution-mechanics.md` - accepted, in force. The pipeline edits keep the mechanics intact.
- `adr/0004-enforce-ste-in-specs.md` - accepted, in force. All change text passed the mechanical gate in this change.
- `adr/0005-adopt-ub-mode-and-quality-tools.md` - accepted, in force. The new package runs under the crapper, dryer, and mutator gates.

## New Durable ADRs Created

- `adr/0006-adopt-handover-telemetry.md` - accepted. Records the mandate, the two data sources, the redaction contract, and the honest-gap rule for estimates.
