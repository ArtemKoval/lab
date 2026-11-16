# crm-copilot Specification

## Purpose

A worker's chat answers with its own graph and tools over the same API
under the worker's own token, waits for a confirmation before a sign-off,
and keeps its conversations, turns, and steps in the database.

## Requirements

### Requirement: The worker chat
The copilot SHALL answer a signed-in worker in a chat. Its own graph and tools go over the same backend API, and every call carries the worker's own token. A case sign-off through the chat SHALL wait for the worker's confirmation before it fires.

#### Scenario: The copilot answers with its tools
- **GIVEN** a signed-in worker and a question about the queue
- **WHEN** the worker sends the message
- **THEN** the answer carries the tool steps that read the records

#### Scenario: A sign-off waits for confirmation
- **GIVEN** the copilot proposing a case sign-off
- **WHEN** the worker has not confirmed
- **THEN** no sign-off fires

### Requirement: Conversation records
Each conversation SHALL keep its turns in the database, with their steps, their state, and their cost. A turn SHALL move through waiting, working, and answered, and a failed turn SHALL name its error.

#### Scenario: A turn keeps its steps
- **GIVEN** a copilot answer that used tools
- **WHEN** the worker reopens the conversation
- **THEN** the turn shows its steps and its cost

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
