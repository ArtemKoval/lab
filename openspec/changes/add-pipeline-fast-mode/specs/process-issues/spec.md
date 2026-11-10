## MODIFIED Requirements

### Requirement: The scan classifies each open issue into one loop state
The `scan` subcommand SHALL list the open issues with their author, their labels, their titles, and their open pull requests. The CLI SHALL map each issue to one loop state from five inputs. The inputs are the author admission, the labels, the title, the pull request links, and the artifact presence. The admission SHALL run before the label precedence. An author outside the allowed-author list SHALL map to the state `refused` with the action `none`. A login whose lowercase form ends with `[bot]` SHALL refuse. An absent or null author SHALL refuse. The refusal sits above every label state. The label precedence SHALL be `handover`, then `blocked`, then `answered`, then `human-approved`, then `waiting-human-approval`, then the tech-debt rule, then no label. A title that starts with `tech-debt:` SHALL map to the state `skip` with the action `none` below the gate labels and before the pull-request branches. The `tech-debt` label SHALL map to the same skip. The allowed-author comparison SHALL ignore letter case. The scan order SHALL follow `createdAt` from oldest to newest.

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
