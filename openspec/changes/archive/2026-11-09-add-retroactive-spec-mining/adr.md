# ADR Review Manifest

- Status: completed
- Review date: 2026-11-09

## Review Summary

ADR review completed for this change. No major durable architectural
decision was introduced. The seven design decisions are tactical and
tool-local, the house tool template carries the package shape, and the
capability spec carries the behavior. The opt-in rule keeps the
feature-pipeline accretion decision untouched, so no supersession of any
in-force record is in play.

## In-Force ADRs Reviewed

- 0001-add-intent-driven-harness (accepted)
- 0002-claude-code-single-harness (accepted)
- 0003-adopt-superpowers-execution-mechanics (accepted)
- 0004-enforce-ste-in-specs (accepted)
- 0005-adopt-ub-mode-and-quality-tools (accepted)
- 0006-adopt-handover-telemetry (accepted)
- 0010-adopt-spec-governed-agent-gates (accepted)
- 0011-pin-glm-5-3-flash-on-every-role (accepted)
- 0013-grant-the-loop-the-automation-authority-with-a-run-lock (accepted,
  supersedes 0012)
- 0014-scheduled-saturation-pass (accepted)
- 0015-remove-the-fde-mutation-carve-out (accepted)

The proposed records 0007, 0008, and 0009 stay outside the in-force set.

## New Durable ADRs Created

- None - no major durable architectural decisions were introduced. The
  residue-scan change made the same call for the same tool-package shape.
