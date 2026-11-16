## ADDED Requirements

### Requirement: The traced turn
The copilot SHALL trace each turn as one Langfuse trace. The trace
SHALL carry the conversation id as the session id, one trace name, and
the turn's model calls as its children. A trace that cannot reach the
server SHALL leave the turn unchanged.

#### Scenario: A turn traces in its conversation
- **GIVEN** a signed-in worker with a conversation, and the variables
  name the compose server
- **WHEN** the worker sends a message, and the copilot answers
- **THEN** the server holds one trace named `Copilot turn`, with the
  conversation id as its session id, and the turn's model calls as its
  children

#### Scenario: An unreachable server leaves the turn whole
- **GIVEN** the variables name an address that answers no request
- **WHEN** the worker sends a message
- **THEN** the copilot answers as it answers without tracing, and no
  model call fails
