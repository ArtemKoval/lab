## ADDED Requirements

### Requirement: The pack protocol
Each pack SHALL ship a `protocol.py` with four verbs the core calls:
`resolve` (compute an outcome), `gate` (the hold predicate), `execute` (the
side effect), and `summarize` (the worker-facing line). The loader SHALL
validate the verbs at startup and refuse a pack that lacks them.

#### Scenario: The loader validates the protocol
- **GIVEN** a pack whose protocol lacks a verb
- **WHEN** the engine loads the pack
- **THEN** the loader refuses the pack and names the missing verb

### Requirement: Declared resolutions and outcomes
The manifest SHALL declare the resolution kinds and the outcome kinds of the
domain. The core SHALL store the resolution text and SHALL NOT parse the
outcome payload.

#### Scenario: The core stores what the pack resolves
- **GIVEN** a pack that declares its resolutions
- **WHEN** the agent records a decision
- **THEN** the decision record carries the resolution text and the opaque
  outcome payload

#### Scenario: The core never parses a payload
- **WHEN** the engine stores or serves an outcome
- **THEN** no core module reads inside the payload except through the pack's
  summarize and metric accessors

### Requirement: The gate hold is generic
The pack's `gate` verb SHALL decide whether an outcome is held. The core
SHOLD hold a gated outcome, answer the hold generically, and refuse the
effect until the hold is answered.

#### Scenario: A gated outcome waits
- **GIVEN** an outcome the pack's gate holds
- **WHEN** the case is read
- **THEN** the case carries the hold status the pack declared

### Requirement: One execution per effect
The core SHALL store one executed outcome per case and effect (unique), and
SHALL refuse a repeat.

#### Scenario: A repeated effect is refused
- **GIVEN** an effect already executed on a case
- **WHEN** the same effect is executed again
- **THEN** the API refuses with the recorded execution
