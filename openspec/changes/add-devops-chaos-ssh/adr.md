# ADR Review Manifest

- Status: completed
- Review date: 2026-11-13

## Review Summary

The review walked the supersession graph of `adr/` (0001 through
0016, and 0013 supersedes 0012). No new ADR follows. The tutor, its
environments, and the safety rule are change-scoped design that lives
in design.md. No durable, cross-cutting architecture decision enters
this change.

## In-Force ADRs Reviewed

- `adr/0002-claude-code-single-harness.md` - accepted, in force. The
  tutor is a standalone CLI and docker stack, and no second agent
  runtime enters.
- `adr/0005-adopt-ub-mode-and-quality-tools.md` - accepted, in force.
  The apply phase holds the default quality bar over the new Python
  package: CRAP at 10 or less, duplication below 0.8, and mutation
  with no survivors.
- `adr/0013-grant-the-loop-the-automation-authority-with-a-run-lock.md`
  - accepted, in force. The loop processed this issue under the run
  lock, and the operator holds the spec gate.
- `adr/0014-scheduled-saturation-pass.md` - accepted, in force. The
  saturation ratchet covers the new package at apply time.

ADR 0008 carries the proposed status, so the design cites the docker
daemon on this host as observed evidence and names no accepted
record for it.

## New Durable ADRs Created

None.
