# gate-learning Specification

## Purpose
The learning loop turns gate failures into next week's behavior. The example bank takes judge-gated writes, the seven-step nightly run carries the five safety rails, and drafted changes wait for a human.

## Requirements

### Requirement: The nightly loop runs seven idempotent steps in order
The learning runner SHALL run collect, triage, expand, optimize, certify, promote, and escalate in that order. Each step SHALL be idempotent. The collect step SHALL pull the gate failures of the last 24 hours.

#### Scenario: The loop runs the seven steps in order
- **WHEN** the runner completes one full pass on a log with one eval gap
- **THEN** the run report lists the seven steps in order with their outcomes

### Requirement: The triage step classifies each failure
The triage step SHALL classify each failure as an eval gap, a spec gap, environment rot, or a known flake. The expand step SHALL grow the train set from the failing scenario text for every eval gap.

#### Scenario: An eval gap grows the train set
- **WHEN** the triage step classifies a failure as an eval gap
- **THEN** the expand step adds cases derived from the failing scenario text

### Requirement: The escalate step drafts a change for a recurring spec gap
The escalate step SHALL draft an OpenSpec change for a recurring spec gap. The draft SHALL wait for a human. The runner SHALL never edit `openspec/specs/`.

#### Scenario: A spec gap drafts a change and nothing more
- **WHEN** the triage step classifies a failure as a spec gap
- **THEN** the runner drafts a change under the draft area and never edits `openspec/specs/`

### Requirement: The example bank takes judge-gated writes and evicts on regression
The bank SHALL store one JSONL entry per validated trajectory. Each entry SHALL hold the scenario ID, the inputs, the final prediction, the compact trace, and the gate verdicts. The bank SHALL accept a write only when the trajectory passed its gates. The bank SHALL evict an entry when the entry fails a frozen suite. The retrieval SHALL return the most similar entries for a query.

#### Scenario: A passing trajectory enters the bank
- **WHEN** the bank receives an entry whose gate verdicts are all green
- **THEN** the bank appends the entry to the JSONL store

#### Scenario: A failing trajectory stays out
- **WHEN** the bank receives an entry with a red gate verdict
- **THEN** the bank refuses the write and reports the verdict

#### Scenario: A regressed entry leaves the bank
- **WHEN** a bank entry fails a frozen suite on a re-run
- **THEN** the bank removes that entry and records the eviction

### Requirement: Five safety rails bound the loop
The runner SHALL honor five rails. The optimizer SHALL never see the held-out set. Every candidate SHALL run the frozen suites before promotion. No path SHALL lead from run feedback to a requirement, a threshold, or a rubric without a human review. The budgets `max_optimize_loops` and the token ceilings SHALL bound every autonomous run. Promotion SHALL be a pointer move to a versioned artifact, and rollback SHALL be the same move in reverse.

#### Scenario: The optimizer never sees the held-out set
- **WHEN** the runner splits the scenarios with a holdout ratio of 0.3
- **THEN** no held-out scenario ID appears in the train or validation sets

#### Scenario: A candidate that regresses a frozen suite stays unpromoted
- **WHEN** a candidate passes the held-out set and fails one frozen suite
- **THEN** the runner discards the candidate and keeps the current artifact version

### Requirement: The scheduled run is default-off
The nightly workflow SHALL carry a cron trigger. Each job SHALL run only when the repository variable `DSPY_NIGHTLY_ENABLED` is true and the `ZAI_API_KEY` secret exists. The workflow SHALL also carry a manual dispatch trigger that honors the same condition.

#### Scenario: The job skips without the variable
- **WHEN** the schedule fires and `DSPY_NIGHTLY_ENABLED` is unset
- **THEN** no job of the nightly workflow runs

#### Scenario: The job runs with the variable and the key
- **WHEN** the schedule fires, the variable is true, and the secret exists
- **THEN** the nightly job runs the learning loop through the CLI
