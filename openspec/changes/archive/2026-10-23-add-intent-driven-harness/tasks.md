# Tasks

## 1. Schema and config

- [x] 1.1 Copy `openspec/schemas/intent-driven/` (schema, README, five templates) from upstream commit `b5bda46`
- [x] 1.2 Run `openspec schema validate intent-driven` from the repo root and make it pass (schema commands use the working directory as the project root)
- [x] 1.3 Switch `openspec/config.yaml` to `schema: intent-driven` and apply the rule map from design D5

## 2. Agents and skills

- [x] 2.1 Port the four agent files to `.claude/agents/` with Claude Code frontmatter (design D4)
- [x] 2.2 Port the eleven skills to `.claude/skills/` with provenance metadata and the D3 adaptations
- [x] 2.3 Check every ported file for OpenCode-only paths or commands and fix them per D3

## 3. Discipline and docs

- [x] 3.1 Edit the `feature-pipeline` skill: two-merge Step 1.5, archive gate in Step 13, grill-me and adversarial references in the inner loop and Step 12 (design D7)
- [x] 3.2 Add the discipline line and the `adr/` entry to CLAUDE.md
- [x] 3.3 Add a short harness section to README.md

## 4. ADRs and glossary

- [x] 4.1 Write `adr/0001-add-intent-driven-harness.md` and `adr/0002-claude-code-single-harness.md` (design D8)
- [x] 4.2 Seed `glossary/business.md` and `glossary/technical.md` with the design D9 terms

## 5. Tests

- [x] 5.1 Add `tests/claude_infra/test_intent_driven_harness.py` with the five test groups from design D10
- [x] 5.2 Run the root suite and make it green

## 6. Gates, review, merge

- [x] 6.1 Run `openspec validate 2026-10-23-add-intent-driven-harness --type change --strict` and make it pass
- [ ] 6.2 Run the adversarial review over the final diff and fix every confirmed finding
- [ ] 6.3 Publish, open the pull request, merge with squash, delete the branch, open the handover issue
