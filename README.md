# lab

A personal lab of Art Koval. The repository holds small projects, tools, and the Claude Code harness that builds them.

`CLAUDE.md` is the source of truth for conventions. Each project has its own README with the exact commands.

## Repository layout

| Path | Contents |
| --- | --- |
| `adr/` | Architectural decision records. An accepted ADR changes only through a superseding ADR. |
| `apple/fm/` | Experiments with the Apple Foundation Model. |
| `configs/` | Machine configs, for example WezTerm. |
| `fde/` | A desktop chat app for OpenRouter. |
| `glossary/` | Domain and technical terms for the specs. |
| `llm_ops/` | LLM operations experiments. |
| `notebooks/` | Standalone teaching notebooks. |
| `openspec/` | Behavior specs and the OpenSpec change workflow. |
| `tests/` | The root test suite. |
| `tools/` | Standalone command line tools. |
| `.claude/` | The Claude Code harness: skills, agents, hooks, and the output style. |

## Projects

| Project | What it is | Documentation |
| --- | --- | --- |
| `fde` | A desktop chat app for OpenRouter. The user interface is Electron. An embedded Python backend talks to OpenRouter. | `fde/README.md`, the `fde-app` skill |
| `llm_ops/eval` | A DeepEval script that uses a local apfel server as the judge. It runs in a devcontainer. | `llm_ops/eval/README.md`, the `apfel-eval` skill |
| `tools/zai_routing_audit` | A stdlib CLI that audits the model routing of z.ai behind Claude Code. Its venv interpreter runs the root test suite. | `tools/zai_routing_audit/README.md`, the `zai-routing-audit` skill |
| `tools/devcontainer_init` | A stdlib CLI that scaffolds a devcontainer with an Ubuntu LTS base, git, node, and uv. | `tools/devcontainer_init/README.md`, the `devcontainer-init` skill |
| `tools/plan_exec` | A stdlib CLI that extracts task briefs, packages review diffs, and keeps append-only execution ledgers. | `tools/plan_exec/README.md`, the `openspec-apply-change` skill |
| `tools/spec_ste_check` | A stdlib CLI that enforces the mechanical ASD-STE100 rules on spec text. | `tools/spec_ste_check/README.md`, the `spec-ste-check` skill |
| `tools/crapper`, `tools/dryer`, `tools/mutator` | Vendored gate tools from `unclebob` (0BSD, pinned commits). They are the default quality gates for new Python changes: CRAP, duplication, and mutation. | the vendored READMEs, the `ub-mode` skill |

The devcontainer for the UnderCover contribution lives in `fde/.devcontainer/`. The root suite guards it in `tests/undercover_devcontainer/`.

## Setup for a clean clone

1. Read `tools/project_setup/registry.json`. It names the units that a clean clone must have.
2. In Claude Code, use the `project-setup` skill. The skill examines each unit. After you give permission, it installs the units that the clone does not have.
3. If you do not use Claude Code, run the `install` command of each unit.

## Common commands

Run the root test suite from the repository root. By default, it opens no network connection and uses no daemon.

```bash
tools/zai_routing_audit/.venv/bin/python -m pytest
```

The e2e tests run only with their gate variables. They must have a network or a Docker daemon.

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
npm run dev
```

Run the `fde` suites:

```bash
npm test                    # JS suite
.venv/bin/python -m pytest  # backend suite
```

The `llm_ops/eval` commands run in a devcontainer. See `llm_ops/eval/README.md` and the `apfel-eval` skill.

## Specs and decisions

The repository uses [OpenSpec](https://github.com/Fission-AI/OpenSpec) with the `intent-driven` schema (`openspec/schemas/intent-driven/`).

- Behavior specs live in `openspec/specs/`. They are the source of truth.
- In-flight changes live in `openspec/changes/`.
- To propose a change, run `/opsx:propose` in Claude Code. To build it, run `/opsx:apply`. To archive it, run `/opsx:archive`.
- The proposal PR merges to `main` before implementation starts. The implementation PR merges before the archive PR. The `openspec-git-discipline` skill owns these gates.

Durable decisions live in `adr/`:

- [0001 - Adopt the intent-driven harness](adr/0001-add-intent-driven-harness.md)
- [0002 - Claude Code is the single harness](adr/0002-claude-code-single-harness.md)
- [0003 - Adopt the superpowers execution mechanics](adr/0003-adopt-superpowers-execution-mechanics.md)
- [0004 - Enforce ASD-STE100 in specs](adr/0004-enforce-ste-in-specs.md)

The glossary files `glossary/business.md` and `glossary/technical.md` define the domain and technical terms.

## The harness

The harness surfaces live under `.claude/`:

- Skills in `.claude/skills/`, agents in `.claude/agents/`, and commands in `.claude/commands/`.
- The `feature-pipeline` skill owns the delivery flow for every repository change.
- Two hooks in `.claude/hooks/`, wired in `.claude/settings.json`: the `SessionStart` charter hook and the `PreToolUse` spec STE gate on `Write` and `Edit`.
- The output style `.claude/output_styles/asd-ste100.md`. All repository prose is in ASD-STE100 Simplified Technical English. Vendored upstream files are exempt.
- The MCP config `.mcp.json` starts the `zai-routing-audit` server.

## Adopt the harness in a new repository

1. Copy `openspec/schemas/intent-driven/` into the new repository.
2. Set `schema: intent-driven` in `openspec/config.yaml`.
3. Port the skills and agents from the template at `github.com/intent-driven-dev/intent-driven-template`, commit `b5bda460a2180a55fc508fdedc4ef058d95355db`.
4. Create `adr/0001`.
5. Read `openspec/schemas/intent-driven/README.md`.

## CI

GitHub Actions runs two workflows in `.github/workflows/`:

- `tests.yml` runs the root suite on pull requests and on `main`. It ignores changes under `fde/` and `llm_ops/`. It measures coverage on `plan_exec` and `spec_ste_check` and runs ruff.
- `build.yml` packages `fde` on `fde` pull requests and on version tags.

## License

MIT. See `LICENSE`.
