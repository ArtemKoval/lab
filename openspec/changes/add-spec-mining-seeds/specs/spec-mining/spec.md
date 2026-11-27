## ADDED Requirements

### Requirement: One run writes the dated report directory
One run SHALL write `reports/spec_mining/<UTC-date>/` with
`coverage.json`, `report.md`, and `drafts/<candidate>/proposal.md`,
one scaffold per uncovered candidate. Outside `drafts/`, a rerun
SHALL replace the files the run owns and SHALL leave any other file
in place. The `drafts/` tree is owned wholesale: a rerun removes it
and rewrites it. The tool SHALL stay read-only on the audited tree
and SHALL use the standard library only.

#### Scenario: A rerun keeps the foreign files outside drafts
- **GIVEN** a foreign file in the run directory outside `drafts/`
- **WHEN** the rerun completes
- **THEN** the rerun replaces the owned outputs and leaves the
  foreign file in place

#### Scenario: The drafts tree rewrites wholesale
- **WHEN** the rerun completes
- **THEN** the `drafts/` tree carries exactly this run's scaffolds

### Requirement: The tree scan names the uncovered units
The tree scan SHALL walk `tools/`, `.claude/hooks/`, `.claude/skills/`,
and the project directories. A unit is covered when its normalized
name matches a capability, when a `units.json` alias maps it to one,
or when its `units.json` coverage entry matches the capability set.
The scan SHALL name every unit the rule does not cover, and SHALL
report the stale `units.json` entries in the payload.

#### Scenario: An aliased unit counts as covered
- **WHEN** a unit's normalized name does not match a capability name
- **THEN** a `units.json` alias or coverage entry still counts the
  unit as covered

#### Scenario: A stale entry gets reported
- **WHEN** a `units.json` entry names no live unit
- **THEN** the payload carries the stale entry in its tree section

### Requirement: The drift scan compares archived scenario names
The drift scan SHALL parse the `ADDED` and `MODIFIED` scenario names
of every archived change delta and SHALL report the names the
capability spec does not hold today. An archived change with no delta
stays out. A capability with no spec directory marks its scenarios.

#### Scenario: A missing scenario name gets reported
- **WHEN** an archived delta carries a scenario name the live spec
  does not hold
- **THEN** the drift scan reports the name

### Requirement: The history ranking counts the merged commits
The history ranking SHALL feed one `git log --name-only --format=%H
main` call into the merged commit count per uncovered area. Ties
order by area name.

#### Scenario: A tie orders by area name
- **WHEN** two uncovered areas carry the same commit count
- **THEN** the ranking orders them by area name

### Requirement: The exit codes name the failure
The tool SHALL exit 0 on a completed run. The tool SHALL exit 2 on a
failed fact call, with the reason on stderr.

#### Scenario: A failed fact call exits 2
- **WHEN** the tool hits a failed fact call
- **THEN** the tool exits 2 and the reason lands on stderr
