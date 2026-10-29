# ADR Review Manifest

- Status: completed
- Review date: 2026-10-29

## Review Summary

The change introduces no new durable decision beyond ADR 0007, which already owns the seam. The auth replacement, the saver factory, and the rules contract are change-local decisions recorded in design.md, and a later change that ports the AWS rollout may promote the auth contract to a durable record when Cognito lands.

## In-Force ADRs Reviewed

- `adr/0001-add-intent-driven-harness.md` - accepted, in force. The change follows the schema flow with all artifacts.
- `adr/0002-claude-code-single-harness.md` - accepted, in force. The `crm-app` skill gains the new commands.
- `adr/0003-adopt-superpowers-execution-mechanics.md` - accepted, in force. The change runs the pipeline machinery: review rounds, gates, three milestone commits.
- `adr/0004-enforce-ste-in-specs.md` - accepted, in force. All change text passes the mechanical gate. The pack content stays vendored.
- `adr/0005-adopt-ub-mode-and-quality-tools.md` - accepted, in force. The new Python runs under the three gates on changed paths.
- `adr/0006-adopt-handover-telemetry.md` - accepted, in force. The handover issue after the merge carries the telemetry block.
- `adr/0007-crm-engine-with-domain-packs.md` - accepted, in force. The rules module and the pack data extensions follow the seam it owns.

## New Durable ADRs Created
