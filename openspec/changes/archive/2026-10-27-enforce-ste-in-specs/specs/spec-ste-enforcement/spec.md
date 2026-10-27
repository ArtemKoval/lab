# spec-ste-enforcement Specification (Delta)

## Purpose

The mechanical ASD-STE100 gate for spec text. One CLI owns the rules. The pytest gate and the write-time hook enforce them.

## ADDED Requirements

### Requirement: The checker reports mechanical STE violations
The CLI at `tools/spec_ste_check` SHALL scan a file or a tree. It SHALL report each violation with the file, the line, the rule, and the text. The CLI SHALL exit 0 on a clean scan and 2 when an error exists. The `--json` flag SHALL give machine-readable output.

#### Scenario: A violation carries its location
- **WHEN** the checker scans a file with a sentence over the word cap
- **THEN** the report names the file, the line number, the rule, and the sentence text
- **AND** the CLI exits 2

#### Scenario: A clean tree exits 0
- **WHEN** the checker scans a tree with no violations
- **THEN** the CLI prints no violations and exits 0

#### Scenario: JSON output parses
- **WHEN** the checker runs with `--json` on a file with one violation
- **THEN** stdout parses as JSON and carries the file, the line, the rule, the text, and the severity of the violation

### Requirement: The checker examines prose only
The rules SHALL examine prose. Code spans, fenced code blocks, commands, paths, identifiers, and quoted text SHALL stay exempt. A code element SHALL count as one word in the word count.

#### Scenario: A long code span passes the cap
- **WHEN** a sentence holds a code span of ten tokens and nine prose words
- **THEN** the code span counts as one word and the checker reports no violation

#### Scenario: A fenced block stays exempt
- **WHEN** a fenced code block holds a semicolon and a 40-word line
- **THEN** the checker reports no violation

### Requirement: The checker enforces the sentence caps
The checker SHALL cap an imperative sentence at 20 words and any other sentence at 25 words. A hyphenated group, a number with its unit, and a code element SHALL count as one word each.

#### Scenario: The caps follow the sentence type
- **WHEN** a file holds a 24-word imperative sentence and a 27-word descriptive sentence
- **THEN** the checker reports two word-cap errors and exits 2

### Requirement: The checker enforces the banned words and the punctuation
The checker SHALL treat `perform`, `utilize`, `ensure`, and `provide` as banned words. It SHALL treat `check` as a banned word only as a verb. It SHALL treat a semicolon and a contraction as errors.

#### Scenario: The checker tells the word `check` apart by its role
- **WHEN** one sentence says `Examine the check.` and another says `Check the logs.`
- **THEN** the checker reports the verb use as a banned-word error and accepts the noun use

#### Scenario: Punctuation and a contraction are errors
- **WHEN** a sentence says `Don't run it; the state is stale.`
- **THEN** the checker reports a contraction error and a semicolon error

### Requirement: The checker treats tenses by strength
The checker SHALL treat a progressive tense as an error. It SHALL treat a perfect tense as a warning. A warning SHALL never change the exit code.

#### Scenario: A perfect tense warns without a failure
- **WHEN** a sentence says `The job has finished.`
- **THEN** the report carries a perfect-tense warning and the CLI exits 0

#### Scenario: A progressive tense is an error
- **WHEN** a sentence says `The job is running.`
- **THEN** the report carries a progressive-tense error and the CLI exits 2

### Requirement: The gate scope is the specs and the active changes
The checker SHALL scan `openspec/specs/**` and the active directories under `openspec/changes/**`. It SHALL skip `openspec/changes/archive/`.

#### Scenario: An archived violation stays out
- **WHEN** a file under `openspec/changes/archive/` holds a semicolon
- **THEN** the checker reports no violation for that file

#### Scenario: An active change document is in scope
- **WHEN** a `proposal.md` under an active change directory holds a 30-word sentence
- **THEN** the checker reports the violation

### Requirement: The pytest gate fails the suite on an error
A test in the root suite SHALL run the checker over the gate scope. An error in the scope SHALL fail the suite. A warning SHALL NOT fail the suite.

#### Scenario: An error turns the suite red
- **WHEN** the gate scope holds one banned word and the suite runs
- **THEN** the gate test fails and names the violation

#### Scenario: A warning keeps the suite green
- **WHEN** the gate scope holds only a perfect-tense warning and the suite runs
- **THEN** the gate test passes

### Requirement: The hook blocks a non-STE write to a spec path
The hook runs before `Write` and `Edit` apply their change. The script `.claude/hooks/spec-ste-gate.sh` SHALL filter to the gate paths and SHALL examine the text after the edit. An error SHALL block the write, and the block SHALL name the violations on stderr. A warning SHALL NOT block the write. If the checker cannot run, the hook SHALL allow the write and print a note on stderr.

#### Scenario: A violating write blocks
- **WHEN** a `Write` targets a file under `openspec/specs/` and its content holds a semicolon
- **THEN** the hook blocks the write and stderr names the semicolon rule with the line number

#### Scenario: An archive edit passes
- **WHEN** an `Edit` targets a file under `openspec/changes/archive/`
- **THEN** the hook allows the write without a scan

#### Scenario: A warning-only write passes
- **WHEN** the text after the edit carries one perfect-tense warning and no error
- **THEN** the hook allows the write

#### Scenario: A broken setup fails open
- **WHEN** the hook cannot run the checker on a machine without the repository venv
- **THEN** the hook allows the write and prints a note on stderr
