# crm-domain-pack Specification

## Purpose

A domain pack holds everything that belongs to one domain: its
manifest, its seed data, its policy documents, its instructions, and
its evals. The engine reads the active pack through one loader and
carries no domain nouns of its own. This spec pins the week one pack
contract for the insurance pack.

## Requirements

### Requirement: Pack discovery
The loader SHALL read the pack named by `CRM_DOMAIN` under `crm/domains/`. The loader SHALL fall back to the insurance pack when `CRM_DOMAIN` is not set.

#### Scenario: The variable names a pack
- **GIVEN** `CRM_DOMAIN` set to a pack name under `crm/domains/`
- **WHEN** the engine loads the pack
- **THEN** the engine reads the manifest, the documents, and the seed data of that pack

#### Scenario: The fallback pack
- **GIVEN** `CRM_DOMAIN` is not set
- **WHEN** the engine loads the pack
- **THEN** the engine uses the insurance pack

### Requirement: The manifest
The manifest SHALL name the pack and SHALL match its folder. The manifest SHALL carry the settings that the engine serves.

#### Scenario: Settings come from the manifest
- **GIVEN** a manifest with an award approval limit
- **WHEN** the engine serves the settings
- **THEN** the approval limit comes from the manifest

#### Scenario: The manifest names the pack
- **GIVEN** a manifest whose name differs from its folder
- **WHEN** the engine loads the pack
- **THEN** the loader refuses the pack with a named error

### Requirement: Seed from the pack
The seed command SHALL fill the database from the pack. The seed command SHALL refuse a pack with a required file absent and name the file. A seed over a seeded database SHALL rebuild the same queue.

#### Scenario: Seed fills the queue
- **GIVEN** a fresh database
- **WHEN** the user runs the seed command
- **THEN** the database holds the cases, customers, contracts, workers, and settings from the pack

#### Scenario: Seed names a missing file
- **GIVEN** a pack with a required file absent
- **WHEN** the user runs the seed command
- **THEN** the command fails and names the missing file

#### Scenario: A seed over a seeded database rebuilds the same queue
- **GIVEN** a seeded database
- **WHEN** the user runs the seed command again
- **THEN** the database holds the same queue as the first seed built

### Requirement: Documents in the pack
The pack SHALL carry the policy documents. The API SHALL serve a section with its document title, its number, and its title.

#### Scenario: Sections carry titles
- **GIVEN** the documents of the pack
- **WHEN** the user asks for one section
- **THEN** the API returns the document title, the section number, and the section title

### Requirement: Instructions in the pack
The pack SHALL carry the agent instructions. The API SHALL serve the instructions text from the pack.

#### Scenario: The API serves pack instructions
- **GIVEN** the instructions of the pack
- **WHEN** a client asks the API for the instructions
- **THEN** the API returns the instructions text from the pack

### Requirement: Evals stay out of the queue
The pack SHALL carry the held-out decision sets for later changes. The seed and the document routes SHALL return no eval content to the agents or the pages.

#### Scenario: The agents never see the evals
- **GIVEN** the eval files of the pack
- **WHEN** a client seeds the database or reads a document
- **THEN** no response carries eval content

### Requirement: The engine stays generic
Engine code SHALL carry no domain noun outside the packs. A root-suite guard test SHALL fail on a banned domain noun in engine code.

#### Scenario: The guard test bans domain nouns
- **GIVEN** the engine source tree
- **WHEN** the root suite runs the guard test
- **THEN** the test fails on a banned domain noun outside the packs
