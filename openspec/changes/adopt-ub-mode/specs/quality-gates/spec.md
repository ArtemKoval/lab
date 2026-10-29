# quality-gates Specification (Delta)

## ADDED Requirements

### Requirement: The repository vendors the three gate tools
The repository SHALL carry `tools/crapper`, `tools/dryer`, and `tools/mutator` as vendored upstream copies. Each copy SHALL keep the upstream layout with its 0BSD `LICENSE` file, its launcher, and its own test suite.

#### Scenario: The vendored layout resolves
- **WHEN** a reader lists `tools/crapper`, `tools/dryer`, and `tools/mutator`
- **THEN** each directory holds `LICENSE`, the launcher script, `src/`, and `tests/` in the upstream layout

#### Scenario: CI runs each vendored suite
- **WHEN** the test workflow runs on a pull request that changes gated Python
- **THEN** it runs each vendored suite with that unit venv interpreter from the vendored location

### Requirement: The vendored copies record provenance
Each vendored README SHALL name the upstream URL and the pinned commit. The `tools/mutator` copy SHALL read its function names from the sibling `tools/crapper`.

#### Scenario: The pins match upstream
- **WHEN** a reader compares the README pins with the upstream repositories
- **THEN** crapper pins `6fd92c4c9bcc56efb64a2f8743d5a2993bcfd42d`, dryer pins `66ff6d21a42c04afcad89c78a80066176d1294b0`, and mutator pins `a5a0cb803b66e0cdb8bf471b3b08af701d424a41`

### Requirement: The crapper gate holds CRAP at 10 or less for changed Python
The crapper gate command SHALL run as `tools/crapper/crapper --threshold 10` with explicit paths or with `--changed`. The command SHALL exit 0 when the worst CRAP score is 10 or less. It SHALL exit 2 when the worst score exceeds 10. A score of exactly 10 passes.

#### Scenario: A conforming fixture passes
- **WHEN** the gate command runs with `--threshold 10` on a fixture whose worst CRAP score is below 10
- **THEN** the command exits 0

#### Scenario: A score above the threshold fails the gate
- **WHEN** the gate command runs with `--threshold 10` on a fixture whose worst CRAP score exceeds 10
- **THEN** the command exits 2 and names the threshold breach

#### Scenario: The boundary score passes
- **WHEN** the gate command runs with `--threshold 10` on a fixture whose worst CRAP score is exactly 10
- **THEN** the command exits 0

### Requirement: The dryer gate holds duplication at or below 0.8
The dryer gate command SHALL run as `tools/dryer/dryer --threshold 0.8 --fail-above` with explicit paths or with `--changed`. The vendored copy adds `--fail-above` to the upstream tool. The tool reports a pair when the pair score is at or above the threshold. The command SHALL exit 0 when no pair is reported. It SHALL exit 2 when a pair at or above 0.8 is reported. The owned tests in `tools/dryer/tests/test_fail_above.py` pin the flag.

#### Scenario: A conforming fixture passes
- **WHEN** the gate command runs with `--threshold 0.8 --fail-above` on a fixture with no pair at or above 0.8
- **THEN** the command exits 0

#### Scenario: A duplicate pair fails the gate
- **WHEN** the gate command runs with `--threshold 0.8 --fail-above` on a fixture with a pair that scores 1.0
- **THEN** the command exits 2 and names the pair

### Requirement: The mutator gate kills the mutants of changed Python
The mutator gate command SHALL run as `tools/mutator/mutator` with explicit paths or with `--changed`. The command SHALL exit 0 when every executed mutant dies. It SHALL exit 3 when a mutant survives. It SHALL exit 2 when the baseline tests fail.

#### Scenario: A killed mutant set passes
- **WHEN** the gate command runs on a fixture whose mutants all die under its test command
- **THEN** the command exits 0

#### Scenario: A surviving mutant fails the gate
- **WHEN** the gate command runs on a fixture with a mutant that survives its test command
- **THEN** the command exits 3 and names the survivor

### Requirement: The registry installs the three gate tools
`tools/project_setup/registry.json` SHALL carry one unit per tool with `kind: dependency-file`. Each install command SHALL build the unit venv and SHALL install the tool editable with its dev extras, plus `coverage`. Each check command SHALL run through the unit venv interpreter.

#### Scenario: The check passes after the install
- **WHEN** the project-setup skill runs the install command of a gate unit and then its check command
- **THEN** the check command exits 0

#### Scenario: The check fails on a clone without the venvs
- **WHEN** the project-setup skill runs the check command of a gate unit on a clone with no unit venv
- **THEN** the check command exits with a code other than 0

### Requirement: CI runs the vendored suites and the gates on pull requests
The test workflow SHALL build the three unit venvs and SHALL run the three vendored suites. The workflow SHALL run the three gates on every pull request whose paths pass the filter.

#### Scenario: A pull request that touches gated Python runs the gates
- **WHEN** a pull request changes a file under `tools/plan_exec` and the test workflow runs
- **THEN** the workflow runs the crapper, dryer, and mutator steps on the changed gated paths

#### Scenario: A pull request outside the gate scope skips the gates
- **WHEN** a pull request changes only files under `fde/`
- **THEN** the workflow filter skips the test workflow and no gate runs

### Requirement: The CI gate derives its paths from the pull request diff
The gate step SHALL fetch the pull request base and SHALL derive the changed gated paths from the diff. The step SHALL pass the paths to the tools as explicit arguments. The gate scope SHALL be the repository-owned Python minus the vendored trees and the fixtures. The crapper and dryer gates SHALL use the LCOV form of the workflow coverage run. The mutator gate SHALL cover changed product paths only.

#### Scenario: A clean CI checkout still gates the changed files
- **WHEN** the gate step runs in CI, where the working tree is clean
- **THEN** the tools receive the changed paths as explicit arguments and no step uses `--changed`

#### Scenario: The coverage input is the workflow coverage run
- **WHEN** the crapper and dryer gate steps run on a pull request
- **THEN** they read the LCOV conversion of the coverage report the workflow pytest run produced

### Requirement: The mutator CI step carries a runtime budget
The mutator step SHALL cap its workers and SHALL carry a timeout as its budget. The gate venvs SHALL carry `pytest` and `coverage` from the install step, so no gate run installs tooling on demand. The workflow contract test SHALL state the mutation policy after this change.

#### Scenario: The contract test states the new policy
- **WHEN** a reader opens the workflow contract test after this change
- **THEN** its docstring states that CI runs the mutator gate on changed gated paths

### Requirement: The e2e smoke exercises the three launchers
An opt-in e2e test at `tests/quality_gates/` SHALL run the three launchers against a fixture tree when `UB_TOOLS_E2E=1` and the unit venvs exist. It SHALL assert exit 0 on a conforming fixture, exit 2 above each threshold, and exit 3 for a surviving mutant. It SHALL skip when the variable is unset or a venv is absent. The pytest marker docstring SHALL name `UB_TOOLS_E2E`.

#### Scenario: The smoke runs with the gate variable set
- **WHEN** the e2e test runs with `UB_TOOLS_E2E=1` and all three unit venvs present
- **THEN** it asserts the exit codes of the three launchers on the fixture tree

#### Scenario: The smoke skips without the gate variable
- **WHEN** the e2e test runs without `UB_TOOLS_E2E`
- **THEN** the test skips and no launcher runs
