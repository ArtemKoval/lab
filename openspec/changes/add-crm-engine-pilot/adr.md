# ADR Review Manifest

- Status: completed
- Review date: 2026-10-29

## Review Summary

The change carries one durable decision: the CRM engine with domain packs, with the seam contract and the vocabulary rule. It lands as `adr/0007-crm-engine-with-domain-packs.md` in this change. The port plan, the rename map, and the auth and checkpoint choices stay in design.md as change-local decisions for later changes to revise.

## In-Force ADRs Reviewed

- `adr/0001-add-intent-driven-harness.md` - accepted, in force. The change follows the intent-driven schema flow with all artifacts.
- `adr/0002-claude-code-single-harness.md` - accepted, in force. The `crm-app` skill targets Claude Code.
- `adr/0003-adopt-superpowers-execution-mechanics.md` - accepted, in force. The change goes through the pipeline machinery: tournament, builder check, adversarial round, gates.
- `adr/0004-enforce-ste-in-specs.md` - accepted, in force. All change text passes the mechanical gate. The config exemption for vendored upstream files applies to the pack content ported under `crm/domains/insurance/`.
- `adr/0005-adopt-ub-mode-and-quality-tools.md` - accepted, in force. The new Python in `crm/` runs under the crapper, dryer, and mutator gates on changed paths.
- `adr/0006-adopt-handover-telemetry.md` - accepted, in force. The handover issue after the merge carries the telemetry block.

## New Durable ADRs Created

- `adr/0007-crm-engine-with-domain-packs.md` - proposed. Records the engine and domain seam, the pack contract, the vocabulary rule and its guard, and the port series over the upstream milestones.
