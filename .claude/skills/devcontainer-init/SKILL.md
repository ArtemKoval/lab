---
name: devcontainer-init
description: Scaffold a devcontainer for a project directory with the latest Ubuntu LTS, git, node, and uv wired up for VS Code. Use when the user asks to create a devcontainer or dev container config, or to containerize a new or existing project. Gives the command, the flags, the exit codes, and the build commands.
---

# devcontainer-init

## When to use

The user asks for a devcontainer, a dev container config, or a container for a new or existing project. The tool writes one file: `.devcontainer/devcontainer.json`.

## Command

Run from `tools/devcontainer_init/` with any Python 3.11 or newer:

```bash
cd tools/devcontainer_init
python3 -m devcontainer_init /path/to/project
```

Flags:

- `--os VERSION` — Ubuntu version for the base image; the default `26.04` is the latest LTS.
- `--extension ID` — add a VS Code extension to the config; repeatable.
- `--force` — overwrite an existing `devcontainer.json`.
- `--json` — machine-readable output with `ok`, `written`, `os`, and `extensions`.

Exit code 0 means the file is written. Exit code 2 means the target does not exist, or a config is already there and `--force` is missing. A refusal never touches the existing file.

## What the config contains

The `ubuntu:26.04` image, plus the features `common-utils:2`, `git:1` (`os-provided`), `node:2` (`lts`), and `devcontainers-extra/features/uv:1` (`latest`). `remoteUser` is `vscode`. There is no Dockerfile. The image has no Python; run `uv python install` inside the container for interpreters.

## Build and check the result

Docker must run; Docker Desktop starts by hand on this machine. First use of the CLI downloads it through npx:

```bash
npx --yes @devcontainers/cli build --workspace-folder /path/to/project
npx --yes @devcontainers/cli exec --workspace-folder /path/to/project -- node --version
```

## Tests

The hermetic tests run with the root suite: `tools/zai_routing_audit/.venv/bin/python -m pytest tests/devcontainer_init`. The live build check runs opt-in with `DEVCONTAINER_INIT_E2E=1 ... -m e2e`.
