# ADR Review Manifest

- Status: completed
- Review date: 2026-11-08

## Review Summary

ADR review completed for this change. The change writes an analysis report
and introduces no architectural commitment, so it creates no new
repository-level ADR. The review confirmed that ADR 0005 stays in force and
untouched: its rejection of whole-tree mutation governs pull requests, and
this research runs two bounded passes once and proposes no gate.

## In-Force ADRs Reviewed

- ADR 0001 - add the intent-driven harness. It owns the change flow this
  change follows.
- ADR 0002 - Claude Code as the single harness. Background for the harness
  surface the report measures.
- ADR 0003 - adopt the superpowers execution mechanics. Background for the
  pipeline steps.
- ADR 0004 - enforce STE in specs. The change artifacts sit in the gate
  scope, so every sentence follows the mechanical rule set.
- ADR 0005 - adopt the ub-mode discipline and quality tools. It owns the
  vendored tools, the no-survivors limit, and the rejected whole-tree CI
  option that bounds this measurement plan.
- ADR 0006 - adopt handover telemetry. It owns the telemetry block that the
  handover issue of this change carries.
- ADR 0010 - adopt the spec-governed agent gates. No governed capability
  changes, so no `gates.yaml` applies.
- ADR 0011 - pin glm-5.3-flash on every role. No text role runs in this
  change.
- ADR 0013 - grant the loop the automation authority with a run lock. The
  change touches no loop write.

ADR 0012 is superseded by 0013, so it is historical context. ADR 0007, 0008,
and 0009 carry the status proposed, so they constrain nothing yet.

## New Durable ADRs Created

None. No major durable architectural decision sits in this change. A future
adoption change owns any ADR for a saturation ratchet or a scheduled pass.
