# ADR Review Manifest

- Status: completed
- Review date: 2026-11-08

## Review Summary

ADR review completed for this change. The review walked the
supersession graph of `adr/` (0001 through 0014, no supersessions)
and re-read design.md. The change tightens the CI gate contract. The
durable placement boundary already lives in ADR 0005 and ADR 0014, so
no new architecture decision arises.

## In-Force ADRs Reviewed

- ADR 0005 (adopt the ub-mode discipline and quality tools): the
  diff-scoped gate with an explicit worker cap and timeout stays. This
  change only removes the score resolution from that gate.
- ADR 0014 (schedule the saturation pass outside pull requests): the
  diff-scoped per-pull-request gate and the scheduled whole-tool pass
  keep their separate scopes. This change raises the bar of the
  former and leaves the latter alone.

## New Durable ADRs Created

- None - no major durable architectural decisions were introduced.
  The saturation bar lands as a `quality-gates` requirement, which is
  the behavior source of truth.
