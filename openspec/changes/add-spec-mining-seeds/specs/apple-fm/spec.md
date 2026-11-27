## ADDED Requirements

### Requirement: The build script drives the model through a step ledger
The script `apple/fm/simple_game/build.sh` SHALL run the build as
numbered steps, SHALL write no game logic itself, and SHALL drive the
model at `/usr/bin/fm` for every implementation, unit test, and
browser layer line. The script SHALL resume a run from its ledger.
The flags `--clean`, `--from N`, `--only N`, `--refreeze`,
`--list`, `--serve`, and `--help` SHALL behave as the usage text
states. The script SHALL hold bash 3.2 syntax only.

#### Scenario: A rerun resumes from the ledger
- **WHEN** the script runs again after an interrupted build
- **THEN** it resumes from the ledger instead of starting from the
  first step

#### Scenario: The script writes no game logic
- **WHEN** a reader examines the script's steps
- **THEN** the game code comes from the model outputs, and the script
  only assembles prompts, judges answers, and runs gates

### Requirement: The gates hold the generated code
The build SHALL gate every model answer before the next step accepts
it. A step that repairs SHALL retry up to `FM_RETRIES` attempts
(default 3) with an escalation ladder per attempt, and SHALL re-issue
the skeleton prompt after two failed repairs. The coverage gate SHALL
run with no repair. The mutation gate SHALL feed its uncovered lines
to the strengthen pass.

#### Scenario: A repair retries within the bound
- **GIVEN** a model answer whose unit fails its gate
- **WHEN** the step processes the answer
- **THEN** the step repairs up to `FM_RETRIES` attempts with the
  escalation ladder, and re-issues the skeleton after two failed
  repairs

#### Scenario: The coverage gate repairs nothing
- **WHEN** the coverage gate fails
- **THEN** the step reports the failure with no repair request

### Requirement: The frozen contracts pin the step shapes
The frozen contracts under `contracts/` SHALL pin the shapes that
steps exchange. The `--refreeze` flag SHALL accept the current
contracts as the frozen ones.

#### Scenario: The contracts refreeze
- **WHEN** the script runs with `--refreeze`
- **THEN** the current step contracts become the frozen contracts

### Requirement: The build never continues after a signal
The script SHALL trap the interrupt and terminate signals. On a
signal the script SHALL name the step that ran and SHALL stop the
build, and SHALL never continue to the next step.

#### Scenario: A signal stops the build
- **WHEN** the build receives an interrupt or a terminate signal
- **THEN** the script logs the current step and stops, and no further
  step runs

### Requirement: The build stays local
The build SHALL keep every model call local on the host. The build
SHALL need the network one time only for `npm install`. No prompt
SHALL leave the machine.

#### Scenario: The build runs offline after install
- **GIVEN** the `npm install` step completed once
- **WHEN** the build runs with the network down
- **THEN** every model call still runs local and the build proceeds
