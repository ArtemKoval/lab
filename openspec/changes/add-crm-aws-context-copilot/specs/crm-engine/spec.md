## ADDED Requirements

### Requirement: Send-back on the case page
The case page SHALL carry a send-back form for a held case, and the case SHALL show its sent-back decisions with who sent them and why.

#### Scenario: The page shows the sent-back decisions
- **GIVEN** a case with a sent-back decision
- **WHEN** the user opens the case page
- **THEN** the page shows the decisions with the worker and the reason

### Requirement: Take a sent-back case
A worker SHALL take a sent-back case back into their own work, which stops the agent's work on it.

#### Scenario: A worker takes the case
- **GIVEN** a sent-back case in progress
- **WHEN** a worker takes it
- **THEN** the agent's work on the case stops and the case stays with the worker
