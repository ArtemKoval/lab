## ADDED Requirements

### Requirement: The pack protocol
The pack SHALL ship `protocol.py` with the verbs `resolve`, `gate`,
`execute`, and `summarize`, beside the manifest and seed examinations the
validator already carries. The validator SHALL examine each verb's signature.

#### Scenario: The protocol answers the engine's calls
- **GIVEN** a pack with `protocol.py`
- **WHEN** the engine calls each verb with the engine's arguments
- **THEN** each verb answers without touching the core's routes
