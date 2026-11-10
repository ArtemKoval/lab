# 0016 - Fast-mode delivery contract

- Status: accepted
- Date: 2026-11-11

## Context

The full pipeline discipline costs more than a prototype is worth in
a 1-1 decomposition session. The operator needs working results in
minutes, and the skips need one durable record per run.

## Decision

The `fast:` prefix selects a reduced flow for one invocation. The run
skips the spec artifacts, the new test matrix, the quality gates, and
the agent dispatches, and it opens one technical debt issue before
the merge. Rejected options: a separate fast-pipeline skill, because
one flow with one prefix keeps the modes honest. Direct pushes to
main, because the pull request keeps the diff reviewable. One
standing ledger issue, because debt items mix across runs and the
closure rule gets vague.

## Consequences

Fast runs carry no spec, no new tests, and no gate verdicts, so the
debt issue is the only run record besides the diff. The unwaited CI
run stays the backstop, and a red result needs an immediate fix. The
debt issue stays open until a normal-pipeline run pays the items, so
prototype debt stays visible in the issue list.
