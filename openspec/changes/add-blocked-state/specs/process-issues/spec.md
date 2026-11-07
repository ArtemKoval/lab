## ADDED Requirements

### Requirement: The blocked state
The scan SHALL map an open issue that carries the `blocked` label to the
state `blocked` and the action `blocked`. The label SHALL sit in the
precedence between `handover` and `answered`. The loop SHALL never retry a
blocked issue, and only the operator SHALL clear the label.

#### Scenario: A blocked issue reports the blocked state
- **GIVEN** an open issue that carries the `blocked` label and no other gate
  label
- **WHEN** the scan runs
- **THEN** the issue reports the state `blocked` and the action `blocked`

#### Scenario: A handover issue stays above a blocked label
- **GIVEN** an open issue that carries both the `handover` and the `blocked`
  labels
- **WHEN** the scan runs
- **THEN** the issue reports the state `skip`

#### Scenario: A blocked label outranks a stale answered label
- **GIVEN** an open issue that carries both the `blocked` and the `answered`
  labels
- **WHEN** the scan runs
- **THEN** the issue reports the state `blocked`
