# spec-gates Specification

## Purpose
The six spec gates prove mechanically that code matches the scenarios from proposal to production. They cover lint, manifest coverage, optimize and certify, conformance suites, archive freeze, and pin re-certification. Every failure routes to one named action.

## Requirements

### Requirement: Gate 0 rejects a scenario that cannot prove itself
The lint CLI SHALL run on one change before its pull request. The command SHALL reject a requirement with no scenario. In a registry capability, the command SHALL reject a THEN that parses to no assertion and carries no judge tag with a rubric. The same rule rejects a scenario with no surface tag. Scenarios of capabilities outside the registry stay with the ordinary suite. The command SHALL exit 0 on a clean change and 2 on any violation.

#### Scenario: A clean change passes the lint
- **WHEN** the lint CLI runs on the pilot change
- **THEN** the command exits 0

#### Scenario: A missing surface tag fails the lint
- **WHEN** the lint CLI runs on a registry capability scenario without a surface tag
- **THEN** the command exits 2 and names that scenario

### Requirement: Gate 0 rejects dangling governance
The lint CLI SHALL pass `openspec validate --strict` on the change. The command SHALL reject a judge tag whose rubric file does not exist. The command SHALL reject a `gates.yaml` threshold outside the policy bounds of the effective policy file.

#### Scenario: A dangling rubric fails the lint
- **WHEN** the lint CLI runs on a change whose judge tag names no existing file
- **THEN** the command exits 2 and names the rubric path

#### Scenario: A threshold outside the bounds fails the lint
- **WHEN** the lint CLI runs on a change whose `gates.yaml` holds a tier_b_min below the policy floor
- **THEN** the command exits 2 and names the threshold

### Requirement: Gate 1 proves bidirectional manifest coverage
The manifest verifier SHALL pass only when every scenario in the change has one eval case, and every eval case cites one scenario that exists. The command SHALL exit 0 at full coverage and 2 otherwise.

#### Scenario: Full coverage passes
- **WHEN** the verifier runs on a manifest that holds one eval case per scenario and no extra case
- **THEN** the command exits 0

#### Scenario: An extra eval case fails
- **WHEN** the verifier runs on a manifest whose eval case cites no scenario in the change
- **THEN** the command exits 2 and names the case

### Requirement: Gate 2 certifies on held-out scenarios before it writes artifacts
The optimize runner SHALL split the scenarios of a module into a train set, a validation set, and a held-out set from `holdout_ratio`. The runner SHALL certify the candidate on the held-out set after optimization. The runner SHALL write artifacts only after a green certification with Tier A at 1.0. The runner SHALL bound the loops with `max_optimize_loops`. A live run SHALL require the `ZAI_API_KEY` variable.

#### Scenario: A green candidate writes artifacts
- **WHEN** the runner certifies a candidate with Tier A at 1.0 on the held-out set
- **THEN** the runner writes the artifacts under `tools/dspy_gate/artifacts/<change-id>/`

#### Scenario: A red candidate writes nothing
- **WHEN** the runner certifies a candidate with a Tier-A miss on the held-out set
- **THEN** the runner writes no artifact and exits 2

### Requirement: Gate 3 runs the conformance suites
The root suite SHALL run the generated Tier-A conformance tests with no network and no model call. The gate runner SHALL run the delta suite and the frozen suite on a pull request. A conformance failure SHALL name the scenario it violates.

#### Scenario: The root suite runs tier A hermetically
- **WHEN** the root suite runs with no network
- **THEN** every generated Tier-A conformance test passes

#### Scenario: A conformance failure names the scenario
- **WHEN** the gate runner meets a failing assertion for one scenario
- **THEN** the report names that scenario ID and the failing tier

### Requirement: Gate 4 freezes the suites and baselines at archive
The freeze step SHALL copy the eval cases and the visual baselines of the change into `openspec/specs/<capability>/evals/` and `openspec/specs/<capability>/visual/` at archive time. The archive flow SHALL run the freeze step, so the frozen suite survives the spec sync.

#### Scenario: The archive freezes the suite
- **WHEN** the freeze step runs for an archived capability
- **THEN** the frozen eval cases and baselines exist under `openspec/specs/<capability>/`

### Requirement: Gate 5 re-certifies on a model pin change
The CI SHALL compare the effective model pins of `gates.yaml` against the pins recorded at the last certification. The CI SHALL fail when a pin changed and no frozen-suite run recorded a green result after the change. The CI SHALL fail when a drift report falls below `alert_below`.

#### Scenario: A pin change without re-certification fails
- **WHEN** a pull request changes a model pin and carries no green frozen-suite record after the change
- **THEN** the CI job exits non-zero and names the changed pin

### Requirement: Gate failures route to one of four actions
Every gate failure SHALL route to re-optimize, fix the harness, change the spec, or repair the environment. The gate report SHALL print the route with every failure.

#### Scenario: A report carries the route
- **WHEN** the gate runner reports a failing scenario
- **THEN** the report names one of the four routes for that failure

### Requirement: The gate status is queryable through the CLI and the MCP tool
The CLI SHALL carry a status command that reports the gate state and the conformance matrix. An MCP wrapper SHALL expose the same state as a tool with no logic of its own. The registration SHALL sit in `.mcp.json` and in the `enabledMcpjsonServers` and `permissions.allow` keys of `.claude/settings.json`.

#### Scenario: The CLI reports the gate state
- **WHEN** the status command runs after a gate run
- **THEN** the output names each gate with its state and carries the matrix rows

#### Scenario: The MCP wrapper mirrors the CLI
- **WHEN** a session calls the gate-status MCP tool
- **THEN** the tool returns the same state object as the CLI status command
