## ADDED Requirements

### Requirement: The notebook tests stay hermetic
The tests at `tests/notebooks/` SHALL read each notebook as JSON and
SHALL run its code cells against stubbed course dependencies. The
tests SHALL import no course dependency, so the default pytest run
needs no network and no model key.

#### Scenario: The tests run hermetic
- **WHEN** the default pytest run executes `tests/notebooks/`
- **THEN** the notebook tests run with no network and no model key,
  against the stubs

### Requirement: The public checklist holds
A notebook that goes to a public course repo SHALL pass that repo's
checklist: cleared outputs on the source notebook, no secrets in any
cell, and no emojis. The emoji-free rule SHALL allow only the middle
dot and the em dash as non-ASCII characters.

#### Scenario: An emoji fails the checklist
- **WHEN** a notebook cell carries an emoji
- **THEN** the notebook test fails the notebook for the public repo

#### Scenario: The allowed non-ASCII set passes
- **WHEN** a notebook cell carries a middle dot or an em dash
- **THEN** the notebook test passes the notebook for the public repo
