# Proposal

## Why

A new devcontainer means a hand-written config file. The writer must find image tags, feature names, and versions every time. A generator turns that work into one command and keeps the choices in one reviewed place.

## What Changes

- Add `tools/devcontainer_init/`, a standard-library Python CLI that writes `.devcontainer/devcontainer.json` into an existing target directory.
- The generated config uses the `ubuntu:26.04` image, the latest LTS at the time of writing. The `--os` flag picks another version.
- The generated config references four features: `common-utils:2`, `git:1` with the `os-provided` version, `node:2` with the `lts` version, and `devcontainers-extra/features/uv:1` with the `latest` version.
- The generated config sets `remoteUser` to `vscode` and carries a `customizations.vscode.extensions` list. The CLI flag `--extension` appends to that list. The default list is empty.
- The CLI accepts `--json` for machine output and `--force` to overwrite. Exit code is 0 on success and 2 on operational failure. Without `--force`, the CLI refuses to overwrite an existing `devcontainer.json`. The target directory must exist.
- Add hermetic unit and CLI tests under `tests/devcontainer_init/`. Add an opt-in e2e module, gated on `DEVCONTAINER_INIT_E2E=1`, that validates the generated config and builds the container.
- Add the `devcontainer-init` skill and a README for the tool. Add the tool to the Projects list in CLAUDE.md.

## Capabilities

### New Capabilities

- `devcontainer-init`: the scaffold of a devcontainer configuration with a pinned latest-LTS Ubuntu base, the git, node, and uv features, a VS Code remote user, safe overwrite behavior, and machine-readable output.

### Modified Capabilities

- None.

## Impact

- New files: `tools/devcontainer_init/` (package, README), `tests/devcontainer_init/`, and `.claude/skills/devcontainer-init/SKILL.md`. Edits: `CLAUDE.md`.
- No new dependencies. The tool uses the standard library only. The e2e module must have Docker and `@devcontainers/cli` at run time. It stays opt-in.
- No effect on existing tools, specs, or the default pytest run.
