# crm

A CRM engine with domain packs. The engine runs a backoffice queue. AI case
workers read each case and decide it against the policy documents. A human
signs off large awards, and then the engine pays them. One domain pack,
`domains/insurance/`, holds the words, the rules, and the seed data of the
first domain, a fictional travel insurer. A later change adds the skill
that onboards a new domain from a free-form description.

The project ports the week one milestones of `github.com/ed-donner/undercover`.
The engine carries generic names: case, contract, award, worker, decision.
The pack keeps the insurance wording in its content. `port/` holds the tool
that ports the next upstream milestones.

## Run it

You need Python 3.12 or newer, Node 22 or newer, and uv.

```bash
uv sync && npm install
cp .env.example .env   # the key is optional
npm run seed           # build crm.db from the active pack
npm run dev            # backend on 8000, dashboard on 5173
```

Work one case with the agent on the command line:

```bash
uv run -m agent CLM-1001
```

The `OPENROUTER_API_KEY` variable names no key in a fresh clone. The tests
and the e2e never call a model. A dev run without a key fails on the first
decision. Put a key in `.env` to work real cases.

## Examine it

```bash
npm run check   # ruff, pyright, pytest, prettier, eslint, tsc, vitest, e2e
```

The Python suite is hermetic: a stub model stands in for OpenRouter, and
every test gets its own seeded SQLite file. The e2e specs start their own
backend and dashboard on their own ports and post decisions through the
API, so they need no model either.

## Layout

| Path | What it holds |
| --- | --- |
| `backend/` | The FastAPI app, the database, and the seed |
| `agent/` | The harness, the tools, and the stub model |
| `dashboard/` | The React queue and case pages |
| `e2e/` | The Playwright specs and helpers |
| `domains/insurance/` | The first domain pack |
| `domains/loader.py` | The one seam between the engine and the packs |
| `docs/` | The product documents |
| `port/` | The upstream port tool |
| `.devcontainer/` | The dev container |

## Documents

`docs/BRIEF.md` states what the product does. `docs/HARNESS.md` states how
the agent works the queue. `docs/PROCESS.md` gives the commands and the
rules of work. `docs/TECH_STACK.md` names the stack. `docs/STATUS.md`
tracks the state of the port. The full behavior specs live in the
repository root under `openspec/specs/`.
