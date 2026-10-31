# ADR Review Manifest

- Status: completed
- Review date: 2026-10-30

## Review Summary

One durable decision lands: the crm core becomes a generic operations
automation engine — resolutions, outcomes, effects, and gates are pack
declarations, and the pack ships a four-verb protocol the core calls. It
supersedes the insurance-shaped types that ADR 0007 left in the core, and it
lands as `adr/0009-ops-automation-core.md`.

## In-Force ADRs Reviewed

- `adr/0007-crm-engine-with-domain-packs.md` - accepted, in force. The pack
  seam stays. this change deepens it: the outcome and its meaning move fully
  into the pack.
- `adr/0008-local-emulator-first-aws-targets.md` - accepted, in force. The
  refactor changes no deployment target.

## New Durable ADRs Created

- `adr/0009-ops-automation-core.md` - proposed. Records the generic core
  vocabulary, the pack protocol verbs, and the declarations the manifest
  owns.
