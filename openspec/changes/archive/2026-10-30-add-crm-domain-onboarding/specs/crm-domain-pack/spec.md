## ADDED Requirements

### Requirement: The manifest and rules examinations
The validator SHALL examine that the manifest names its folder and carries every required key. It SHALL examine that the rules module answers the engine's contract signature.

#### Scenario: Every examination is named and runnable
- **GIVEN** the validator's help
- **WHEN** the user reads the examination list
- **THEN** each contract rule appears as one named examination

### Requirement: The document and seed examinations
The validator SHALL examine that each document carries front matter with a version and a source. It SHALL examine that every seed reference resolves inside the pack.

#### Scenario: A broken seed reference is named
- **GIVEN** a pack whose seed refers to a missing customer
- **WHEN** the validator runs
- **THEN** it names the file, the record, and the missing reference

### Requirement: The eval, instruction, and noun examinations
The validator SHALL examine that every eval decision names a case in the pack and a legal decision kind. It SHALL examine that the instructions name only tools the engine serves, and that no engine-facing file name carries a domain noun.

#### Scenario: An illegal eval decision is named
- **GIVEN** an eval decision with an unknown kind
- **WHEN** the validator runs
- **THEN** it names the eval file and the decision

### Requirement: A second domain proves the seam
The engine SHALL run a second domain pack through the same suite the insurance pack runs, so the seam's domain-genericity is regression-pinned.

#### Scenario: The helpdesk pack passes the engine's gates
- **GIVEN** the helpdesk pack onboarded by the skill
- **WHEN** the default suite runs with `CRM_DOMAIN=helpdesk`
- **THEN** the pack's tests pass and the noun guard holds
