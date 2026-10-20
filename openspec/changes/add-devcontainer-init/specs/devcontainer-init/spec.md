# Spec Delta

## Purpose

The `devcontainer-init` capability is the scaffold of a devcontainer configuration. One command writes a complete `devcontainer.json` into an existing project directory, with a latest-LTS Ubuntu base and the git, node, and uv features wired up for VS Code.

## ADDED Requirements

### Requirement: Scaffold into an existing directory

The tool SHALL write `.devcontainer/devcontainer.json` into the target directory. The tool SHALL create the `.devcontainer` directory when it does not exist. The tool SHALL exit with code 0 after it writes the file.

#### Scenario: Scaffold into an empty project

- **WHEN** the user runs the tool with a target directory that exists and holds no `.devcontainer` directory
- **THEN** the tool writes `devcontainer.json` under `<target>/.devcontainer/` and exits with code 0

#### Scenario: Reject a missing target

- **WHEN** the user runs the tool with a target path that does not exist
- **THEN** the tool writes nothing, prints an error to stderr, and exits with code 2

### Requirement: Default configuration content

The generated configuration SHALL use the `ubuntu:26.04` image by default. The configuration SHALL set `remoteUser` to `vscode`. The `customizations.vscode.extensions` list SHALL be empty by default. The `name` field SHALL carry the name of the target directory.

#### Scenario: Defaults on a fresh scaffold

- **WHEN** the user runs the tool with no flags except the target
- **THEN** the generated file names the `ubuntu:26.04` image, sets `remoteUser` to `vscode`, and holds an empty extensions list and the target directory name

### Requirement: Wired tool features

The `features` map SHALL reference `ghcr.io/devcontainers/features/common-utils:2`, `ghcr.io/devcontainers/features/git:1` with the `os-provided` version, `ghcr.io/devcontainers/features/node:2` with the `lts` version, and `ghcr.io/devcontainers-extra/features/uv:1` with the `latest` version.

#### Scenario: Feature set on a fresh scaffold

- **WHEN** the user runs the tool with no flags except the target
- **THEN** the `features` map holds the four features with their default versions

### Requirement: OS and extension overrides

The `--os` option SHALL replace the Ubuntu version in the image reference. The `--extension` option SHALL add one VS Code extension to the extensions list. The user can repeat `--extension`. The tool SHALL keep the extension order and SHALL remove duplicates.

#### Scenario: Custom OS and two extensions

- **WHEN** the user runs the tool with `--os 24.04`, `--extension a`, `--extension b`, and `--extension a`
- **THEN** the generated file names the `ubuntu:24.04` image and lists the extensions in the order `a`, `b`

### Requirement: Safe overwrite behavior

The tool SHALL refuse to overwrite an existing `devcontainer.json` when the user does not pass `--force`. On refusal, the tool SHALL leave the existing file unchanged, SHALL print an error to stderr, and SHALL exit with code 2. With `--force`, the tool SHALL overwrite the file and SHALL exit with code 0.

#### Scenario: Refuse without force

- **WHEN** the target holds a `.devcontainer/devcontainer.json` and the user runs the tool without `--force`
- **THEN** the existing file keeps its content, the tool prints an error to stderr, and exits with code 2

#### Scenario: Overwrite with force

- **WHEN** the target holds a `.devcontainer/devcontainer.json` and the user runs the tool with `--force`
- **THEN** the tool replaces the file content and exits with code 0

### Requirement: Machine-readable output

With `--json`, the tool SHALL print one JSON object to stdout. The object SHALL carry `ok` set to `true` on success and `false` on failure, the written path on success, and an error message on failure. The exit code SHALL stay 0 on success and 2 on failure. Without `--json`, the tool SHALL print a human-readable message.

#### Scenario: JSON success

- **WHEN** the user runs the tool with `--json` on a fresh target
- **THEN** the tool prints a JSON object with `ok` set to `true` and the path of the written file, and exits with code 0

#### Scenario: JSON failure

- **WHEN** the user runs the tool with `--json` and a missing target
- **THEN** the tool prints a JSON object with `ok` set to `false` and an error message, and exits with code 2

### Requirement: Built container carries the wired tools

When the environment gate `DEVCONTAINER_INIT_E2E=1` is set, the e2e suite SHALL build a container from the generated configuration and SHALL check the tools inside. The check SHALL assert that `node`, `uv`, and `git` run inside the container and that the OS release reports the pinned Ubuntu version. The default test run SHALL NOT build anything.

#### Scenario: Live build check

- **WHEN** the user runs the e2e suite with `DEVCONTAINER_INIT_E2E=1` and a running Docker daemon
- **THEN** the suite builds the container from a generated configuration and the in-container `node --version`, `uv --version`, and `git --version` commands succeed
