## ADDED Requirements

### Requirement: The vocabulary in the manifest
The manifest MAY carry a `vocabulary` object. The loader SHALL pass it to
the engine beside the declarations, SHALL refuse an unknown `award_format`
or an unknown row `format`, and SHALL accept a pack with no vocabulary
section.

#### Scenario: A pack carries its words
- **GIVEN** a manifest with a vocabulary section
- **WHEN** the loader loads the pack
- **THEN** the vocabulary travels with the declarations

#### Scenario: A pack without the section still loads
- **GIVEN** a manifest with no vocabulary section
- **WHEN** the loader loads the pack
- **THEN** the pack loads as before, with no vocabulary
