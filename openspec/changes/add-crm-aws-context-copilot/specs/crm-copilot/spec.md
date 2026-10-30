## ADDED Requirements

### Requirement: The worker chat
The copilot SHALL answer a signed-in worker in a chat, with its own graph and tools over the same backend API, and the worker's own token on every call. A case sign-off through the chat SHALL wait for the worker's confirmation before it fires.

#### Scenario: The copilot answers with its tools
- **GIVEN** a signed-in worker and a question about the queue
- **WHEN** the worker sends the message
- **THEN** the answer carries the tool steps that read the records

#### Scenario: A sign-off waits for confirmation
- **GIVEN** the copilot proposing a case sign-off
- **WHEN** the worker has not confirmed
- **THEN** no sign-off fires

### Requirement: Conversation records
Each conversation SHALL keep its turns in the database with their steps, their state, and their cost. A turn SHALL move through waiting, working, and answered, and a failed turn SHALL name its error.

#### Scenario: A turn keeps its steps
- **GIVEN** a copilot answer that used tools
- **WHEN** the worker reopens the conversation
- **THEN** the turn shows its steps and its cost
