## ADDED Requirements

### Requirement: The loop acknowledges the pick

The loop SHALL post one pick comment on the issue before the first
phase step. The pick comment SHALL keep the fixed first line and SHALL
carry one line in the form `On it: <object and expected result>`. The
line SHALL name the object and the expected result. The loop SHALL NOT
replace the line with a plan sentence that names no object. One pick
comment SHALL serve each issue that enters a pipeline path. The loop
SHALL post no progress comment on the issue before the phase result.

#### Scenario: The pick line names the object

- **GIVEN** the scan maps issue 40 to the state propose with the
  action `start`
- **WHEN** the loop starts the propose phase for issue 40
- **THEN** the pick comment carries one `On it:` line with the object
  and the expected result

#### Scenario: The fixed first line stays first

- **GIVEN** the recipe wraps the pick comment write in the ledger
  steps
- **WHEN** the loop posts the pick comment
- **THEN** the first line is `process-issues loop` and the `On it:`
  line follows it

#### Scenario: The loop stays silent before the result

- **GIVEN** the pick comment is on the issue
- **WHEN** the loop runs the phases
- **THEN** the loop posts no progress comment on the issue before the
  phase result
