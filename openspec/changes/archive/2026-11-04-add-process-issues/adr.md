# ADR Review Manifest

- Status: completed
- Review date: 2026-11-04

## Review Summary

One durable decision. The change gives the issue loop the authority to merge its own pull requests, close issues, and run the fix path without per-PR review. The record lands as `adr/0012` at archive.

## In-Force ADRs Reviewed

- `adr/0001-add-intent-driven-harness.md` - accepted, in force. The change adds one skill and one tool to the existing harness surface, and it adds no second workflow.
- `adr/0002-claude-code-single-harness.md` - accepted, in force. The loop runs inside a Claude Code session and uses no other agent runtime.
- `adr/0004-enforce-ste-in-specs.md` - accepted, in force. All change prose follows the mechanical rule set, and the gate passes it.
- `adr/0005-adopt-ub-mode-and-quality-tools.md` - accepted, in force. The new Python passes the three gates, crapper, dryer, and mutator, on changed paths.
- `adr/0006-adopt-handover-telemetry.md` - accepted, in force. The loop skips handover issues, and handover issues stay the telemetry record for merged work.
- `adr/0010-adopt-spec-governed-agent-gates.md` - accepted, in force. The capability stays outside the harness registry, so the ordinary gates govern it.
- `adr/0011-pin-glm-5-3-flash-on-every-role.md` - accepted, in force. The change pins no model and adds no `gates.yaml`.

## New Durable ADRs Created

### 0012 - Grant the process-issues loop the automation authority

- Status: proposed
- Date: 2026-11-04

#### Context

The `feature-pipeline` skill assumes an interactive operator. It asks the operator questions, waits for plan approval, and merges through reviewed pull requests. Issue 86 asks a loop to run the pipeline for each open issue and to merge the proposal PR itself. The operator reviews specs in the issue, not in a PR review session.

#### Decision

The loop holds the automation authority. It merges its own proposal and implementation pull requests to `main`, closes issues, and runs the fix path without per-PR review. The control is the two-label gate: a spec-carrying change waits at `waiting-human-approval`, and only `human-approved` resumes it. The fix path relies on the suite and the three quality gates as its defect control. The `gh pr merge` allow rule in `.claude/settings.json` is a deliberate part of this grant. Rejected options: per-PR human review, because it defeats the loop and the issue demands the merge step. A lock file for the single-run rule, because a stale lock wedges the loop worse than the race it prevents.

#### Consequences

Every session in this repo can merge to `main` through the allowed patterns, so the allow set is part of the trust boundary. The two-label gate is the only review control for spec-carrying changes, and a mistaken approval implements at once. The fix path ships without per-PR review, so the gates are its only defect control. The authority extends to future loop-like skills unless a superseding ADR narrows it.
