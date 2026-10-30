## ADDED Requirements

### Requirement: The skill
The `crm-local-aws` skill SHALL run the crm app with the AWS wiring pointed at the local emulator. The steps start the emulator, set the wiring variables, start the app, verify the wiring, and tear it down. Every step SHALL name its command and its gate.

#### Scenario: The skill runs the app with the wiring live
- **GIVEN** Docker running and the floci image pulled
- **WHEN** the user walks the skill's steps
- **THEN** the app runs with `CRM_AGENT_RUNTIME` set, and the wiring verification passes through the emulator

### Requirement: The wiring gate
The `crm/deploy/verify_wiring.py` script SHALL invoke the emulated runtime through the backend's own runtime caller and assert the acceptance the backend reads. The script SHALL need no model key and SHALL make no call outside the emulator.

#### Scenario: The gate proves the runtime path
- **GIVEN** the emulator running with a runtime registered
- **WHEN** the user runs the wiring gate
- **THEN** the backend's runtime caller reports the acceptance, and the script exits 0

#### Scenario: The gate fails when the emulator is down
- **GIVEN** the emulator stopped
- **WHEN** the user runs the wiring gate
- **THEN** the script exits 2 and names the failed connection

### Requirement: Honest boundaries
The skill SHALL state what the emulator proves and what it does not. The runtime invoke path is proven against the emulator's canned acceptance. Agent behavior stays with the hermetic tests and the human's own reviews.

#### Scenario: The skill names the boundary
- **WHEN** the user reads the skill
- **THEN** it states that the emulator proves the wiring, not the behavior
