## ADDED Requirements

### Requirement: The registry names the units a clean clone must have
The file `tools/project_setup/registry.json` SHALL name every unit a
clean clone must have, with its id, kind, purpose, probe commands,
install command, and requirement note. The probe commands are the
registry's `check` field. The units SHALL cover the owned tools, the
system tools, the venvs, and the Claude infra. A clean clone SHALL
get the units it lacks from the registry. A unit whose probe passes
on a prepared clone SHALL stay untouched.

#### Scenario: A prepared unit stays untouched
- **GIVEN** a unit whose probe passes
- **WHEN** the setup runs on a prepared clone
- **THEN** the setup leaves the unit untouched

#### Scenario: A missing unit installs after consent
- **GIVEN** a unit whose probe fails on the clone
- **WHEN** the setup interview collects the consent
- **THEN** the setup installs the unit from its install command

### Requirement: The registry carries the venv units
The registry SHALL carry one unit per gate tool venv, one unit for
the shared zai venv, one unit for the crm venv, and one unit for the
crm node modules. Each gate-tool venv unit SHALL install its
editable tool with its dev extras and `coverage`. The other venv
units SHALL carry their own install commands: the shared zai venv
installs from its requirements file, and the crm venv and node
modules units run their project install commands.

#### Scenario: The gate-tool venv installs editable with coverage
- **WHEN** a reader reads a gate-tool venv unit's install command
- **THEN** the command builds the venv and installs the tool
  editable with its dev extras and `coverage`

#### Scenario: The registry covers the venvs
- **WHEN** a reader counts the venv units in the registry
- **THEN** the registry carries one venv unit per gate tool, the
  shared zai venv, the crm venv, and the crm node modules

### Requirement: The setup interview keeps the operator attention small
The project-setup skill SHALL run the setup as one interview. The
skill SHALL run the probe first and give the probe report before any
question. The skill SHALL ask one question per message, with one
recommended answer and one sentence of reason each. The skill SHALL
collect every answer before it executes anything. When every probe
passes, the skill SHALL ask no question and SHALL give the probe
report alone.

#### Scenario: The probe precedes the questions
- **WHEN** the setup starts on a clone
- **THEN** the probe report lands before the interview questions

#### Scenario: One question lands per message
- **WHEN** the interview asks the operator something
- **THEN** the message carries one question, one recommended answer,
  and one sentence of reason

#### Scenario: A clean probe asks nothing
- **WHEN** every probe passes on the clone
- **THEN** the interview asks no question and the report stands alone

### Requirement: The plan and the secrets keep their places
The skill SHALL give one plan message. The skill SHALL put every
hands-on step with secrets in one operator message with exact
commands. The skill SHALL never ask for a secret in the chat.

#### Scenario: A secret never enters the chat
- **WHEN** a step needs a secret
- **THEN** the skill names the exact command in the operator message,
  and no question in the chat asks for the secret

### Requirement: The setup doctors follow the house contract
Each setup doctor SHALL examine read-only by default. Each setup
doctor SHALL accept `--install`, `--json` with an `ok` field,
`--repo-root`, and SHALL exit 0 on a clean probe and 2 on a finding.
The per-tool registry tests, for example
`tests/saturation_pass/test_setup_unit.py`, SHALL fail until the
doctor is registered.

#### Scenario: The doctor exits 2 on a finding
- **WHEN** a doctor runs read-only on a clone with a missing unit
- **THEN** the doctor exits 2 and names the finding

### Requirement: The doctor install refuses a blanket run
The `--install` flag SHALL refuse a run without `--units`. The
install SHALL run the install command of each absent named unit, and
SHALL re-run the unit's `check` commands as the readback. A failed
install or a failed readback SHALL classify the unit as
`install_failed`. The skill text carries the backup rule for the
operator, and no doctor code enforces a backup today.

#### Scenario: A blanket install refuses
- **WHEN** the doctor runs `--install` with no `--units`
- **THEN** the doctor refuses and names the requirement

#### Scenario: A failed readback classifies the unit
- **WHEN** the install command fails or the readback probe fails
- **THEN** the doctor classifies the unit as `install_failed`
