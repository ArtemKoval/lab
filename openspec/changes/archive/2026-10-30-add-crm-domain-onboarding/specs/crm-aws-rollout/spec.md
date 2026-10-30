## ADDED Requirements

### Requirement: The rollout skill
The `crm-aws-rollout` skill SHALL roll the stack out to a real AWS account, and roll it back. The paths walk a checklist the skill carries, on the ADR 0008 variables. The skill SHALL examine the account's readiness first, and a failed step SHALL stop the rollout with the step named.

#### Scenario: The skill examines readiness before it deploys
- **GIVEN** an AWS account with credentials
- **WHEN** the user walks the skill's up path
- **THEN** the skill examines the account (region, permissions, the emulator-off state) before any deployment step

#### Scenario: A failed step stops the rollout
- **GIVEN** a rollout in progress
- **WHEN** a step fails
- **THEN** the skill stops, names the step, and carries the roll-down path

### Requirement: The roll-down path
The skill's down path SHALL remove the deployed stack in reverse order and print what remains for the account owner to delete by hand.

#### Scenario: Roll-down removes the stack
- **GIVEN** a rolled-out stack
- **WHEN** the user walks the skill's down path
- **THEN** the deployed pieces are removed and the manual remainder is printed
