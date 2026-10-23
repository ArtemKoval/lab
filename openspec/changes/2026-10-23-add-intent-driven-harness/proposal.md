# Proposal

## Why

The harness runs every repository change through one pipeline. The pipeline records requirements, but it loses decisions, unanswered questions, and review pressure between changes. The intent-driven template adds those pieces around OpenSpec as a schema, domain skills, and review agents. Adoption turns each change into one intent that drives proposal, specs, design, ADRs, and tasks.

## What Changes

- Add the `intent-driven` schema as project-local files under `openspec/schemas/intent-driven/`, ported from upstream commit `b5bda46` of `intent-driven-dev/intent-driven-template`. Switch `openspec/config.yaml` to `schema: intent-driven`.
- Add the immutable ADR folder `adr/` at the repo root. Seed it with ADR-0001, which records this adoption decision, and ADR-0002, which records the single-harness decision.
- Add four Claude Code subagents under `.claude/agents/`: `adversarial-author`, `adversarial-reviewer`, `senior-dev`, `senior-qa`.
- Add eleven skills under `.claude/skills/`: `grill-me`, `adversarial-authoring`, `architectural-decision-records`, `c4-diagrams`, `gherkin-authoring`, `glossary`, `openspec-git-discipline`, `verify-change` (renamed from upstream `openspec-verify-change`, which the CLI owns), `spec-as-source`, `acceptance-test-authoring`, and `test-driven-development`.
- Turn on git discipline: proposal artifacts merge to `main` before apply starts, and implementation merges before archive runs. Record the flow in the `feature-pipeline` skill and in CLAUDE.md.
- Install the eleven skills as independent directories. Disable `spec-as-source` and `glossary` through commented config rules, like the template default. `acceptance-test-authoring` is its own skill, not a sub-skill.
- Seed `glossary/business.md` and `glossary/technical.md` at the repo root with the terms the glossary skill reads.

## Capabilities

### New Capabilities

- `intent-driven-harness`: the OpenSpec schema, the skills, the subagents, the ADR folder, and the merge discipline that carry each change from proposal to archive.

### Modified Capabilities

- None. The switch changes the shape of change artifacts. It does not change any shipped tool behavior.

## Impact

- New files: `openspec/schemas/intent-driven/` (schema, README, five templates), `adr/0001-add-intent-driven-harness.md`, `adr/0002-claude-code-single-harness.md`, `.claude/agents/` (4 files), eleven skill directories under `.claude/skills/`, and the two glossary files.
- Edits: `openspec/config.yaml`, `.claude/skills/feature-pipeline/SKILL.md`, `CLAUDE.md`, and `README.md`.
- New structural tests under `tests/claude_infra/`. They use the standard library only.
- No new dependencies. No new setup units in `tools/project_setup/registry.json`; the `openspec-cli` unit already exists there.
