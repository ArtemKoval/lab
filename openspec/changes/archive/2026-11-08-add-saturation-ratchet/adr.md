# ADR Review Manifest

- Status: completed
- Review date: 2026-11-08

## Review Summary

ADR review completed for this change. The review walked the
supersession graph of `adr/` (0001 through 0013, no supersessions) and
re-read design.md. The change carries one major durable decision: the
scheduled saturation pass outside the pull request path.

## In-Force ADRs Reviewed

- ADR 0005 (adopt the ub-mode discipline and quality tools): rejected
  whole-tree mutation on every pull request because the runtime is
  unbounded. This change places the whole-tool pass on a bounded
  schedule outside pull requests, so it does not collide with the
  rejection. The new ADR records the boundary.
- ADR 0012 and ADR 0013 (grant the loop the automation authority, with
  a run lock): the loop merges its own proposal, implementation, and
  archive pull requests after a green suite. This change relies on
  that authority for its own pull requests.
- ADR 0004 (enforce STE in specs): the delta spec text follows the
  mechanical rule set, and the spec STE gate holds it there.

## New Durable ADRs Created

- `adr/0014-scheduled-saturation-pass.md` - lands with the
  implementation pull request. Status: accepted. The decision: a
  scheduled, timeout-bounded saturation pass runs outside pull
  requests. The per-pull-request gate stays diff-scoped. The store
  moves only through review. The workflow carries an operator-visible
  escape variable. The ADR answers ADR 0005 through the placement
  boundary and does not supersede it.
