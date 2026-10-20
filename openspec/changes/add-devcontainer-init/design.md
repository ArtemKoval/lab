# Design

## Context

The repo holds standalone tools under `tools/<task_name>/` with mirrored tests under `tests/<task_name>/`. The `zai_routing_audit` tool defines the house rig: a stdlib package, a dual-path test conftest, a mutmut config in the tool directory, and gates run with the root venv (`tools/zai_routing_audit/.venv/bin/python`). See proposal.md for the motivation.

Facts checked against reality on 2026-10-20:

- The latest Ubuntu LTS is 26.04. The blessed image `mcr.microsoft.com/devcontainers/base` publishes tags only up to `ubuntu-24.04`.
- `ubuntu:26.04` exists on Docker Hub.
- Feature manifests and ghcr tags verified: `devcontainers/features/node` (2.x line, default version `lts`), `devcontainers/features/common-utils` (2.x line), `devcontainers/features/git` (1.x line, options `latest`, `system`, `os-provided`), `devcontainers-extra/features/uv` (1.x line, default version `latest`).

## Goals / Non-Goals

Goals:

- One command that turns an existing project directory into a VS Code devcontainer project.
- The generated container builds fast: image plus features, no Dockerfile, no source builds.
- The generator is standard-library only, hermetically testable, and follows the house CLI contract (`--json`, exit 0 and 2).

Non-Goals:

- No Python interpreter in the image. `uv` fetches interpreters on demand; users run `uv python install`.
- No publishing as a containers.dev template. The tool scaffolds locally.
- No MCP server. The CLI through Bash is the full surface; file scaffolding has no stateful capability worth a server.
- No project-setup registry unit. The tool needs no install; the e2e tools (Docker, `@devcontainers/cli`) are user-run and already present on the machines that run them.

## Decisions

- **Base image `ubuntu:26.04` plus the `common-utils` feature, not `devcontainers/base:ubuntu-24.04`.** The requirement is the latest LTS Ubuntu. The blessed base image lags at 24.04, so the config assembles the standard equivalent: the plain `ubuntu:26.04` image with `common-utils:2` for the `vscode` user and sudo. `remoteUser` is `vscode` because a plain image defaults to root. Alternative rejected: pinning the blessed image would violate the requirement today and silently drift instead of tracking LTS.
- **`git:1` with `version: os-provided`, not `latest` from source.** A plain Ubuntu image has no git. The `os-provided` option installs through apt in seconds; `latest` compiles git from source and slows every build. The requirement asks for git wired up, not the newest git.
- **`node:2` with `version: lts` and `uv:1` with `version: latest`.** Both versions float, so each build takes the current LTS or stable release. This matches the requirement directly. The feature majors are pinned to tags verified to exist; the patch lines stay floating.
- **The OS default lives in one constant (`DEFAULT_UBUNTU_LTS = "26.04"`).** A future LTS is a one-line change plus a test update. `--os` exists for projects that must stay on an older LTS.
- **The tool is a package (`devcontainer_init/` with `core.py`, `cli.py`, `__main__.py`), and tests mirror it in `tests/devcontainer_init/`.** This reuses the `zai_routing_audit` rig: the conftest imports the in-tree package under pytest and stands down under mutmut, and the mutmut run uses a flattened out-of-tree copy. Alternatives rejected: a single-file script would fork the house rig, and a root-level `pyproject.toml` would add repo-wide config for one tool.
- **The e2e module is opt-in through `DEVCONTAINER_INIT_E2E=1` and the `e2e` marker.** The default run stays hermetic: no Docker, no network. The e2e asserts the config parses with `@devcontainers/cli read-configuration` and then builds and checks `node`, `uv`, `git`, and the OS release inside the container.

## Risks / Trade-offs

- **`ubuntu:26.04` lacks the curated base-image tooling** (zsh setup, common editors' helper packages). `common-utils` restores the parts the container contract relies on: the non-root user, sudo, and locale. The container stays leaner than the blessed image by design.
- **Floating `lts` and `latest` versions make builds non-reproducible.** That is the requested behavior. A project that needs a pin can edit the generated file; the generator treats the generated file as owned by the project after the scaffold.
- **The devcontainers-extra uv feature is a third-party feature.** The official Astral installer script is the alternative, but it would need a `postCreateCommand`, runs late, and installs into the user home. The feature installs at build time, and its source repo is the standard community features hub. The e2e check catches a broken feature reference.
- **Feature tags can disappear upstream.** The tags are verified today and pinned to majors; a removed major breaks the build loudly, and the e2e surfaces it.
