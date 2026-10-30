---
name: crm-app
description: Build, test, and run the crm engine with its insurance domain pack. Use this skill to run the crm backend and dashboard, to run its Python or TypeScript suites and gates, to seed or reseed its database, to work one case with the agent, or to find the cause of a failed crm check. Gives the commands, the ports, and the exit codes.
---

# crm-app

The crm project lives at `crm/`. It is a CRM engine with domain packs. The
active pack is `insurance` unless `CRM_DOMAIN` names another. Engine code
carries no domain noun. The pack carries all of them.

## Set up

```bash
uv sync --project crm
npm install --prefix crm
```

A clean clone needs `uv`, Python 3.12 or newer, and Node 22 or newer. The
`project-setup` skill installs the units `uv`, `crm-python-deps`, and
`crm-node-deps`.

## Run

```bash
cd crm
cp .env.example .env   # once. The OPENROUTER_API_KEY line is optional
npm run seed           # build crm.db from the active pack
npm run dev            # backend on 8000, dashboard on 5173
uv run -m agent CLM-1001   # work one case on the command line
```

`npm run dev` starts the backend and the dashboard. The seed is idempotent:
it rebuilds the database, so run it again after a change to the pack seed
data. Without a model key, the dashboard and the tests work, and a live
agent run fails on its first decision.

## Test

```bash
cd crm
npm run check          # every check: python, ts, and e2e
```

- `npm run check:python` runs ruff format, ruff lint, pyright, and pytest.
- `npm run check:ts` runs prettier, eslint, tsc, and vitest.
- `npm run e2e` runs Playwright. It starts its own backend on 8001 and its
  own dashboard on 5174, and posts decisions through the API, so it needs
  no model key.

Exit codes: 0 green, 1 failed checks. The Python suite is hermetic: the
stub model in `agent/tests/stub_model.py` stands in for OpenRouter, and
every test gets its own seeded SQLite file.

## Onboard a domain

A new domain is a pack under `crm/domains/`. The `crm-onboard-domain`
skill walks the whole path. Two commands examine a pack directly, run
from the `crm/` directory:

```bash
.venv/bin/python validate.py <pack>   # exit 0 clean, 2 names findings
.venv/bin/python smoke.py <pack>      # works 3 cases on the stub model
```

## Run with the AWS wiring (floci)

The `crm-local-aws` skill starts the floci emulator, points the runtime,
gateway, and memory variables at it, and proves the invoke path with a
wiring gate. The laptop route (the agent on 8080) stays the default;
`CRM_AGENT_RUNTIME` moves the backend to the emulator.

## Gates

The repository adds three gates on the changed Python of `crm/`. Run them
from the `crm/` directory. First produce the coverage report with the crm
interpreter, then run the gates on the module you changed:

```bash
# in crm/
.venv/bin/python -m coverage run --data-file=target/coverage/python/.coverage \
  --source=backend,agent,domains -m pytest -q -o addopts=
.venv/bin/python -m coverage lcov \
  --data-file=target/coverage/python/.coverage -o target/coverage/python/lcov.info
../tools/crapper/.venv/bin/python -m crapper --threshold 10 --use-existing-coverage backend agent domains
../tools/dryer/.venv/bin/python -m dryer --threshold 0.8 --fail-above backend agent domains
# mutation, one module at a time. Expect no survivor but the documented one
../tools/mutator/.venv/bin/python -m mutator --use-existing-coverage --max-workers 4 \
  --test-command "$PWD/.venv/bin/python -m pytest -q <module tests> -o addopts=" <module>
```

The mutation gate keeps one documented equivalent survivor: the
`strict=True` flag in `backend/documents.py`, whose two lists always have
equal length. CI runs the CRAP and duplication gates for `crm/`. The
mutation gate runs per change on this host. The duplication gate covers
`backend` and `domains` only: the two API clients at `agent/api.py` and
`agent/improver_api.py` hold one function per backend operation by
contract, so their wrappers are shape-clones by design, and crapper and
mutator still gate them.

## Know

- The pack lives at `crm/domains/insurance/`. `crm/domains/loader.py` is
  the one seam. No other engine module names a pack.
- The behavior specs live under `openspec/specs/` in the repository root.
- The port tool for the next upstream milestones lives at `crm/port/`.
- The dev container lives at `crm/.devcontainer/`.
- A failed check prints the failing tool first. Fix that tool's finding,
  then run `npm run check` again.

## Headed e2e

Run the full Playwright suite headed, from `crm/`:

```bash
npm run e2e -- --headed
```

The suite starts its own backend and dashboard with stand-ins, signs in by
itself, and needs no model key. A browser window opens; close nothing.

## Visit after launch

- Dashboard: `http://localhost:5173` — sign in with a pack worker email
  (insurance: `dana.whitfield@undercover.example`, senior, or
  `marcus.oyelaran@undercover.example`, not senior; helpdesk:
  `priya.nair@fastfix.example`, lead) and the dev password `crm-dev`
  (`AUTH_DEV_PASSWORD`).
- Backend health: `http://localhost:8000/api/health`
- Agent service: `http://127.0.0.1:8080`
- Copilot: `http://127.0.0.1:8081`
- Context server: `http://127.0.0.1:8006/mcp`
- Auth service: `http://127.0.0.1:8004` (accepts any pack worker email with
  `AUTH_DEV_PASSWORD`, default `crm-dev`)

