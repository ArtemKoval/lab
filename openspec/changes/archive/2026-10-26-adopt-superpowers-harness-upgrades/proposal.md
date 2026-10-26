# Proposal: adopt-superpowers-harness-upgrades

## Why

The harness discipline lives only in the skill text a session invokes, so a long session that compacts loses the contract. Long apply runs keep progress and rulings only in conversation memory, so a run can repeat completed work. Debugging, completion claims, skill authoring, and review replies follow no fixed procedure. The obra/superpowers project (MIT) ships small, proven mechanics for each gap. The user approved adoption of all seven mechanics on 2026-10-23.

## What Changes

- A SessionStart hook injects a short harness charter at session start, after a clear, and after a compaction, so the contract survives context loss.
- A new stdlib CLI, `tools/plan_exec`, extracts one task brief, packages a review diff, and keeps an append-only execution ledger that survives compaction.
- Three ported skills: `systematic-debugging`, `verification-before-completion`, `writing-skills`.
- The `feature-pipeline` skill gains review-reception rules, a model-selection rule, a discard contract, worktree provenance cleanup, and a builder check; its stale "no hooks yet" statements go.
- ADR 0003 records the adoption and designates upstream `diagnosing-superpowers` as the reference design for the future Step 14 Analyse sub-step.
- A CI job runs the root test suite and the `plan_exec` coverage and lint gates on pull requests that touch the harness, the tests, or the tools (`fde/**` and `llm_ops/**` excluded); mutation stays a local gate.

## Capabilities

### New Capabilities

- `plan-exec`: the plan execution tooling. A stdlib CLI with `brief`, `package`, and `ledger` subcommands, hermetic tests, and the house quality gates.

### Modified Capabilities

- `intent-driven-harness`: the charter hook, the three adoption skills, the new pipeline rules, ADR 0003, and the CI job join the harness contract.

## Impact

- New files: `.claude/hooks/harness-charter.sh`, `.claude/hooks/charter.md`, `tools/plan_exec/**`, `tests/plan_exec/**`, `tests/claude_infra/test_harness_charter.py`, `.github/workflows/tests.yml`, `adr/0003-adopt-superpowers-execution-mechanics.md`, and the two council-note files beside the proposal and design artifacts.
- Edited files: `.claude/settings.json` (hooks key through the update-config skill), `.claude/skills/feature-pipeline/SKILL.md`, `.claude/skills/openspec-apply-change/SKILL.md`, `.claude/skills/architectural-decision-records/preferences.md`, `CLAUDE.md`, `.coveragerc`, `.gitignore`, `tests/claude_infra/test_intent_driven_harness.py`.
- No new dependency, setup unit, or MCP server. No change to runtime projects (`fde`, `llm_ops/eval`, `notebooks`).
- Every session start carries the charter text in context (about 60 lines).
