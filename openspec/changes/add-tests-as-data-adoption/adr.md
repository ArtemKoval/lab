# ADR Review Manifest

- Status: completed
- Review date: 2026-11-13

## Review Summary

The review walked the supersession graph of `adr/` (0001 through
0016, and 0013 supersedes 0012). No new ADR follows. The plan adopts
nothing yet, and each future adoption change carries its own review.

## In-Force ADRs Reviewed

- `adr/0002-claude-code-single-harness.md` - accepted, in force. The
  adoptions land inside the Claude Code harness and the pytest suite,
  and no second test runtime enters.
- `adr/0004-enforce-ste-in-specs.md` - accepted, in force. The spec
  prose stays STE. The scenario tables are data files, so the table
  rows stay outside the STE prose gate.
- `adr/0005-adopt-ub-mode-and-quality-tools.md` - accepted, in force.
  The quality gates stay the default bar. The plan adds no gate change
  and no mutation change.
- `adr/0010-adopt-spec-governed-agent-gates.md` - accepted, in force.
  The dspy-gate scenario rule enforces the Constrained-Tests pattern
  on governed capabilities. The plan extends nothing there.
- `adr/0013-grant-the-loop-the-automation-authority-with-a-run-lock.md`
  - accepted, in force. The loop processed this issue under the run
  lock, and the operator holds the spec gate.
- `adr/0014-scheduled-saturation-pass.md` - accepted, in force. The
  mutation ratchet stays the assertion-strength proof. The plan cites
  it as the reason for the property-based testing deferral.

ADR 0008 carries the proposed status, so the design cites the floci
and apfel setups as observed evidence and names the record with its
status.

## New Durable ADRs Created

None.
