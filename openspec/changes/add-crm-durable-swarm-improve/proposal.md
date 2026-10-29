# Proposal: add-crm-durable-swarm-improve

## Why

The crm engine pilot holds one case agent that loses its work on a restart, works one case at a time, and has no measure of its own accuracy. The upstream week two milestones solve all three: durable checkpoints, a dispatcher with parallel case agents and a scoreboard, and an improver with versions and a judge. Porting them turns the pilot into an operations platform.

## What Changes

- Port milestone `week2day3` as durable state: the deterministic award engine in the pack as `rules.py`, a calculation the decision must match, a hand-written case-agent graph, checkpoints that survive a restart through a saver factory, an agent service on port 8002, sign-off that resumes the case, and idempotent decision and payment repeats.
- Port milestone `week2day4` as the swarm: a model-free dispatcher with up to 25 case agents at once, cost and time per model call, evaluations on the queue set and the held-out set, and a scoreboard page.
- Port milestone `week2day5` as self-improvement: agent configurations in versions, a judge for explanations, improver rounds with recipes, spending limits, the keep-or-rollback verdict, worker sign-in with roles, and the settings page.
- Replace Supabase Auth with a small local auth service that issues signed JWTs and serves JWKS, on the same contract the backend already verifies. The AWS rollout later points the same variables at Cognito.
- Move `data/models.json` and `data/improvement.json` into the pack, and read the seeded settings through the manifest.
- Keep every test hermetic: SQLite stays the test database, the stub model stands in for OpenRouter, and the e2e boots its own auth stand-in.
- Extend `crm/port/port.py` passes and keep the two ported docs (`docs/SWARM.md`, `docs/IMPROVE.md`) in the house style.

## Capabilities

### New Capabilities

- `crm-durable-state`: Checkpoints that survive a restart, sign-off that resumes a case, idempotent repeats, and the deterministic award engine behind the pack rules contract.
- `crm-swarm`: The dispatcher, cost and time records, evaluations, and the scoreboard.
- `crm-self-improvement`: Versions, the judge, improver rounds and recipes, spending limits, the verdict rule, sign-in with roles, and settings.

### Modified Capabilities

- `crm-engine`: The case agent becomes a hand-written graph, the case agent loses its pay tool, a sign-off records the worker instead of paying, and decision repeats are idempotent.

## Impact

- `crm/backend` gains SQLAlchemy Core with a dual SQLite and Postgres engine, the runs, versions, rounds, and settings routers, and the auth verification.
- `crm/agent` gains the graph, the dispatcher, the service on port 8002, the saver factory, and the improver.
- `crm/domains/insurance` gains `rules.py`, the models and improvement data, and the changed instructions.
- `crm/dashboard` gains the scoreboard, evaluation, configuration, improvement, settings, and sign-in pages.
- `crm/auth` is a new small Node service. `.env.example` and the devcontainer gain the auth and Postgres variables. CI keeps gating the crm Python paths.
