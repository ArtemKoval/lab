## MODIFIED Requirements

### Requirement: Decisions
An approval SHALL carry the outcome the pack resolved for the attempt, as an
opaque payload. A decline or a referral SHALL carry no outcome. The decision
SHALL keep the reason and the section reference. The API SHALL refuse an
approval whose outcome the pack has not resolved on the attempt in flight.

#### Scenario: Record a decline
- **GIVEN** a case in progress
- **WHEN** the agent records a decline with a reason and a section reference
- **THEN** the case is decided, the decision carries no outcome, and the
  decision keeps the reason and the reference

#### Scenario: An approval needs a positive award
- **GIVEN** a case in progress whose outcome the pack has not resolved
- **WHEN** the agent records an approval
- **THEN** the API refuses the record with a validation error that names
  resolve_outcome

### Requirement: The award limit and sign-off
The pack's gate SHALL decide whether an approval waits for a worker sign-off,
under the limit in force. The API SHALL refuse to run the effect while the
case waits. A sign-off SHALL record the worker and the time and SHALL run the
held effect once. The case graph SHALL run the effect after the sign-off
resumes the case.

#### Scenario: An approval over the limit waits
- **GIVEN** the approval limit in the settings
- **WHEN** the agent records an approval whose outcome the pack's gate holds
- **THEN** the case waits for sign off and a request to run the effect is
  refused

#### Scenario: A worker signs off
- **GIVEN** a case waiting for sign off
- **WHEN** a worker signs off
- **THEN** the sign-off records the worker and the time, and the effect runs
  once

#### Scenario: A worker signs off and the agent pays
- **GIVEN** a case waiting for sign off
- **WHEN** a worker signs off and the agent runs
- **THEN** the case resumes, and the effect run is already on the case

## REMOVED Requirements

### Requirement: Payment
