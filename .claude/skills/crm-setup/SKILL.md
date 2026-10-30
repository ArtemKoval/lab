---
name: crm-setup
description: Install everything the crm engine needs on a dev box and run it locally. Use this skill to prepare a machine for the crm engine, to install the crm dependencies, to seed the crm database, to run the crm backend, agent, copilot, and dashboard locally, or to find what a clean clone still lacks. Gives the commands, the ports, and the parts that need no model key.
---

# crm-setup

The crm project lives at `crm/`. It needs Python 3.12 or newer, Node 22 or
newer, and uv. Docker is optional. It runs the local AWS emulator for the
deployment targets.

## Examine the system tools

```bash
uv --version
python3 --version
node --version
docker info   # optional, only for the emulator
```

If a command fails, install that tool first. A clean clone gets its units
from `tools/project_setup/registry.json`. The `project-setup` skill examines
the units, and installs each unit that the clone does not have. The crm
units are `uv`, `crm-python-deps`, and `crm-node-deps`.

## Install the dependencies

```bash
uv sync --project crm
npm install --prefix crm
```

## Make the env file

```bash
cp crm/.env.example crm/.env
```

The file works with no model key. Put `OPENROUTER_API_KEY` in the file only
when you want live agent runs.

## Seed the database

```bash
npm run seed --prefix crm
```

The command builds `crm/crm.db` from the active domain pack. Run the command
again after any change to the pack seed data.

## Run it

```bash
npm run dev --prefix crm
```

The command starts the services: the backend on 8000, the agent on 8080,
the copilot on 8081, and the dashboard on 5173. It also starts the context
server. Open `http://localhost:5173` for the queue.

## Run the gates

```bash
npm run check --prefix crm
```

Exit 0 is green. Exit 1 means a gate failed, and the output names the tool.
Repair that tool's finding, and run the command again.

## What needs no model key

- The Python suite, the TypeScript suite, the Playwright e2e, and the pack
  smoke run work with no model key. The smoke run is
  `.venv/bin/python smoke.py <pack>` from `crm/`.
- A live agent run needs a model key. Put `OPENROUTER_API_KEY` in
  `crm/.env`, and run `uv run -m agent <case-id>` from `crm/`. Without the
  key, a live run fails on its first decision.

With Docker, the `crm-local-aws` skill also runs the app with its AWS
wiring pointed at the local floci emulator.
