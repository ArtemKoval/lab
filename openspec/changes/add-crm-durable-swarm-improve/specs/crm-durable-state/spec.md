## ADDED Requirements

### Requirement: The deterministic award engine
The pack SHALL carry the deterministic award rules as a pure Python module. The backend SHALL keep one latest calculation per case per attempt, and an approval SHALL match its stored calculation.

#### Scenario: The rules work an award without a model
- **GIVEN** a case with claim lines and the pack plans
- **WHEN** the engine calls the pack rules
- **THEN** the rules return the award steps with no model call

#### Scenario: An approval must match its calculation
- **GIVEN** a stored calculation for a case attempt
- **WHEN** the agent records an approval whose award differs from it
- **THEN** the API refuses the record with a validation error

### Requirement: Checkpoints survive a restart
The harness SHALL save the case graph state after every step through a saver factory. The factory SHALL use SQLite when no database URL is set and Postgres when one is set. A stopped case SHALL carry on from its saved state without a new attempt.

#### Scenario: A stopped case carries on
- **GIVEN** a case in progress whose agent stopped partway
- **WHEN** the agent runs again
- **THEN** the case carries on from its saved state and its attempt count stays the same

#### Scenario: A failed case still starts afresh
- **GIVEN** a case whose work failed with an error
- **WHEN** the run retries it
- **THEN** the case starts from a clean state as a new attempt

### Requirement: Sign-off resumes the case
A sign-off SHALL record the worker and the time, and the agent SHALL pick the case back up and pay it. A sign-off SHALL reach the agent only after it is saved, and the sign-off SHALL stand if the agent cannot be reached.

#### Scenario: A sign-off wakes the waiting case
- **GIVEN** a case waiting for sign off with saved state
- **WHEN** a worker signs off
- **THEN** the case moves to in progress and the agent pays it from where it stopped

#### Scenario: The sign-off stands when the agent is away
- **GIVEN** the agent service is not running
- **WHEN** a worker signs off
- **THEN** the sign-off is saved and the case resumes on the next run

### Requirement: Nothing happens twice
The backend SHALL treat a repeat of a recorded decision or payment as done and return the case. A different decision on a decided case SHALL still be refused.

#### Scenario: A repeated decision returns the case
- **GIVEN** a decided case
- **WHEN** the agent records the same decision again
- **THEN** the API returns the case with no change

#### Scenario: A different decision is refused
- **GIVEN** a decided case
- **WHEN** the agent records a different decision
- **THEN** the API refuses with a conflict

### Requirement: The agent service
The agent SHALL run as a small web service on port 8002. The backend SHALL call it after each sign-off. The command line entry SHALL still start runs.

#### Scenario: The service carries a case back up
- **GIVEN** the agent service running
- **WHEN** the backend posts a resumed case to it
- **THEN** the service works that case from its saved state
