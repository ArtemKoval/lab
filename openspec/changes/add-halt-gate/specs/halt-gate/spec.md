## ADDED Requirements

### Requirement: The deny
When the halt file exists at `.claude/halt`, the hook SHALL exit 2 for every
matched call. stderr SHALL name the file path, the first line of the file cut
at 200 characters, and the resume instruction. A file that exists but carries
no readable first line SHALL still deny, with a fallback reason.

#### Scenario: A halt file stops the call
- **GIVEN** the halt file exists with a first line of text
- **WHEN** a matched tool call arrives
- **THEN** the hook exits 2, and stderr names the path and the reason

#### Scenario: An unreadable halt file still stops the call
- **GIVEN** the halt file exists with no readable first line
- **WHEN** a matched tool call arrives
- **THEN** the hook exits 2 with the fallback reason

### Requirement: The allow paths
When no halt file exists, the hook SHALL exit 0 with empty stderr. When the
repository root cannot be resolved, the hook SHALL exit 0, because the wiring
always sets the project directory and this path is a broken install.

#### Scenario: No halt file allows the call
- **GIVEN** no halt file at the resolved root
- **WHEN** a matched tool call arrives
- **THEN** the hook exits 0 with no output

#### Scenario: No resolvable root allows the call
- **GIVEN** no project directory and no derivable root
- **WHEN** a matched tool call arrives
- **THEN** the hook exits 0 with no output

### Requirement: The wiring and the state
The settings SHALL carry one PreToolUse group with the peak-hours matcher, a
command that references the project directory, a timeout of 10 or less, and a
non-async entry. The gitignore SHALL carry the halt file path. The contract
test SHALL pin the wiring and the live paths.

#### Scenario: The wiring matches the peak-hours group
- **WHEN** a reader opens the settings and the contract test
- **THEN** the group carries the same matcher as the peak-hours gate, and the
  test pins the entry fields and the live deny and allow paths

#### Scenario: The halt file is ignored by git
- **WHEN** the operator creates the halt file in a clean checkout
- **THEN** git status carries no entry for it
