# Proposal: add-crm-engine-pilot

## Why

The lab needs a CRM engine that a skill can onboard to a new domain from a free-form description. The UnderCover project holds a working operations backoffice with an agent, but it mixes the engine with one insurance domain. This change ports the week one milestones and puts the engine and the domain in separate places from the start.

## What Changes

- Add `crm/`, a standalone project: a FastAPI and SQLite backend, a React dashboard, and a LangGraph agent harness on OpenRouter.
- Add the domain-pack seam: `crm/domains/insurance/` holds the manifest, the policy documents, the seed data, the instructions, and the evals. The engine reads the pack through one loader and the `CRM_DOMAIN` variable.
- Rename the engine vocabulary: claim becomes case, payout becomes award, handler becomes worker, and the policy record becomes contract. The pack keeps the insurance wording in its content and labels.
- Port milestone `week1day3` as the pilot: the queue, case pages, one case agent, decisions, the award limit, sign-off, and payment.
- Port milestone `week1day5` as the harness. Queue runs take a cap. The run keeps a to-do list and hands each case to one fresh subagent. The agent looks up document sections. The failure path recovers, and the run examines the queue for missed cases.
- Keep every test hermetic: pytest on a stub model, vitest, and Playwright e2e with stand-in servers. No test calls a model or a network.
- Add `crm/.devcontainer/`, registry units for the Python and Node dependencies, and the `crm-app` skill.
- Add `crm/docs/` for the product documents, written in this house style.
- Add a guard suite at `tests/crm_infra/` for the devcontainer, the registry, and the skill. Add a suite test that bans domain nouns in engine code.

## Capabilities

### New Capabilities

- `crm-engine`: The backend API, the queue, decisions, awards, sign-off, payment, queue runs, and the agent harness behavior for week one.
- `crm-domain-pack`: The pack contract for week one: the manifest, discovery, the seed data, the documents, and the instructions.

### Modified Capabilities

## Impact

- New code under `crm/`: the `backend` and `agent` packages, `dashboard/`, `e2e/`, `domains/insurance/`, `docs/`, and `.devcontainer/`.
- `tools/project_setup/registry.json` gains the crm units. `.claude/skills/` gains `crm-app`.
- The root suite gains `tests/crm_infra/`. `README.md` and `CLAUDE.md` gain the project entry.
- A clean clone needs `uv` and the crm Python and Node dependency sets. No existing project changes.
