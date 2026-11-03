# gate-surface Specification

## Purpose
The surface dimension routes scenarios to their runners. The dspy-eval runner works in process. Browser journeys drive the fixture preview page, and visual baselines plus the VLM judge ensemble sit behind the e2e gate.

## Requirements

### Requirement: Surface tags route scenarios to runners
Every scenario SHALL carry a surface tag from the set dspy-eval, e2e-ui, e2e-visual, and agent-e2e. The bridge SHALL record the surface of each scenario in the manifest. The gate runner SHALL send each eval case to the runner of its surface. Gate 0 SHALL reject an unknown surface value.

#### Scenario: An unknown surface fails the lint
- **WHEN** the lint CLI runs on a scenario with the surface tag e2e-print
- **THEN** the command exits 2 and names the unknown value

#### Scenario: The runner follows the surface
- **WHEN** the gate runner reads a case with the surface dspy-eval
- **THEN** the runner sends the case to the in-process harness runner and not to the browser runner

### Requirement: The fixture preview page serves the e2e surface
The tool SHALL ship a fixture preview page served by a stdlib http server on a fixed port. The page content SHALL stay deterministic: fixed labels, fixed data rows, and no animation. The server SHALL start for the e2e runs only.

#### Scenario: The preview page serves deterministic content
- **WHEN** the server starts and a client fetches the page twice
- **THEN** both responses carry the same labels and the same row content

### Requirement: The e2e journeys follow the a11y-first rule
An e2e-ui journey SHALL assert semantic THENs against the accessibility tree. A journey SHALL use pixels only for a claim about layout, overlap, contrast, or rendering. The journeys SHALL run behind the `DSPY_GATE_E2E=1` gate with a seeded fixture and a fixed viewport.

#### Scenario: A semantic claim reads the a11y tree
- **WHEN** a journey asserts the triage result label
- **THEN** the journey reads the label from the accessibility tree and passes on the expected text

### Requirement: Visual baselines are governed artifacts
A visual baseline SHALL live under `openspec/specs/<capability>/visual/` and SHALL carry its scenario ID in its name or its metadata. CI SHALL fail when a visual scenario has no baseline and when a baseline has no scenario. A baseline update SHALL ride the change pull request that alters the rendered surface.

#### Scenario: A visual scenario without a baseline fails CI
- **WHEN** CI examines a manifest with a visual scenario and no baseline under the visual directory
- **THEN** the CI job exits non-zero and names the scenario

### Requirement: The VLM judge ensemble examines visual claims
The visual judge SHALL use the pinned vision role. The judge SHALL vote in an ensemble of 3 at temperature 0 and SHALL pass at a majority. A visual run SHALL require the `DSPY_GATE_E2E=1` gate and the `ZAI_API_KEY` variable.

#### Scenario: The ensemble passes on a majority
- **WHEN** the three judge votes hold two pass votes and one fail vote
- **THEN** the visual gate marks the scenario green
