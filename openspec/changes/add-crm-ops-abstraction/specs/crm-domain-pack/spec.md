## MODIFIED Requirements

### Requirement: The manifest
The manifest SHALL name the pack and SHALL match its folder. The manifest
SHALL carry the settings that the engine serves, and SHALL declare the
domain's resolutions, outcomes, config, and effects, with engine_api 2. The
loader SHALL refuse a pack whose declarations are missing, bind an outcome to
an unknown verb, or name an effect on an undeclared outcome.

#### Scenario: Settings come from the manifest
- **GIVEN** a manifest with an award approval limit
- **WHEN** the engine serves the settings
- **THEN** the approval limit comes from the manifest

#### Scenario: The manifest names the pack
- **GIVEN** a manifest whose name differs from its folder
- **WHEN** the engine loads the pack
- **THEN** the loader refuses the pack with a named error

#### Scenario: An effect names no declared outcome
- **GIVEN** an effect whose outcome is not in the declared outcomes
- **WHEN** the engine loads the pack
- **THEN** the loader refuses the pack and names the effect
