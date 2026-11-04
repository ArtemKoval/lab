# 0012 - Grant the process-issues loop the automation authority

- Status: accepted
- Date: 2026-11-04

## Context

The `feature-pipeline` skill assumes an interactive operator. It asks the operator questions, waits for plan approval, and merges through reviewed pull requests. Issue 86 asked for a loop that runs the pipeline for each open GitHub issue and merges the proposal PR itself. The operator reviews specs in the issue, not in a PR review session, and the review happens through the `waiting-human-approval` and `human-approved` labels. The alternatives: per-PR human review, which defeats the loop and contradicts the approved flow, or a lock file for the single-run rule, where a stale lock wedges the loop worse than the race it prevents.

## Decision

The process-issues loop holds the automation authority. It merges its own proposal and implementation pull requests to `main`, closes issues, and runs the no-spec fix path without per-PR review. The control is the two-label gate: a spec-carrying change waits at `waiting-human-approval`, and only `human-approved` resumes it into the apply and archive phases. The fix path relies on the suite and the three quality gates, crapper, dryer, and mutator, as its defect control. The `gh pr merge` allow rule in `.claude/settings.json` is a deliberate part of this grant, and the allow set is part of the trust boundary. The label repair step needs the label-write authority on the GitHub token, which the host tokens lack today, so the operator creates or repairs labels, or grants the scope. Rejected options: per-PR human review, because it defeats the loop and the issue demands the merge step. A lock file for the single-run rule, because a stale lock wedges the loop worse than the race it prevents.

## Consequences

Every session in this repo can merge to `main` through the allowed patterns, so the allow set is part of the trust boundary. The two-label gate is the only review control for spec-carrying changes, and a mistaken approval implements at once. The fix path ships without per-PR review, so the gates are its only defect control. The authority extends to future loop-like skills unless a superseding ADR narrows it.
