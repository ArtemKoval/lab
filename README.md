# lab
A vessel for the various engineering artifacts

## Installing OpenSpec
- https://github.com/Fission-AI/OpenSpec/blob/main/docs-lab/start/installation.md#install-with-your-ai-assistant

To install OpenSpec from the command line, run `npm install -g @fission-ai/openspec@latest`. You must have Node.js 20.19.0 or newer.

## Prepare a clean clone
The file `tools/project_setup/registry.json` names the units that a clean clone must have. In Claude Code, use the `project-setup` skill. The skill examines each unit. It installs each unit that the clone does not have after you give permission.

## Notebooks
The `notebooks/` directory holds standalone teaching notebooks. The test module `tests/notebooks/` guards each notebook's structure and logic with the standard library only. Run it with the root suite command in CLAUDE.md.

## Intent-driven harness

The repo runs on the intent-driven schema: each change carries proposal, Gherkin specs, design, an ADR manifest, and tasks. The schema files live at `openspec/schemas/intent-driven/`, ported from the upstream template at commit `b5bda460a2180a55fc508fdedc4ef058d95355db`.

Discipline: the proposal PR merges to `main` first. Implementation merges next. The archive PR runs last. The `openspec-git-discipline` skill and the `feature-pipeline` skill own the gates. Durable decisions live in `adr/`.

Surfaces: eleven ported skills and four agents under `.claude/`, the `grill-me` questions skill, the `adversarial-authoring` skill with its author and reviewer agents, `verify-change` before each archive, and the glossary under `glossary/`. The `spec-as-source` layer ships installed but disabled.

Adopt it for a new repo: copy `openspec/schemas/intent-driven/`, switch `openspec/config.yaml` to `schema: intent-driven`, port the skills and agents from the pinned commit, seed `adr/0001`, and read `openspec/schemas/intent-driven/README.md`.
