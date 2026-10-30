## ADDED Requirements

### Requirement: The agent app
The agent SHALL run as one app with named operations for working a run, carrying a round, and resuming a case. The app SHALL answer at once, work in the background, and report its busy state at the ping route.

#### Scenario: The app answers at once
- **GIVEN** the agent app running
- **WHEN** a client posts a run
- **THEN** the app accepts at once and works in the background

#### Scenario: The ping reports the busy state
- **GIVEN** the agent working
- **WHEN** a client pings
- **THEN** the ping reports busy

### Requirement: The heartbeat
The agent SHALL beat the backend while it works. The backend SHALL read the beat as liveness for the runs and the rounds it shows.

#### Scenario: A working run beats
- **GIVEN** a run in progress
- **WHEN** the backend reads the run's liveness
- **THEN** the beat is fresh

### Requirement: Runtime invocation
The backend SHALL reach the agent through its service address by default, or through a runtime when `CRM_AGENT_RUNTIME` is set, with the same payloads on both. The local emulator SHALL serve the runtime target in development.

#### Scenario: The runtime target serves a resume
- **GIVEN** `CRM_AGENT_RUNTIME` pointed at the local emulator
- **WHEN** a worker signs off
- **THEN** the resume reaches the agent through the runtime

### Requirement: Sign-off or send-back
A worker SHALL sign off a held case or send it back with a reason. A sent-back case SHALL keep the sent-back decisions, and the agent SHALL resume it with the note, while the award is refused until it decides again.

#### Scenario: A send-back resumes the case
- **GIVEN** a case waiting for sign off
- **WHEN** a worker sends it back with a reason
- **THEN** the case carries the sent-back decision and the agent resumes it with the note

#### Scenario: A resumed case pays only after a new decision
- **GIVEN** a case sent back and resumed
- **WHEN** the agent works it again
- **THEN** the payment waits for the new decision and the limit applies again
