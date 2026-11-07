## ADDED Requirements

### Requirement: The status operator rows examine the loop

The `status` subcommand SHALL examine the loop components in a fixed
order. The first matched row SHALL decide the exit. The operator rows
SHALL run first: the halt file, the auth probe, the issue list, the
blocked issues. The halt file SHALL sit at `.claude/halt` in the
working root or the primary checkout root. A failed `gh auth token`
probe SHALL decide the setup row. No token value SHALL reach the
output. The blocked detection SHALL reuse the scan classification.

#### Scenario: A halt file reports stopped

- **GIVEN** the `.claude/halt` file exists in the primary checkout root
  with `operator pause` on the first line
- **WHEN** the status runs
- **THEN** the exit code is 1 and the reason names `operator pause`
- **AND** no `gh` call runs

#### Scenario: A missing token reports setup

- **GIVEN** the `gh auth token` call exits non-zero
- **WHEN** the status runs
- **THEN** the exit code is 3
- **AND** no token value reaches the output

#### Scenario: A failed issue list reports a component error

- **GIVEN** the open-issue list call exits non-zero
- **WHEN** the status runs
- **THEN** the exit code is 2 and the reason names the failure

#### Scenario: A blocked issue reports a component error

- **GIVEN** an open issue carries the `blocked` label and no gate label
  above it
- **WHEN** the status runs
- **THEN** the exit code is 2
- **AND** the payload names the issue number and title

#### Scenario: A handover label outranks a blocked label in status

- **GIVEN** an open issue carries the `handover` label and the
  `blocked` label
- **WHEN** the status runs
- **THEN** the exit code is not 2 from that issue

### Requirement: The status lock rows follow the operator rows

The lock rows SHALL run after the operator rows, and status SHALL
reuse the lock verdict with no holder and no session anchor. A fresh
lock SHALL give exit 0. A stale lock SHALL give exit 1 with the stale
rule as the reason. No lock SHALL give exit 1 as idle. A lock record
that the process cannot read SHALL give exit 2 with the read error. A
record that fails to parse SHALL stay in the stale row. A blocked
issue SHALL outrank a fresh lock.

#### Scenario: A fresh lock reports running

- **GIVEN** the lock file records a live holder
- **WHEN** the status runs
- **THEN** the exit code is 0

#### Scenario: A stale lock reports restartable

- **GIVEN** the lock file records a process id that no longer runs
- **WHEN** the status runs
- **THEN** the exit code is 1 and the reason names the stale rule

#### Scenario: No lock reports restartable

- **GIVEN** no lock file exists
- **WHEN** the status runs
- **THEN** the exit code is 1

#### Scenario: An unreadable lock reports a component error

- **GIVEN** the lock file exists and the process cannot read it
- **WHEN** the status runs
- **THEN** the exit code is 2 and the reason names the read error

#### Scenario: A blocked issue outranks a fresh lock

- **GIVEN** a blocked issue and a lock file with a live holder
- **WHEN** the status runs
- **THEN** the exit code is 2

### Requirement: The status output carries the level and the code

Plain mode SHALL print nothing on exit 0 and one reason line on stderr
on every other exit. The `--json` flag SHALL print one object on
stdout on every exit, with the level, the code, the reason, the
blocked entries, and the lock summary. The blocked entries SHALL carry
the number and the title of each blocked issue, or null. The lock
summary SHALL carry the lock state, the holder, and the matched rule,
or null. A component the examination did not reach SHALL carry null.

#### Scenario: The json payload carries the level and the code

- **WHEN** the status runs with `--json`
- **THEN** the output is one JSON object
- **THEN** the object carries the level, the code, the reason, the
  blocked entries, and the lock summary

#### Scenario: The plain mode stays silent on running

- **GIVEN** a fresh lock and no blocked issue
- **WHEN** the status runs without `--json`
- **THEN** stdout and stderr carry nothing

### Requirement: The scheduled-run recipe order

The scheduled run SHALL follow the recipe order: status, the action,
the peak-hours-gate command, the acquire, the scan, the oldest
actionable issue, and the release. The recipe SHALL run one issue per
fire. The recipe SHALL honor the halt file as the intentional stop.

#### Scenario: The recipe order runs status before the peak command

- **WHEN** the scheduled-run recipe runs
- **THEN** the status call comes before the peak-hours-gate command
  and the acquire

#### Scenario: The halt level stops the run silently

- **GIVEN** the status reports exit 1 from the halt row
- **WHEN** the scheduled run starts
- **THEN** the run takes no lock and reports nothing

### Requirement: The scheduled-run actions

The recipe SHALL stop quietly on exit 0, stop silently on the halt
level, proceed on the stale and idle levels, stop and report on exit 3
and on the issue-list and lock rows, and proceed with a report on the
blocked row. The pipeline stop rules SHALL govern the issue work: a
fresh spec-carrying propose stops at the human spec gate, and the
other paths continue as the spec pins.

#### Scenario: A fresh spec-carrying propose stops at the gate

- **GIVEN** the oldest actionable issue is a fresh spec-carrying
  propose
- **WHEN** the scheduled run works it
- **THEN** the run stops at the human spec gate and releases the lock

#### Scenario: The blocked row proceeds and reports

- **GIVEN** the status reports exit 2 from the blocked row
- **WHEN** the scheduled run works the oldest actionable issue
- **THEN** the run proceeds, and the result names the blocked issues
