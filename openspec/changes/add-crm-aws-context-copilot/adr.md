# ADR Review Manifest

- Status: completed
- Review date: 2026-10-30

## Review Summary

The change introduces one durable decision: the local emulator stands in for the AWS deployment targets, and real AWS joins later through the same environment variables. It lands as `adr/0008-local-emulator-first-aws-targets.md`. The key gate, the memory factory, and the runtime entry points stay change-local in design.md.

## In-Force ADRs Reviewed

- `adr/0001-add-intent-driven-harness.md` - accepted, in force. The change follows the schema flow.
- `adr/0002-claude-code-single-harness.md` - accepted, in force. The skills stay Claude Code.
- `adr/0003-adopt-superpowers-execution-mechanics.md` - accepted, in force. The pipeline machinery runs.
- `adr/0004-enforce-ste-in-specs.md` - accepted, in force. All change text passes the gate; pack content stays vendored.
- `adr/0005-adopt-ub-mode-and-quality-tools.md` - accepted, in force. The new Python runs under the three gates.
- `adr/0006-adopt-handover-telemetry.md` - accepted, in force. The handover issue carries the telemetry block.
- `adr/0007-crm-engine-with-domain-packs.md` - accepted, in force. The context server reads the pack through the loader.

## New Durable ADRs Created

- `adr/0008-local-emulator-first-aws-targets.md` - proposed. Records the emulator-first rule for the crm AWS targets and the same-variables rollout.
