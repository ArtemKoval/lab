## ADDED Requirements

### Requirement: The ledger store and the marker

The `ledger` store SHALL sit at `.process_issues/ledger.jsonl` in the
state dir, and the appends SHALL carry a newline guard. An intent line
SHALL carry `event`, `id`, `kind`, `key`, and `at`, and a confirmation
line SHALL carry `event`, `id`, and `at`. Each intent SHALL carry a
fresh marker id over the injected clock and random source, and the
writer SHALL regenerate on a collision. A loop comment SHALL embed its
marker at the end of the body behind the fixed first line.

#### Scenario: A write prints a fresh marker

- **WHEN** `ledger write --kind comment --key 15` runs twice
- **THEN** the two markers differ and the store carries two intents

#### Scenario: The comment embed keeps the fixed first line

- **GIVEN** the recipe embeds the marker in a loop comment
- **WHEN** the fold rule reads the comment
- **THEN** the first line stays `process-issues loop` and the marker
  sits at the end of the body

### Requirement: The ledger command actions

The `ledger` command SHALL carry the three actions `write`, `confirm`,
and `pending`. `write` SHALL print the marker and draw one stderr note
on a second live intent for one kind and key. `confirm` SHALL append
the confirmation, no-op on a second confirm, and refuse an unknown id
at exit 2. `pending` SHALL print the unconfirmed intents with a
superseded flag per kind and key, and the newest row of a group SHALL
own the decision.

#### Scenario: A confirm lands once

- **GIVEN** the store carries the intent with the marker `loop-m`
- **WHEN** `ledger confirm --id loop-m` runs twice
- **THEN** both runs exit 0 and the store carries one confirmation

#### Scenario: An unknown id refuses

- **WHEN** `ledger confirm --id loop-none` runs against a store
  without that marker
- **THEN** the exit code is 2 and stderr names the marker

#### Scenario: The pending view flags the superseded rows

- **GIVEN** the store carries two unconfirmed comment intents for one
  issue and one confirmed intent for another
- **WHEN** `ledger pending --json` runs
- **THEN** the rows carry the older row with `superseded` true, the
  newest row with `superseded` false, and no confirmed row

### Requirement: The ledger exit contract

The read SHALL skip a line that is not a valid event record with one
numbered note at exit 0, and a blank line SHALL skip without a note.
The command SHALL exit 2 on an unreadable store or a confirm for an
unknown id. A missing store SHALL give `write` a created store and
`pending` an empty list at exit 0. A usage error SHALL exit 64.

#### Scenario: A torn line skips with a note

- **GIVEN** the store carries one valid intent and one line that is
  not a valid event record
- **WHEN** `ledger pending` runs
- **THEN** stderr carries one note with the line number
- **AND** the exit code is 0 and the valid intent prints

#### Scenario: A missing store is empty pending

- **GIVEN** no ledger file exists
- **WHEN** `ledger pending --json` runs
- **THEN** the output is an empty JSON array and the exit code is 0

#### Scenario: An unknown action exits 64

- **WHEN** the ledger command runs with an unknown action
- **THEN** the exit code is 64

### Requirement: The loop recipe writes through the ledger

The loop phases SHALL run `ledger write` before each loop GitHub write
and `ledger confirm` after it. The resume, repair, and start actions
SHALL run `ledger pending` first. The recipe SHALL run the ledger
commands under the run lock, and a ledger exit 2 mid-phase SHALL behave
like a gate failure.

#### Scenario: The recipe orders the ledger steps around each write

- **WHEN** a loop phase does a GitHub write
- **THEN** the phase runs `ledger write` before the write and
  `ledger confirm` after it

#### Scenario: The resume, repair, and start read pending first

- **WHEN** the resume, repair, or start action begins
- **THEN** the action runs `ledger pending` before any write

#### Scenario: A ledger fault behaves like a gate failure

- **GIVEN** `ledger write` exits 2 mid-phase
- **WHEN** the phase handles the fault
- **THEN** one comment names the ledger fault and the phase stops

### Requirement: The ledger resume rules per kind

For each pending comment intent, the phase SHALL scan the issue comment
bodies for the literal marker, confirm every marker it finds, and retry
only a missing newest marker with the same marker. A label intent SHALL
retry as a re-add. A merge or close intent SHALL retry and tolerate the
already-done error, and the tolerated error SHALL confirm the intent. A
superseded intent that can no longer confirm SHALL stay in the audit
trail and out of the decision.

#### Scenario: The resume reconciles by the markers

- **GIVEN** a pending comment intent whose marker sits in a posted
  comment
- **WHEN** the resume runs its reconcile
- **THEN** the phase confirms that marker and posts nothing

#### Scenario: A missing newest marker retries with the same marker

- **GIVEN** a pending comment intent whose marker sits in no comment
- **WHEN** the resume retries the write
- **THEN** the write embeds the same marker and no new intent joins

#### Scenario: A label intent retries as a re-add

- **GIVEN** a pending label intent for one issue
- **WHEN** the resume works the group
- **THEN** the phase re-adds the label and confirms the intent

#### Scenario: A close intent tolerates the already-done error

- **GIVEN** a pending close intent for a closed issue
- **WHEN** the resume retries the close
- **THEN** the tolerated error confirms the intent
