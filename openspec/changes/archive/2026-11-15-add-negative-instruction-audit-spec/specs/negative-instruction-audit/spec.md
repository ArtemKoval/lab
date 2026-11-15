## Purpose

The negative-instruction-audit capability inventories the prohibitive
instructions in the harness text and classifies each finding against
the guard-test pins. The tool owns the sentence detection and the pin
classification. The operator owns the contract judgment on the
unpinned candidates. The scan is read-only and runs without a
network. Five documented miss classes stay outside the recall by
design.

## ADDED Requirements

### Requirement: The scan selects the harness surfaces in a stable order
The scan SHALL read `CLAUDE.md`, every `.claude/skills/*/SKILL.md`,
every `.claude/agents/*.md`, and `.claude/hooks/harness-charter.sh`.
The order SHALL put the root file first, then the skills, then the
agents, then the charter hook. The scan SHALL sort the skill paths and
the agent paths. The scan SHALL drop a surface that does not exist.
The output styles and the test tree sit outside the scan.

#### Scenario: The surfaces come in the stable order
- **GIVEN** a root with `CLAUDE.md`, two skill files, two agent files,
  and the charter hook
- **WHEN** the scan collects the surfaces
- **THEN** the list starts with `CLAUDE.md`, the skill files follow in
  path order, the agent files follow in path order, and the charter
  hook comes last

#### Scenario: An absent surface drops out
- **GIVEN** a root with only `CLAUDE.md`, with no skills, agents, or
  charter hook
- **WHEN** the scan collects the surfaces
- **THEN** the list holds `CLAUDE.md` alone

#### Scenario: An absent charter hook drops out
- **GIVEN** skill files and agent files exist, and the charter hook
  file does not exist
- **WHEN** the scan collects the surfaces
- **THEN** the list carries no charter hook

#### Scenario: The out-of-scope trees stay out
- **GIVEN** the root carries test files under `tests/` and one output
  style under `.claude/output_styles/`
- **WHEN** the scan collects the surfaces
- **THEN** the list carries no path under `tests/` and no path under
  `.claude/output_styles/`

### Requirement: The scan splits the prose into sentence candidates
The scan SHALL remove every fenced code block before the split. The
scan SHALL strip a bullet marker from each line. The scan SHALL join
the remaining lines with one space. The scan SHALL split the joined
text after `.`, `!`, or `?`. A candidate under 12 characters SHALL
drop.

#### Scenario: A fenced block stays out of the candidates
- **GIVEN** a file carries one rule, one fenced block with shell
  commands, and one line after the fence
- **WHEN** the scan splits the file text
- **THEN** no candidate carries fenced text, and the rule and the
  last line appear in the candidates

#### Scenario: Each bullet gives one candidate
- **GIVEN** a file carries bullets with the `-`, `*`, `2.`, and `3)`
  markers, and every bullet ends with a sentence ender
- **WHEN** the scan splits the file text
- **THEN** each bullet gives one candidate without its marker

#### Scenario: A bullet without a sentence ender joins the next line
- **GIVEN** a file carries one bullet without a sentence ender and
  one line after it
- **WHEN** the scan splits the file text
- **THEN** the bullet text and the next line form one candidate

#### Scenario: Wrapped lines join into one candidate
- **GIVEN** one sentence spans three physical lines
- **WHEN** the scan splits the file text
- **THEN** the scan joins the three lines, and the sentence is one
  candidate

#### Scenario: A short candidate drops
- **GIVEN** the text carries one candidate of 11 characters and one
  candidate of 12 characters
- **WHEN** the scan splits the text
- **THEN** the 11-character candidate drops, and the 12-character
  candidate stays

### Requirement: The scan flags the sentences that carry a prohibitive marker
The marker set holds `never`, `do not`, `don't`, `should not`,
`must not`, `shall not`, `cannot`, and `avoid`. The scan SHALL flag a
candidate that carries one marker word, and the match SHALL ignore the
letter case. The scan SHALL flag `no` at the start of a candidate
only. The scan SHALL match a marker word on a word boundary. A
candidate with no marker SHALL NOT join the findings.

#### Scenario: A marker word flags the candidate
- **GIVEN** candidates with `never`, `do not`, `should not`,
  `must not`, `shall not`, `cannot`, `avoid`, and `don't`
- **WHEN** the scan examines each candidate
- **THEN** every candidate with one marker word joins the findings

#### Scenario: The match ignores the letter case
- **GIVEN** one candidate starts with `Never` and one candidate
  carries `AVOID`
- **WHEN** the scan examines the candidates
- **THEN** both candidates join the findings

#### Scenario: The word no counts at the start only
- **GIVEN** one candidate starts with `No`, and one candidate carries
  `no` after the first word
- **WHEN** the scan examines the candidates
- **THEN** the first candidate joins the findings, and the second
  candidate stays clean

#### Scenario: A documented miss class stays out
- **GIVEN** the five documented miss classes: the bare-not contrast,
  the verb plus `no`, the positively-phrased prohibition, the
  only-conditional, and the before-conditional
- **WHEN** the scan examines one candidate of each class
- **THEN** no candidate joins the findings

### Requirement: The scan classifies each finding against the test pins
The scan SHALL collect the string literals of the `*.py` files under
`tests/` at every depth. The scan SHALL measure the literal before
the collapse. A literal under 20 characters SHALL drop. The scan
SHALL collapse whitespace runs to one space on both sides. A
substring match in both directions pins the finding. A finding with
a match SHALL report as pinned, and the others SHALL report as
candidates. A test file that does not parse SHALL drop from the pin
set.

#### Scenario: A pin match works in both directions
- **GIVEN** one candidate contains a pin literal, and one candidate
  forms part of a longer pin literal
- **WHEN** the scan classifies the findings
- **THEN** both findings report as pinned

#### Scenario: A short literal gives no pin
- **GIVEN** the test tree holds one string literal of 19 characters,
  and no other literal matches the harness candidates
- **WHEN** the scan classifies the findings
- **THEN** the 19-character literal gives no pin, and the findings
  report as candidates

#### Scenario: A paraphrase reads as a candidate
- **GIVEN** one test pins a sentence, and the harness file carries a
  paraphrase of that sentence
- **WHEN** the scan classifies the findings
- **THEN** the paraphrase reports as an unpinned candidate

#### Scenario: A broken test file drops from the pin set
- **GIVEN** one `*.py` file under `tests/` does not parse, and the
  other test files parse
- **WHEN** the scan collects the pin literals
- **THEN** the scan skips the broken file, and the other literals stay
  in the pin set

### Requirement: The scan report carries per-file records and totals
The report SHALL carry one record per scanned file. Each record SHALL
carry the path, the sentence count, the negative count, the pinned
count, the findings, and the unpinned candidates. Each finding SHALL
carry the sentence text and the pinned flag. The sentence count SHALL
number the candidates that survive the drop. The totals SHALL carry
the five counts over all files.

#### Scenario: A record carries its fields
- **GIVEN** one harness file with one pinned finding and one unpinned
  finding
- **WHEN** the scan runs
- **THEN** the record of that file carries the path, the three counts,
  both findings with the sentence and the pinned flag each, and the
  unpinned finding in the candidates list

#### Scenario: The totals carry the five counts
- **GIVEN** a root with harness files that carry findings
- **WHEN** the scan runs
- **THEN** the totals carry the file count, the sentence count, the
  negative count, the pinned count, and the candidate count

#### Scenario: The totals keep the identity
- **GIVEN** a root with harness files that carry findings
- **WHEN** the scan runs
- **THEN** the candidate count equals the negative count minus the
  pinned count

### Requirement: The CLI prints the report as text or JSON
Without `--json` the CLI SHALL print one totals line, then the path of
each file with findings, then one line per finding. A finding line
SHALL start with the marker `[pinned ]` or `[cand   ]`, and the CLI
SHALL cut the sentence text at 110 characters. The CLI SHALL print
nothing for a file with no findings. With `--json` the CLI SHALL print
the report as JSON on standard output. The JSON `files` array SHALL
carry every scanned file.

#### Scenario: The text report prints the totals and the findings
- **GIVEN** harness files with pinned findings and unpinned findings
- **WHEN** the CLI runs without `--json`
- **THEN** the first line carries the five totals, and each file with
  findings prints its path and one line per finding

#### Scenario: The output skips a file with no findings
- **GIVEN** one harness file carries no negative sentence
- **WHEN** the CLI runs without `--json`
- **THEN** the output carries no path line for that file

#### Scenario: The JSON output carries the report
- **GIVEN** harness files with findings
- **WHEN** the CLI runs with `--json`
- **THEN** standard output parses as one JSON object with `root`,
  `totals`, and `files`

#### Scenario: The JSON carries every scanned file
- **GIVEN** one harness file carries no negative sentence
- **WHEN** the CLI runs with `--json`
- **THEN** the `files` array carries one record for that file

### Requirement: The CLI resolves the repository root before the scan
The CLI SHALL resolve the repository root before the scan. The
default root SHALL be the working directory. The flag `--repo-root`
SHALL override the root with its path argument. Every scan input
SHALL sit under the resolved root.

#### Scenario: The default root is the working directory
- **GIVEN** the CLI runs with no `--repo-root` flag
- **WHEN** the scan runs from a repository root
- **THEN** the scan reads the harness files under the working
  directory

#### Scenario: The flag overrides the root
- **GIVEN** the flag `--repo-root` names a repository root
- **WHEN** the CLI runs
- **THEN** the scan reads the harness files and the test tree under
  that root

### Requirement: The CLI exits 0 on a complete scan and 2 without a tests tree
The CLI SHALL exit 0 after a completed scan in both output modes. The
CLI SHALL exit 2 when `tests/` does not exist under the root. The
failure SHALL print one message on standard error. The message SHALL
name the missing `tests/` tree and one next action: run from the
repository root, or pass `--repo-root`.

#### Scenario: A completed scan exits 0
- **GIVEN** a root with a `tests/` tree and harness files
- **WHEN** the CLI runs without `--json` and then with `--json`
- **THEN** both runs exit 0

#### Scenario: A missing tests tree exits 2 with one next action
- **GIVEN** the root carries no `tests/` directory
- **WHEN** the CLI runs with `--repo-root` at that root
- **THEN** the exit code is 2, the message on standard error names
  `no tests/`, and the message names one next action: run from the
  repository root, or pass `--repo-root`

### Requirement: The scan stays read-only
The scan SHALL read the harness files and the test tree only. The
scan SHALL write no file. The scan SHALL NOT change the content of a
scanned file.

#### Scenario: The tree stays unchanged after a scan
- **GIVEN** a fixture repository root
- **WHEN** the CLI runs in both output modes
- **THEN** every scanned file keeps its content, and the run creates
  no file
