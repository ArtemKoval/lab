# halt-gate Specification

## Purpose
The halt-gate capability gives the operator a one-file stop control over
unattended agent work in this repository. While the `.claude/halt` file
exists at a session root or in the primary checkout behind a worktree, the
PreToolUse hook denies matched model-backed calls and names the reason from
the file's first line. The gate is a safety control: it is pure bash, so a
broken interpreter or venv cannot disarm it, and it fails closed once the
root resolves. The peak-hours gate stays separate, because that gate is an
availability control and fails open by design.

## Requirements

### Requirement: The deny
When a halt file exists at `.claude/halt` in the session root, or in the
primary checkout behind a worktree, the hook SHALL exit 2 for every matched
call. stderr SHALL name the file path and the resume instruction. The reason
is the first line read within the first 200 bytes of the file, with carriage
returns removed. A file whose first line carries no readable text, or whose
first bytes cannot be read, SHALL still deny, with a fallback reason.

#### Scenario: A halt file stops the call
- **GIVEN** the halt file exists in the session root with a first line of text
- **WHEN** a matched tool call arrives
- **THEN** the hook exits 2, and stderr names the path and the reason

#### Scenario: A primary halt stops a worktree call
- **GIVEN** the halt file exists in the primary checkout behind a worktree,
  and the worktree carries no halt file of its own
- **WHEN** a matched tool call arrives in the worktree session
- **THEN** the hook exits 2, and stderr names the primary path and the reason

#### Scenario: A first line with no readable text still stops the call
- **GIVEN** the halt file exists and its first line is whitespace only
- **WHEN** a matched tool call arrives
- **THEN** the hook exits 2 with the fallback reason

### Requirement: The allow paths
When no halt file exists in the session root or in the primary checkout, the
hook SHALL exit 0 with empty stderr. When the repository root cannot be
resolved, the hook SHALL exit 0, because the wiring always sets the project
directory and this path is a broken install.

#### Scenario: No halt file anywhere allows the call
- **GIVEN** no halt file in the session root or in the primary checkout
- **WHEN** a matched tool call arrives
- **THEN** the hook exits 0 with no output

#### Scenario: No resolvable root allows the call
- **GIVEN** no project directory and no derivable root
- **WHEN** a matched tool call arrives
- **THEN** the hook exits 0 with no output

### Requirement: The wiring and the state
The settings SHALL carry one further PreToolUse group with the peak-hours
matcher, placed after the peak-hours group, with a command that references
the project directory, a timeout of 10 or less, and a non-async entry. The
contract test SHALL pin the wiring, the group order, and the live paths. The
gitignore SHALL ignore the halt file path.

#### Scenario: The wiring carries the halt group after the peak group
- **WHEN** a reader opens the settings and the contract test
- **THEN** the halt group shares the peak-hours matcher, sits after the
  peak-hours group, and the test pins the entry fields and the live deny and
  allow paths

#### Scenario: The halt file is ignored by git
- **WHEN** the operator creates the halt file in a clean checkout
- **THEN** git status carries no entry for it
