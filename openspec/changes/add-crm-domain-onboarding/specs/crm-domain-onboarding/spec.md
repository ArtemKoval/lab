## ADDED Requirements

### Requirement: The validator
The `crm/validate` command SHALL examine one pack and exit 0 when it is onboardable, or 2 with named findings. It SHALL examine: the manifest against its schema and folder name; the rules module against the engine's contract; each document's front matter and version; the seed files' referential integrity; each eval decision's legality; the instructions' tool names against the served tools; and the pack's engine-facing file names.

#### Scenario: A good pack validates clean
- **GIVEN** a pack with every required artifact correct
- **WHEN** the user runs the validator
- **THEN** the command exits 0 and prints the pack name

#### Scenario: A broken pack names its findings
- **GIVEN** a pack whose seed refers to a missing customer
- **WHEN** the user runs the validator
- **THEN** the command exits 2 and names the file, the record, and the missing reference

### Requirement: The smoke run
The `crm/smoke` command SHALL seed a temporary database from the pack, work three cases through the harness on the stub model, and print each decision with its award. The command SHALL make no network call and SHALL need no model key.

#### Scenario: A smoke run works three cases
- **GIVEN** a validated pack
- **WHEN** the user runs the smoke command
- **THEN** it prints three decisions worked on the stub model against a temporary database

#### Scenario: The smoke run never reaches the network
- **GIVEN** a machine with no model key
- **WHEN** the user runs the smoke command
- **THEN** the run completes with no network call

### Requirement: The onboarding skill
The `crm-onboard-domain` skill SHALL walk a free-form domain description through five steps: extract the domain model, generate the pack, validate, smoke, and review. The skill SHALL change no engine code, and the pack it lands SHALL pass the engine's gates.

#### Scenario: A description lands a working pack
- **GIVEN** a free-form description of a backoffice domain
- **WHEN** the user walks the skill
- **THEN** the new pack passes the validator, the smoke run, and the noun guard

#### Scenario: The skill changes no engine code
- **GIVEN** a skill run that landed a pack
- **WHEN** the diff is read
- **THEN** every changed file sits under `crm/domains/<name>/` or the run's own tests
