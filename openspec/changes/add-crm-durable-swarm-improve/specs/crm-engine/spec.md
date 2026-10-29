## MODIFIED Requirements

### Requirement: The award limit and sign-off
An approval over the limit SHALL wait for a worker sign-off. The API SHALL refuse payment while the case waits. A sign-off SHALL record the worker and the time and SHALL NOT pay. The case graph SHALL pay after the sign-off resumes the case.

#### Scenario: An approval over the limit waits
- **GIVEN** the approval limit in the settings
- **WHEN** the agent records an approval with an award over the limit
- **THEN** the case waits for sign off and a payment request is refused

#### Scenario: A worker signs off
- **GIVEN** a case waiting for sign off
- **WHEN** a worker signs off
- **THEN** the sign-off records the worker and the time, and no payment happens

#### Scenario: A worker signs off and the agent pays
- **GIVEN** a case waiting for sign off
- **WHEN** a worker signs off and the agent runs
- **THEN** the case resumes, and the payment records the award

## ADDED Requirements

### Requirement: The case agent graph
The case agent SHALL be a hand-written graph with its own state, nodes, and edges. The graph SHALL keep every step recorded on the case, refusals returned to the model, and at most 30 model calls. The graph SHALL pay as a step for every approval and SHALL wait with an interrupt when the backend says the case needs a sign-off. The case agent SHALL have no pay tool.

#### Scenario: The graph keeps the middleware duties
- **GIVEN** a case agent working a case on the stub model
- **WHEN** the graph runs
- **THEN** each step lands on the case, a refusal returns to the model as text, and a thirtieth model call stops the case

#### Scenario: The graph waits with an interrupt
- **GIVEN** an approval over the limit
- **WHEN** the graph reaches the payment step
- **THEN** the graph stops at an interrupt with its state saved
