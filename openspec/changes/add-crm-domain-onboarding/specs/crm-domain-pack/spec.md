## ADDED Requirements

### Requirement: The pack validation rules
The engine SHALL enforce, through the validator, the pack contract's checks: the manifest names its folder and carries every required key; the rules module answers the engine's contract signature; each document carries front matter with a version and a source; every seed reference resolves inside the pack; every eval decision names a case in the pack and a legal decision kind; the instructions name only tools the engine serves; and no engine-facing file name carries a domain noun.

#### Scenario: Every check is named and runnable
- **GIVEN** the validator's help
- **WHEN** the user reads the checks
- **THEN** each contract rule above appears as one named check

### Requirement: A second domain proves the seam
The engine SHALL run a second domain pack through the same suite the insurance pack runs, so the seam's domain-genericity is regression-pinned.

#### Scenario: The helpdesk pack passes the engine's gates
- **GIVEN** the helpdesk pack onboarded by the skill
- **WHEN** the default suite runs with `CRM_DOMAIN=helpdesk`
- **THEN** the pack's tests pass and the noun guard holds
