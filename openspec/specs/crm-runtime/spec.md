# crm-runtime Specification

## Purpose

The agent runs as one app that answers at once and works in the
background, beats the backend while it works, is reached through its
service or a runtime on the same payloads, and hands a held case back to
a worker or takes it again with the worker's note.

## Requirements

### Requirement: The agent app
The agent SHALL run as one app with named operations. They work a run, carry a round, and resume a case. The app SHALL answer at once, work in the background, and report its busy state at the ping route.

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
The backend SHALL reach the agent through its service address by default. When `CRM_AGENT_RUNTIME` is set, it reaches the agent through the runtime, with the same payloads on both. The local emulator SHALL serve the runtime target in development.

#### Scenario: The runtime target serves a resume
- **GIVEN** `CRM_AGENT_RUNTIME` pointed at the local emulator
- **WHEN** a worker signs off
- **THEN** the resume reaches the agent through the runtime

### Requirement: Sign-off or send-back
A worker SHALL sign off a held case or send it back with a reason. A sent-back case SHALL keep the sent-back decisions. The agent SHALL resume it with the note. The award is refused until it decides again.

#### Scenario: A send-back resumes the case
- **GIVEN** a case waiting for sign off
- **WHEN** a worker sends it back with a reason
- **THEN** the case carries the sent-back decision and the agent resumes it with the note

#### Scenario: A resumed case pays only after a new decision
- **GIVEN** a case sent back and resumed
- **WHEN** the agent works it again
- **THEN** the payment waits for the new decision and the limit applies again

### Requirement: The tracing target per environment
The engine SHALL send its model-call traces to one Langfuse server in
each environment. The compose profile SHALL serve the local run and the
floci run at the loopback address. The AWS stack SHALL serve the
runtimes at its public address. The environment SHALL name the server
with `LANGFUSE_BASE_URL` and the project with `LANGFUSE_PUBLIC_KEY` and
`LANGFUSE_SECRET_KEY`. Missing variables SHALL keep the disabled
client, and the app SHALL work as it works without tracing.

#### Scenario: The local run traces to the compose server
- **GIVEN** the compose profile is up, and `crm/.env` carries the three
  variables for `http://localhost:3000`
- **WHEN** the agent works a case
- **THEN** the trace appears in the Langfuse web UI at
  `http://localhost:3000`

#### Scenario: The floci run traces beside the emulator
- **GIVEN** the compose profile and the emulator are up, and the
  variables name the compose server
- **WHEN** the agent works a case on the laptop route
- **THEN** the trace appears in the Langfuse web UI, and the emulator
  answers the runtime invoke with the canned acceptance as before

#### Scenario: Missing variables keep the app working
- **GIVEN** no `LANGFUSE_*` variable is set
- **WHEN** the agent works a case
- **THEN** the case decides as it decides without tracing, and no
  export leaves the process

### Requirement: The runtime trace variables
Both runtimes SHALL receive `LANGFUSE_BASE_URL`,
`LANGFUSE_PUBLIC_KEY`, and `LANGFUSE_SECRET_KEY` as environment
variables. The deploy values SHALL reach the runtimes through the
SETTINGS seam from `crm/agentcore/.env.local` or the deploy
environment. The agentcore deploy path SHALL stay the only deploy and
destroy path for the runtimes.

#### Scenario: The deploy gives both runtimes the variables
- **GIVEN** the three values in `crm/agentcore/.env.local`
- **WHEN** the operator deploys the runtimes
- **THEN** each runtime carries the three variables in its environment

#### Scenario: The Langfuse stack stays outside the agentcore path
- **GIVEN** the Langfuse stack is deployed
- **WHEN** the operator deploys or destroys the runtimes
- **THEN** the command touches no Langfuse resource, and the runtimes
  deploy or destroy as they did before

### Requirement: The Langfuse stack in AWS
The AWS deployment SHALL hold a Langfuse server stack as one CDK app
with its own app bin. The stack SHALL hold the web and worker services
and the Postgres, Redis, ClickHouse, and object storage the server
needs. The stack SHALL seed its first boot from the deploy values. The
stack SHALL come down in one destroy command.

#### Scenario: The stack serves the server at one address
- **GIVEN** the account and region targets, and the deploy values
- **WHEN** the operator deploys the stack
- **THEN** the Langfuse web UI answers at the stack output address

#### Scenario: The stack seeds its first boot
- **GIVEN** the operator gave the init values at deploy time
- **WHEN** the server boots for the first time
- **THEN** the organization, the project, the user, and the project
  keys exist as the values name them

#### Scenario: The stack comes down clean
- **GIVEN** the stack is deployed
- **WHEN** the operator destroys the stack
- **THEN** the account holds no resource that the stack made
