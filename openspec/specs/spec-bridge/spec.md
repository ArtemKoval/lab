# spec-bridge Specification

## Purpose
The bridge compiles governed OpenSpec change scenarios into the eval manifest, per-scenario datasets, compiled tier assertions, and the generated Tier-A conformance tests. The bridge is the one writer of GENERATED paths, so a spec diff shows the behavioral delta.

## Requirements

### Requirement: The bridge compiles change scenarios into eval artifacts
The bridge CLI SHALL read one `openspec/changes/<id>/` directory. The bridge SHALL emit the eval manifest at `openspec/eval_manifest.json`. It SHALL emit one dataset file per scenario of a registry capability and one generated conformance module under `tests/dspy_gate/generated/`. Every emitted file SHALL start with a GENERATED header that names the producing command.

#### Scenario: A change compiles end to end
- **WHEN** the bridge regenerates a change whose scenarios all parse
- **THEN** the manifest lists every scenario with its capability, surface, gates, dataset path, and compiled assertions
- **AND** each dataset file exists and carries the GENERATED header
- **AND** the generated conformance module exists and carries the GENERATED header

#### Scenario: The compilation is deterministic
- **WHEN** the bridge regenerates the same change twice with no spec edit between the runs
- **THEN** every emitted file stays byte-identical between the runs

### Requirement: The bridge compiles THEN clauses by tier
The bridge SHALL compile every THEN clause into one assertion object. An equality, membership, or schema THEN SHALL become a Tier-A assertion. A tool-order THEN SHALL become a Tier-C assertion. A THEN with a judge tag and a rubric SHALL become a Tier-B reference. The bridge SHALL refuse a THEN that fits none of the three forms.

#### Scenario: A field equality compiles to tier A
- **WHEN** the bridge compiles the THEN clause severity = P0
- **THEN** the manifest records a Tier-A assertion for field severity with value P0

#### Scenario: A tool order compiles to tier C
- **WHEN** the bridge compiles a THEN about the escalate tool before the reply step
- **THEN** the manifest records a Tier-C assertion with the before tool and the after step

#### Scenario: A judged THEN compiles to a rubric reference
- **WHEN** the bridge compiles a THEN that carries a judge tag with a rubric path
- **THEN** the manifest records a Tier-B reference with that rubric path and an ensemble of 3

#### Scenario: An unparseable THEN stops the bridge
- **WHEN** the bridge compiles a scenario whose THEN fits no known form
- **THEN** the bridge exits 2 and names the scenario and the capability

### Requirement: The bridge routes each module as hand or optimized
The manifest SHALL carry an impl field with the value hand or optimized for every module. The impl value comes from the harness registry: a registry edit plus a regeneration routes a module, and no other edit routes it.

#### Scenario: A module routes to hand
- **WHEN** a reader opens the manifest for the pilot change
- **THEN** the triage module carries impl hand

### Requirement: GENERATED artifacts stay non-markdown under openspec
The bridge SHALL emit only JSON, JSONL, or Python files as GENERATED artifacts. The bridge SHALL NOT emit markdown under `openspec/`, so the STE scan never reads a generated file.

#### Scenario: The emitted artifact set holds no markdown
- **WHEN** the bridge regenerates a change
- **THEN** no emitted file under `openspec/` carries the .md suffix
