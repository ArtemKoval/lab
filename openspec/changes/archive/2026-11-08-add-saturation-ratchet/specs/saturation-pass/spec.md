## ADDED Requirements

### Requirement: The owned tools sit in one table
The CLI SHALL carry one table with nine owned tools: `plan_exec`,
`spec_ste_check`, `devcontainer_init`, `handover_telemetry`,
`handover_telemetry_setup`, `dspy_gate`, `dspy_gate_setup`,
`peak_hours_gate`, and `process_issues`. Each entry carries the
product path and the test suite path of that tool. `project_setup`
stays out because it carries no product Python.

#### Scenario: The table names the nine owned tools
- **WHEN** a reader opens the table in the CLI source
- **THEN** the table holds exactly the nine owned tool names and no
  entry for `project_setup`

### Requirement: The pass runs the mutator over the selected tools
The CLI SHALL run the vendored mutator over the product path of every
selected tool with that tool's test command and the
`--use-existing-coverage` flag. The CLI SHALL verify the coverage
report exists at `--coverage PATH`, with the default
`target/coverage/python/lcov.info`. The CLI SHALL exit 2 with a
message that names `--coverage` when that file is missing.

#### Scenario: A run over one clean tool exits 0
- **GIVEN** a store whose module scores match a passing mutator run
- **WHEN** the CLI runs with the name of that tool
- **THEN** the CLI exits 0 and prints one score line per module

#### Scenario: A missing coverage report fails with the flag hint
- **GIVEN** no coverage report at the default path
- **WHEN** the CLI runs without `--coverage`
- **THEN** the CLI exits 2 and the message names `--coverage`

### Requirement: The pass parses the printed function table
The CLI SHALL parse the printed per-function table of the mutator.
The CLI SHALL group the rows by the namespace column and SHALL
compute each module score as `round(100 * sum(killed) / (sum(killed)
+ sum(survived)), 1)`. The CLI SHALL skip the header, the separator
line, and the `Total` row.

#### Scenario: The table groups by namespace
- **GIVEN** a printed table with rows from two namespaces
- **WHEN** the CLI parses the table
- **THEN** each namespace carries the sum of its rows, and the header,
  the separator, and the `Total` row stay out

### Requirement: The pass scores modules by their mutants
A namespace whose aggregated site count is zero carries no mutants.
The CLI SHALL omit it from the report and the store. A namespace with
sites but no executed mutants carries no score and never holds or
improves.

#### Scenario: A score-less run fails the pass
- **GIVEN** a mutator table whose module scores are all `n/a`
- **WHEN** the CLI compares the run against the store
- **THEN** the CLI exits 2 and names the tool and the modules with no
  score

#### Scenario: A siteless namespace stays out of the store
- **GIVEN** a mutator table with one namespace whose rows carry zero
  sites
- **WHEN** the CLI computes the module scores
- **THEN** the scores carry no entry for that namespace and the other
  namespaces keep their scores

### Requirement: The pass fails a table-less tool
When the mutator prints no table at all, the CLI SHALL treat that
tool as failed and name it.

#### Scenario: A mutator run with no table fails the tool
- **GIVEN** a mutator run that prints no table for one tool
- **WHEN** the pass finishes
- **THEN** the CLI exits 2 and names the tool with no table

### Requirement: The pass CLI selects the tools
The CLI SHALL accept a repeatable `--tool` option that limits the run
to the named tools in table order. The CLI SHALL exit 2 when a
`--tool` name is not in the table, and the message SHALL name the
unknown tool and the table names.

#### Scenario: The tool option selects a subset
- **GIVEN** the table holds three tools
- **WHEN** the CLI runs with `--tool` for one of them
- **THEN** the CLI runs the mutator for that tool only and skips the
  other two

#### Scenario: An unknown tool name fails the run
- **GIVEN** the table holds the nine owned tools
- **WHEN** the CLI runs with `--tool` for a name outside the table
- **THEN** the CLI exits 2 and names the unknown tool and the table
  names

### Requirement: The pass CLI reports and exits by the contract
The CLI SHALL write a JSON run report with `--json PATH`. The report
carries the module scores, the comparison verdicts, and the exit
verdict. The CLI SHALL exit 0 when every module score holds or
improves and no tool failed. The CLI SHALL exit 2 on a ratchet
violation, an `n/a` score, a failed tool, or an operational failure.
A mutator exit 3 alone does not fail a tool. The parsed scores
decide. Any other non-zero mutator exit fails the tool.

#### Scenario: The exit contract separates a pass from a refusal
- **GIVEN** one run with no drop and one run with a drop
- **WHEN** the CLI finishes each run
- **THEN** the clean run exits 0 and the refusing run exits 2

#### Scenario: Survivors with held scores pass the ratchet
- **GIVEN** a mutator run that exits 3 with every module score equal
  to the store
- **WHEN** the CLI finishes the run
- **THEN** the CLI exits 0

#### Scenario: A mutator baseline failure fails one tool
- **GIVEN** a mutator run that exits 2 for one tool
- **WHEN** the pass finishes
- **THEN** the CLI exits 2, names the tool and the mutator exit code,
  and still runs the remaining tools

### Requirement: The ratchet refuses a per-module score drop
The CLI SHALL compare each module score of the run against the stored
score of the same tool and module. A run score below the stored score
SHALL fail the run. The refusal message SHALL name the tool, the
module, the stored score, and the run score. A module absent from the
store SHALL be recorded without a comparison. A missing or unreadable
store SHALL fail the run with a message that names `--init`.

#### Scenario: A score drop fails the run
- **GIVEN** a store that records module `spec_ste_check.rules` at
  score 100.0
- **WHEN** a mutator run reports score 95.5 for that module
- **THEN** the CLI exits 2 and names the tool, the module, 100.0, and
  95.5

#### Scenario: A new module is recorded without a refusal
- **GIVEN** a store with no entry for the reported module
- **WHEN** a mutator run reports a score for that module
- **THEN** the CLI exits 0 and the report carries the new module

#### Scenario: A missing store fails with the init hint
- **GIVEN** no store file at the store path
- **WHEN** the CLI runs without `--init`
- **THEN** the CLI exits 2 and the message names `--init`

### Requirement: The store schema is pinned
The CLI SHALL read and write the store at `--store PATH` with the
default `reports/saturation/scores.json`. The store is one JSON
object with `schema` set to 1. Each key under `tools` names one tool.
Each tool entry carries `stamp` and `modules`. Each key under
`modules` is one namespace string of the mutator. Each module entry
carries `sites` as an integer and `score` as one float with one
decimal place. Each `stamp` is an ISO 8601 UTC string.

#### Scenario: The store shape matches the schema
- **GIVEN** a store written by `--init` for one tool
- **WHEN** a reader loads the JSON
- **THEN** the object carries `schema` 1, one tool entry with `stamp`
  and `modules`, and one module entry per namespace with `sites` and
  `score`

### Requirement: The store actions are explicit
The actions are mutually exclusive. The CLI SHALL exit 2 when `--init`
and `--update` are both present. `--init` SHALL refuse when the store
exists and SHALL name it. `--update` SHALL refuse a run with any
violation. Under `--update`, the CLI SHALL drop store modules the run
did not report, and the report SHALL name each dropped module.

#### Scenario: The two actions refuse each other
- **GIVEN** a store file at the store path
- **WHEN** the CLI runs with `--init` and `--update`
- **THEN** the CLI exits 2 and names both actions

#### Scenario: Init refuses an existing store
- **GIVEN** a store file at the store path
- **WHEN** the CLI runs with `--init`
- **THEN** the CLI exits 2 and names the existing store

#### Scenario: Update rewrites the store after a clean run
- **GIVEN** a store with a stamp one hour in the past and a lower
  score for one module
- **WHEN** a clean run reports a higher score and the CLI runs with
  `--update`
- **THEN** the store carries the higher score and a newer stamp

#### Scenario: Update refuses a violating run
- **GIVEN** a store at score 100.0 for one module
- **WHEN** a run reports a lower score and the CLI runs with
  `--update`
- **THEN** the CLI exits 2 and the store keeps the old entry

#### Scenario: Update drops a stale module
- **GIVEN** a store with an entry for a module the clean run did not
  report
- **WHEN** the CLI runs with `--update`
- **THEN** the store drops that entry and the report names it

### Requirement: The scheduled workflow carries its budget
The repository SHALL carry `.github/workflows/saturation.yml`. The
workflow SHALL trigger on the cron `37 4 * * 1` and on
`workflow_dispatch` with a `tools` input. The workflow SHALL run only
when `vars.SATURATION_PASS_ENABLED != 'false'` holds. The workflow
SHALL carry `timeout-minutes: 90` and a concurrency group named
`saturation-` with the ref, and `cancel-in-progress` false.

#### Scenario: The contract test pins the budget properties
- **GIVEN** the workflow file text
- **WHEN** the contract test parses it
- **THEN** the test asserts the cron value, the dispatch input, the
  variable expression, the timeout, the concurrency group, and
  `cancel-in-progress` false

### Requirement: The scheduled workflow runs the pass and touches nothing
The workflow SHALL build the three gate venvs and the shared venv,
SHALL produce one coverage report over the owned tools and `tests`,
SHALL run the pass CLI with `--json target/saturation/report.json`,
and SHALL upload that report with `if: always()` and
`if-no-files-found: ignore`. The workflow SHALL NOT write the store
and SHALL NOT carry a store write step or a push step. A workflow
contract test SHALL pin these properties.

#### Scenario: The contract test pins the run and the absence
- **GIVEN** the workflow file text
- **WHEN** the contract test parses it
- **THEN** the test asserts the pass step, the report path, the
  upload, and the absence of store write steps and push steps

#### Scenario: The dispatch input selects the tools
- **GIVEN** a manual dispatch with a tools input of one tool name
- **WHEN** the workflow runs the pass CLI
- **THEN** the CLI receives `--tool` with that name
