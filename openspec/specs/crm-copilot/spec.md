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
