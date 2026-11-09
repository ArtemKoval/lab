## Purpose

The spec-mining capability audits the repository against the OpenSpec
specs. One opt-in, read-only run names the live units without capability
coverage, the archived deltas that drifted from the specs, and the merged
commit weight of each uncovered area.

## ADDED Requirements

### Requirement: The tree scan
The `spec_mining` CLI SHALL carry a read-only tree scan that matches each
repo surface unit against the capability names in `openspec/specs/`. The
match SHALL use the alias, project, and coverage data file in the package.
The unit set covers the tools, the hooks, the skills, and the projects. A
unit with no capability match SHALL report as uncovered.

#### Scenario: A tool with no capability reports as uncovered
- **GIVEN** the tree holds `tools/widget_maker` and no capability name or alias matches it
- **WHEN** the tree scan runs
- **THEN** the report names `widget_maker` as uncovered

#### Scenario: An alias keeps a unit off the uncovered list
- **GIVEN** the data file maps the unit `tools/spec_ste_check` to the capability `spec-ste-enforcement`
- **WHEN** the tree scan runs
- **THEN** `spec_ste_check` stays off the uncovered list

#### Scenario: A skill with no coverage entry reports as uncovered
- **GIVEN** `.claude/skills/` holds the skill `widget-guide` and the data file carries no entry for it
- **WHEN** the tree scan runs
- **THEN** the report names `widget-guide` as uncovered

### Requirement: The archive drift scan
The CLI SHALL examine the `specs/` delta of each archived change and
compare its scenarios with the scenarios in
`openspec/specs/<capability>/spec.md`. An archived scenario that the
capability spec does not hold SHALL report as drift. An archived change
with no `specs/` delta SHALL stay off the drift scan.

#### Scenario: A missing spec scenario reports as drift
- **GIVEN** the archive holds a change whose delta adds the scenario `Old run` to `old-cap`
- **AND** the spec of `old-cap` does not hold the scenario `Old run`
- **WHEN** the drift scan runs
- **THEN** the report names the scenario `Old run` as drift for `old-cap`

#### Scenario: A synced capability reports no drift
- **GIVEN** the spec of `old-cap` holds every scenario of the archived delta
- **WHEN** the drift scan runs
- **THEN** the report carries no drift entry for `old-cap`

#### Scenario: A change with no delta stays off the drift scan
- **GIVEN** the archive holds a change with no `specs/` directory
- **WHEN** the drift scan runs
- **THEN** that change produces no drift entry

### Requirement: The history ranking
The CLI SHALL count the merged commits that touch each uncovered area and
SHALL order the report by that count. An area with more merged commits
SHALL rank above an area with fewer merged commits.

#### Scenario: A busier area ranks higher
- **GIVEN** the area `tools/widget_maker` holds 10 merged commits
- **AND** the area `docs/widget_guide` holds 2 merged commits
- **AND** both areas report as uncovered
- **WHEN** the ranking runs
- **THEN** `widget_maker` ranks above `widget_guide`

### Requirement: The run output
A run SHALL write `coverage.json`, `report.md`, and one
`drafts/<candidate>/proposal.md` seed per uncovered capability under
`reports/spec_mining/<UTC-date>/`. The run SHALL create no file outside
`reports/spec_mining/`.

#### Scenario: A run writes the report set
- **GIVEN** the tree holds two uncovered units
- **WHEN** a run completes
- **THEN** the run directory holds `coverage.json`, `report.md`, and two seed directories

#### Scenario: The seeds stay out of the planning home
- **GIVEN** a run completed with seeds
- **WHEN** a reader lists `openspec/changes/`
- **THEN** the directory holds no seed entry from the run

### Requirement: The CLI contract
The CLI SHALL carry one `run` subcommand. The CLI SHALL accept a `--json`
flag and SHALL exit 0 on success and 2 on operational failure. A failure
SHALL put the reason on stderr and keep the stdout empty. The CLI
SHALL read the tree, the archive, and `git log` without a network call.

#### Scenario: The JSON output parses
- **WHEN** the CLI runs with `--json`
- **THEN** the output is one JSON object with the tree, the drift, and the ranking sections

#### Scenario: A failed read exits 2
- **GIVEN** the git read fails
- **WHEN** the CLI runs
- **THEN** the exit code is 2 and the reason is on stderr
