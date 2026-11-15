## MODIFIED Requirements

### Requirement: The scan classifies each open issue into one loop state
The scan SHALL map each open issue to one loop state and one
action. The admission SHALL run before the label precedence. The
label precedence SHALL order `handover`, `blocked`, `answered`,
`human-approved`, `waiting-human-approval`, the tech-debt rule, and
no label. A `tech-debt:` title or label SHALL skip the issue. The
scan order SHALL follow `createdAt` from oldest to newest.

#### Scenario: A foreign author refuses
- **GIVEN** issue 30 carries the login `stranger` and the allowed list carries `ArtemKoval`
- **WHEN** the scan classifies issue 30
- **THEN** the state is refused and the action is none

#### Scenario: A foreign handover label refuses
- **GIVEN** issue 31 carries the login `stranger` and the `handover` label
- **WHEN** the scan classifies issue 31
- **THEN** the state is refused

#### Scenario: A foreign blocked label refuses
- **GIVEN** issue 32 carries the login `stranger` and the `blocked` label
- **WHEN** the scan classifies issue 32
- **THEN** the state is refused

#### Scenario: An allowed author keeps the blocked state
- **GIVEN** issue 33 carries the login `ArtemKoval` and the `blocked` label
- **WHEN** the scan classifies issue 33
- **THEN** the state is blocked

#### Scenario: A listed bot login refuses
- **GIVEN** the allowed list names `helper[bot]` and issue 34 carries that login
- **WHEN** the scan classifies issue 34
- **THEN** the state is refused

#### Scenario: The login comparison ignores letter case
- **GIVEN** the allowed list carries `artemkoval` and issue 35 carries the login `ArtemKoval`
- **WHEN** the scan classifies issue 35
- **THEN** the state is not refused from the letter case

#### Scenario: A missing author refuses
- **GIVEN** issue 36 carries no author object in the fetch payload
- **WHEN** the scan classifies issue 36
- **THEN** the state is refused

#### Scenario: A handover label wins
- **GIVEN** issue 12 carries the `handover` label and the `human-approved` label
- **WHEN** the scan classifies issue 12
- **THEN** the state is skip

#### Scenario: An answered label wins
- **GIVEN** issue 13 carries the `answered` label and the `human-approved` label
- **WHEN** the scan classifies issue 13
- **THEN** the state is answered

#### Scenario: A gate label waits
- **WHEN** the scan classifies issue 14 with the `waiting-human-approval` label
- **THEN** the state is wait-approval

#### Scenario: A plain issue proposes
- **WHEN** the scan classifies issue 15 with no gate label
- **THEN** the state is propose

#### Scenario: A tech-debt title skips
- **GIVEN** issue 40 carries the login `ArtemKoval` and the title `tech-debt: prototype x`
- **WHEN** the scan classifies issue 40
- **THEN** the state is skip and the action is none

#### Scenario: A tech-debt label skips
- **GIVEN** issue 41 carries the login `ArtemKoval` and the `tech-debt` label
- **WHEN** the scan classifies issue 41
- **THEN** the state is skip and the action is none

#### Scenario: The tech-debt rule sits below the gate labels
- **GIVEN** issue 42 carries the login `ArtemKoval`, the title `tech-debt: prototype x`, and the `human-approved` label
- **WHEN** the scan classifies issue 42
- **THEN** the state is apply

#### Scenario: The order is oldest first
- **GIVEN** issues 15 and 9 both classify as propose
- **WHEN** the loop runs
- **THEN** the loop processes issue 9 before issue 15

### Requirement: The scan CLI reports the queue
The `scan` subcommand SHALL print one line per open issue with its
number, its state, and its pull request links. The `--json` flag
SHALL print the same data as JSON, and each entry SHALL carry the
author login. The CLI SHALL exit 0 on success. The CLI SHALL exit 2
on an operational failure: a failed `gh` call, an unreadable state
directory, a fresh foreign lock, or a missing, unparsable, or
wrong-shape authors config. A usage error SHALL exit 64.

#### Scenario: A scan prints the queue
- **WHEN** the scan runs with `--json`
- **THEN** the output is a JSON array
- **AND** each entry carries the issue number, the state, the author login, and the pull request links

#### Scenario: A broken gh fails the run
- **GIVEN** the `gh` call fails
- **WHEN** the scan runs
- **THEN** the exit code is 2
- **AND** stderr names the failure

#### Scenario: A broken authors config fails the run
- **GIVEN** the authors config does not parse
- **WHEN** the scan runs
- **THEN** the exit code is 2
- **AND** stderr names the config path
- **AND** stdout carries no queue

#### Scenario: A usage error exits 64
- **WHEN** the scan runs with an unknown flag
- **THEN** the exit code is 64
- **AND** stderr carries the parser message

#### Scenario: The lock gates the first fetch
- **GIVEN** a fresh foreign lock
- **WHEN** the scan runs
- **THEN** the refusal comes before the first `gh` call
- **AND** the authors-config read follows the lock examination

### Requirement: The status operator rows examine the loop
The `status` subcommand SHALL examine the loop components in a fixed
order. The first matched row SHALL decide the exit. The operator
rows run first: the halt file, the auth probe, the authors config,
the issue list, the blocked issues. The halt file SHALL sit at
`.claude/halt` in the working root or the primary checkout root. A
failed `gh auth token` probe SHALL decide the setup row. A missing,
unparsable, or wrong-shape authors config SHALL give the config row
exit 2 with the level `config`.

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

#### Scenario: A broken authors config reports a component error

- **GIVEN** the authors config does not parse
- **WHEN** the status runs
- **THEN** the exit code is 2 and the level is `config`

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

#### Scenario: A refused blocked issue stays out of the operator rows

- **GIVEN** an open issue carries the login `stranger` and the
  `blocked` label
- **WHEN** the status runs
- **THEN** the exit code is not 2 from that issue

#### Scenario: A handover label outranks a blocked label in status

- **GIVEN** an open issue carries the `handover` label and the
  `blocked` label
- **WHEN** the status runs
- **THEN** the exit code is not 2 from that issue
