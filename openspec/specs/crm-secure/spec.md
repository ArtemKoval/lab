# crm-secure Specification

## Purpose

The agent's routes carry the agent's key, a screening step reads each
case before the case agent and refers the injected ones, and the backend
serves the same API from a Lambda-style handler.

## Requirements

### Requirement: The agent key gate
The agent's routes SHALL require the `CRM_AGENT_KEY` header to match the configured key. A request that carries both the key and a worker token SHALL be refused.

#### Scenario: A request with the key passes
- **GIVEN** the configured agent key
- **WHEN** the agent posts a start with the key header
- **THEN** the API accepts the request

#### Scenario: A request without the key is refused
- **GIVEN** no key header
- **WHEN** a client posts to an agent route
- **THEN** the API refuses with a named error

### Requirement: Screening
A screening step SHALL read the case before the case agent. It SHALL refuse instructions hidden in the case. A screened case SHALL be referred, never decided. The case agent SHALL not see the injected text.

#### Scenario: An injected case is referred
- **GIVEN** the pack's injection case in the queue
- **WHEN** the agent works it
- **THEN** the case is referred and the decision names the screening

#### Scenario: A clean case passes screening
- **GIVEN** a clean case
- **WHEN** the agent works it
- **THEN** the case reaches the case agent with its screening recorded

### Requirement: The Lambda-ready handler
The backend SHALL expose one handler for a Lambda-style runtime, and the same app SHALL serve HTTP locally with no code change.

#### Scenario: The handler serves the API
- **GIVEN** the backend app
- **WHEN** the handler answers an API call
- **THEN** the response matches the HTTP route's response
