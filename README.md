# library_crm

A CRM engine with domain packs, and the agentic harness that builds it. The
engine runs a backoffice queue: AI case workers read each case, decide it
against the pack's policy documents, and a human signs off the large
outcomes. Every domain word lives in a pack, so one engine runs a travel
insurer, an IT helpdesk, an operations desk, and a public library.

`CLAUDE.md` is the source of truth for conventions. Each project has its own
README with the exact commands.

## The engine

| Pack | Domain | The desk it runs |
| --- | --- | --- |
| `insurance` | A fictional travel insurer | Claims, service credits, lead sign-off over $1,000 |
| `helpdesk` | FastFix IT support | Outage and response credits on support plans |
| `opsdemo` | Nimbus OpsDesk | Escalation effort in engineer-hours, no money |
| `library` | Northgate Public Library | Loan requests, 14-day terms, the three loan cap |

`CRM_DOMAIN` names the active pack, and the engine carries no domain word of
its own. The full behavior specs live under `openspec/specs/`.

## Run the engine

You need Python 3.12 or newer, Node 22 or newer, and uv. From `crm/`:

```bash
uv sync && npm install
cp .env.example .env   # the model key is optional
npm run seed           # build crm.db from the active pack
npm run dev            # backend on 8000, dashboard on 5173
```

The dashboard lives on `http://localhost:5173`. Sign in with a worker email
of the active pack and the dev password `crm-dev`; the emails sit in
`crm/README.md`. The suite and the e2e need no model key.

```bash
npm run check --prefix crm     # ruff, pyright, pytest, prettier, eslint, tsc, vitest, e2e
uv run python validate.py insurance   # examine a pack, from crm/
```

The devcontainer and the floci emulator run the same commands in a
container and against the local AWS emulator; the `crm-setup`,
`crm-local-aws`, and `crm-aws-rollout` skills own the three ways to run.

## One command: everything, in the devcontainer, on floci

The script installs and runs the whole solution locally: the devcontainer
with all services, the AWS targets on the floci emulator, the pack
validated and seeded, and the stack left running. In Claude Code the same
path is the `crm-local-aws` skill.

```bash
crm/local-up.sh library   # any pack name; then open http://localhost:5173
```

Stop with `docker rm -f crm-floci` and `docker rm -f crm-dev`.

## The assignment around it

The library domain landed as one assignment
([issue 1](https://github.com/ArtemKoval/library_crm/issues/1)), and its
records stay in the repository:

| Record | Where |
| --- | --- |
| The setup around the agents | [HARNESS.md](HARNESS.md) |
| The team-scale plan | [SCALE.md](SCALE.md) |
| The wiki pages, with screenshots | [docs/wiki/](docs/wiki/Home.md) |
| Four narrated videos | [docs/videos/](docs/videos/) |

## The rest of the lab

| Project | What it is | Documentation |
| --- | --- | --- |
| `fde` | A desktop chat app for OpenRouter. The user interface is Electron. An embedded Python backend talks to OpenRouter. | `fde/README.md`, the `fde-app` skill |
| `llm_ops/eval` | A DeepEval script that uses a local apfel server as the judge. It runs in a devcontainer. | `llm_ops/eval/README.md`, the `apfel-eval` skill |
| `tools/zai_routing_audit` | A stdlib CLI that audits the model routing behind Claude Code. Its venv interpreter runs the root test suite. | the README, the `zai-routing-audit` skill |
| `tools/devcontainer_init` | A stdlib CLI that scaffolds a devcontainer with an Ubuntu LTS base, git, node, and uv. | the README, the `devcontainer-init` skill |
| `tools/plan_exec` | Task briefs, review diffs, and append-only execution ledgers. | the README, the `openspec-apply-change` skill |
| `tools/spec_ste_check` | The mechanical ASD-STE100 gate for spec text. | the README, the `spec-ste-check` skill |
| `tools/slidecast` | One narrated video from one JSON deck. | the README |
| `tools/crapper`, `tools/dryer`, `tools/mutator` | The vendored quality gates: CRAP, duplication, and mutation. | the vendored READMEs, the `ub-mode` skill |
| `notebooks` | Standalone teaching notebooks. | `tests/notebooks/` |

The devcontainer for the UnderCover contribution lives in `fde/.devcontainer/`.
The root suite guards it in `tests/undercover_devcontainer/`.

## Repository layout

| Path | Contents |
| --- | --- |
| `crm/` | The CRM engine, its dashboard, its e2e suite, and the domain packs. |
| `adr/` | Architectural decision records. An accepted ADR changes only through a superseding ADR. |
| `docs/` | The wiki pages and the videos of the assignment. |
| `glossary/` | Domain and technical terms for the specs. |
| `openspec/` | Behavior specs and the OpenSpec change workflow. |
| `tests/` | The root test suite. |
| `tools/` | Standalone command line tools. |
| `.claude/` | The Claude Code harness: skills, agents, hooks, and the output style. |

## Setup for a clean clone

Read `tools/project_setup/registry.json`, and use the `project-setup` skill
in Claude Code. It examines each unit, and installs the units the clone
lacks after you give permission.

## Common commands

Run the root test suite from the repository root. By default, it opens no
network connection and uses no daemon.

```bash
tools/zai_routing_audit/.venv/bin/python -m pytest
```

The e2e tests run only with their gate variables. The zai and devcontainer
tests need a network or a Docker daemon. The gate-tool smoke needs only the
three built tool venvs.

```bash
ZAI_ROUTING_AUDIT_E2E=1 tools/zai_routing_audit/.venv/bin/python -m pytest -m e2e
DEVCONTAINER_INIT_E2E=1 tools/zai_routing_audit/.venv/bin/python -m pytest -m e2e
UB_TOOLS_E2E=1 tools/zai_routing_audit/.venv/bin/python -m pytest -m e2e
```

Develop `fde`:

```bash
cd fde
npm ci
npm run py:setup
```
