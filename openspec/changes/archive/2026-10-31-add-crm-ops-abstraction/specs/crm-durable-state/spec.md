## MODIFIED Requirements

### Requirement: The deterministic award engine
The pack SHALL resolve an outcome through its protocol module as a pure
Python call. The backend SHALL keep one outcome payload per case and outcome
kind for the attempt in flight, and an approval SHALL carry that payload.

#### Scenario: The rules work an award without a model
- **GIVEN** a case with its lines and the pack plans
- **WHEN** the engine calls the pack's resolve verb
- **THEN** the resolve returns the outcome payload with no model call

#### Scenario: An approval must match its calculation
- **GIVEN** an outcome the pack resolved on the case's current attempt
- **WHEN** the agent records the approval
- **THEN** the decision carries that payload, and the engine never reads
  inside it
