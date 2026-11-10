# ADR Review Manifest

- Status: completed
- Review date: 2026-11-10

## Review Summary

The review walked the supersession graph of `adr/` (0001 through
0015, no supersessions). One durable decision follows: the delivery
contract gains a fast mode, and the record lands as `adr/0016` with
the implementation pull request.

## In-Force ADRs Reviewed

- `adr/0003-adopt-superpowers-execution-mechanics.md` - accepted, in
  force. Fast mode is a reduced execution mode inside the same
  delivery flow, and it does not replace the mechanics.
- `adr/0004-enforce-ste-in-specs.md` - accepted, in force. The change
  prose and the template text follow the mechanical rule set.
- `adr/0005-adopt-ub-mode-and-quality-tools.md` - accepted, in force.
  Fast mode skips the three gates on prototype code, and each skip
  becomes a debt item. Normal runs keep the gates.
- `adr/0006-adopt-handover-telemetry.md` - accepted, in force. The
  debt issue replaces the handover issue in fast mode, and the debt
  template carries the Telemetry section.
- `adr/0012-grant-the-loop-the-automation-authority.md` - accepted,
  in force. The change grants the loop no new authority, and the
  loop skip rule keeps the loop out of prototype debt.

## New Durable ADRs Created

### 0016 - Fast-mode delivery contract

- Status: proposed
- Date: 2026-11-10

#### Context

The full pipeline discipline costs more than a prototype is worth in
a 1-1 decomposition session. The operator needs working results in
minutes, and the skips need one durable record per run.

#### Decision

The `fast:` prefix selects a reduced flow for one invocation. The run
skips the spec artifacts, the new test matrix, the quality gates, and
the agent dispatches, and it opens one technical debt issue before
the merge. Rejected options: a separate fast-pipeline skill, because
one flow with one prefix keeps the modes honest. Direct pushes to
main, because the pull request keeps the diff reviewable. One
standing ledger issue, because debt items mix across runs and the
closure rule gets vague.

#### Consequences

Fast runs carry no spec, no new tests, and no gate verdicts, so the
debt issue is the only run record besides the diff. The unwaited CI
run stays the backstop, and a red result needs an immediate fix. The
debt issue stays open until a normal-pipeline run pays the items, so
prototype debt stays visible in the issue list.
