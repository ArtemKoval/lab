## ADDED Requirements

### Requirement: The traced case work
The case agent and the improver SHALL export their model-call traces
to the Langfuse server. Each case thread SHALL trace in its own
session. The improver's round SHALL trace in the round's session. A
run SHALL tag the traces of the cases it works with the run id. A
trace that cannot reach the server SHALL leave the work unchanged.

#### Scenario: A case traces in its thread session
- **GIVEN** the variables name the compose server
- **WHEN** the agent works a case
- **THEN** the trace carries the case's `case_id:thread_id` session and
  the work's trace name

#### Scenario: The improver traces its round
- **GIVEN** the variables name the compose server
- **WHEN** the improver works a round
- **THEN** the improver's traces carry the round's session and the
  `Improver` trace name

#### Scenario: A run tags the cases it works
- **GIVEN** a run works the queue
- **WHEN** the run works a case
- **THEN** the case's trace carries the run id as a tag

#### Scenario: An unreachable server leaves the work whole
- **GIVEN** the variables name an address that answers no request
- **WHEN** the agent works a case
- **THEN** the case decides as it decides without tracing, and no model
  call fails
