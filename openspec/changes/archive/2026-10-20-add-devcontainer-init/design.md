# Design

## Context

The repo holds standalone tools under `tools/<task_name>/` with mirrored tests under `tests/<task_name>/`. The `zai_routing_audit` tool defines the house rig. The rig holds a stdlib package, a dual-path test conftest, a mutmut config in the tool directory, and gates that run with the root venv at `tools/zai_routing_audit/.venv/bin/python`. See proposal.md for the motivation.

Facts from reality checks on 2026-10-20:

- The latest Ubuntu LTS is 26.04. The blessed image `mcr.microsoft.com/devcontainers/base` publishes tags only up to `ubuntu-24.04`.
- `ubuntu:26.04` exists on Docker Hub.
- Feature manifests and ghcr tags, examined on the same day: `devcontainers/features/node` (2.x line, default version `lts`), `devcontainers/features/common-utils` (2.x line), `devcontainers/features/git` (1.x line, options `latest`, `system`, `os-provided`), `devcontainers-extra/features/uv` (1.x line, default version `latest`).

## Goals / Non-Goals

Goals:

- One command that turns an existing project directory into a VS Code devcontainer project.
- The generated container builds fast: image plus features, no Dockerfile, no source builds.
- The generator is standard-library only, hermetically testable, and follows the house CLI contract (`--json`, exit 0 and 2).

Non-Goals:

- No Python interpreter in the image. `uv` fetches interpreters on demand, and users run `uv python install`.
- No containers.dev template publication. The tool scaffolds locally.
- No MCP server. The CLI through Bash is the full surface, because file scaffolding has no stateful capability worth a server.
- No project-setup registry unit. The tool installs nothing. The e2e tools, Docker and `@devcontainers/cli`, are user-run and already present on the machines that run them.

## Decisions

- **Base image `ubuntu:26.04` plus the `common-utils` feature, not `devcontainers/base:ubuntu-24.04`.** The requirement names the latest LTS Ubuntu. The blessed base image lags at 24.04. The config therefore assembles the standard equivalent: the plain `ubuntu:26.04` image with `common-utils:2` for the `vscode` user and sudo. `remoteUser` is `vscode` because a plain image defaults to root. The alternative, a pin to the blessed image, fails the requirement today and drifts instead of LTS tracking.
- **`git:1` with `version: os-provided`, not `latest` from source.** A plain Ubuntu image has no git. The `os-provided` option installs through apt in seconds. The `latest` option compiles git from source and slows every build. The requirement asks for git in the config, not the newest git.
- **`node:2` with `version: lts` and `uv:1` with `version: latest`.** Both versions float, so each build takes the current LTS or stable release. This matches the requirement directly. The feature majors have pins to tags that exist today. The patch lines stay floating.
- **The OS default lives in one constant (`DEFAULT_UBUNTU_LTS = "26.04"`).** A future LTS is a one-line change plus a test update. `--os` exists for projects that must stay on an older LTS.
- **The tool is a package (`devcontainer_init/` with `core.py`, `cli.py`, `__main__.py`), and tests mirror it in `tests/devcontainer_init/`.** This reuses the `zai_routing_audit` rig. The conftest imports the in-tree package under pytest and stops under mutmut. The mutmut run uses a flattened out-of-tree copy. A single-file script would fork the house rig. A root-level `pyproject.toml` would add repo-wide config for one tool.
- **The e2e module is opt-in through `DEVCONTAINER_INIT_E2E=1` and the `e2e` marker.** The default run stays hermetic: no Docker, no network. The e2e asserts that the config parses with `@devcontainers/cli read-configuration`. It then builds the container and examines `node`, `uv`, `git`, and the OS release inside it.

## Risks / Trade-offs

- **`ubuntu:26.04` lacks the curated base-image tooling** (zsh setup, common editors' helper packages). `common-utils` restores the parts the container contract relies on: the non-root user, sudo, and locale. The container stays leaner than the blessed image by design.
- **Floating `lts` and `latest` versions make builds non-reproducible.** That is the requested behavior. A project that wants a pin can edit the generated file. The generator treats the generated file as owned by the project after the scaffold.
- **The devcontainers-extra uv feature is a third-party feature.** The official Astral installer script is the alternative. The script runs late through a `postCreateCommand` and installs into the user home. The feature installs at build time, and its source repo is the standard community features hub. The e2e catches a broken feature reference.
- **Feature tags can disappear upstream.** The tags exist today and have major pins. A removed major breaks the build loudly. The e2e surfaces the break.
