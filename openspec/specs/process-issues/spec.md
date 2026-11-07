# process-issues Specification

## Purpose

The process-issues loop scans the open GitHub issues of this repo and runs the feature delivery pipeline for one issue at a time. The labels carry the loop state, and one human spec-approval gate sits between the propose phase and the apply phase of a spec-carrying change.

## Requirements

### Requirement: The scan classifies each open issue into one loop state
The `scan` subcommand SHALL list the open issues with their author, their labels, and their open pull requests. The CLI SHALL map each issue to one loop state from its author admission, its labels, the pull request links, and the artifact presence. The admission SHALL run before the label precedence. An author outside the allowed-author list SHALL map to the state `refused` with the action `none`. A login whose lowercase form ends with `[bot]` SHALL refuse. An absent or null author SHALL refuse. The refusal sits above every label state. The label precedence SHALL be `handover`, then `blocked`, then `answered`, then `human-approved`, then `waiting-human-approval`, then no label. The allowed-author comparison SHALL ignore letter case. The scan order SHALL follow `createdAt` from oldest to newest.

#### Scenario: A foreign author refuses
- **GIVEN** issue 30 carries the login `stranger` and the allowed list carries `ArtemKoval`
- **WHEN** the scan classifies issue 30
- **THEN** the state is refused and the action is none

#### Scenario: A foreign handover label refuses
- **GIVEN** issue 31 carries the login `stranger` and the `handover` label
- **WHEN** the scan classifies issue 31
- **THEN** the state is refused

#### Scenario: A foreign blocked label refuses
- **GIVEN** issue 32 carries the login `stranger` and the `blocked` label
- **WHEN** the scan classifies issue 32
- **THEN** the state is refused

#### Scenario: An allowed author keeps the blocked state
- **GIVEN** issue 33 carries the login `ArtemKoval` and the `blocked` label
- **WHEN** the scan classifies issue 33
- **THEN** the state is blocked

#### Scenario: A listed bot login refuses
- **GIVEN** the allowed list names `helper[bot]` and issue 34 carries that login
- **WHEN** the scan classifies issue 34
- **THEN** the state is refused

#### Scenario: The login comparison ignores letter case
- **GIVEN** the allowed list carries `artemkoval` and issue 35 carries the login `ArtemKoval`
- **WHEN** the scan classifies issue 35
- **THEN** the state is not refused from the letter case

#### Scenario: A missing author refuses
- **GIVEN** issue 36 carries no author object in the fetch payload
- **WHEN** the scan classifies issue 36
- **THEN** the state is refused

#### Scenario: A handover label wins
- **GIVEN** issue 12 carries the `handover` label and the `human-approved` label
- **WHEN** the scan classifies issue 12
- **THEN** the state is skip

#### Scenario: An answered label wins
- **GIVEN** issue 13 carries the `answered` label and the `human-approved` label
- **WHEN** the scan classifies issue 13
- **THEN** the state is answered

#### Scenario: A gate label waits
- **WHEN** the scan classifies issue 14 with the `waiting-human-approval` label
- **THEN** the state is wait-approval

#### Scenario: A plain issue proposes
- **WHEN** the scan classifies issue 15 with no gate label
- **THEN** the state is propose

#### Scenario: The order is oldest first
- **GIVEN** issues 15 and 9 both classify as propose
- **WHEN** the loop runs
- **THEN** the loop processes issue 9 before issue 15
### Requirement: The apply and repair states need extra inputs
A `human-approved` issue with change artifacts SHALL report the state apply. A `human-approved` issue without change artifacts SHALL run the propose phase and continue into the apply phase. A no-label issue whose linked proposal PR is merged SHALL report the state propose with the repair action.

#### Scenario: An apply state with artifacts
- **GIVEN** issue 20 carries the `human-approved` label and its change artifacts exist
- **WHEN** the scan classifies issue 20
- **THEN** the state is apply

#### Scenario: A merged proposal PR repairs
- **GIVEN** issue 21 carries no gate label and its proposal PR is merged
- **WHEN** the scan classifies issue 21
- **THEN** the state is propose with the repair action

#### Scenario: An early approval skips the second stop
- **GIVEN** issue 16 carries the `human-approved` label with no change artifacts
- **WHEN** the loop runs
- **THEN** the loop runs the propose phase and continues into the apply phase

### Requirement: The propose phase gates a spec-carrying change
The loop SHALL run the propose phase for a propose-state issue and merge the proposal PR. The loop SHALL post a comment that references the change id and the merged PR, add the `waiting-human-approval` label, and leave the issue open. The loop SHALL repair a missing label before the first tag. The loop SHALL take no further action on the issue until the `human-approved` label appears.

#### Scenario: A spec change stops at the gate
- **WHEN** the propose phase completes for issue 15
- **THEN** the issue carries the spec reference comment and the `waiting-human-approval` label
- **AND** the issue stays open

#### Scenario: The loop repairs a missing label
- **GIVEN** the `waiting-human-approval` label does not exist in the repo
- **WHEN** the loop tags issue 15
- **THEN** the label exists and the issue carries it

#### Scenario: The wait blocks a second run
- **WHEN** a later scan classifies issue 15
- **THEN** the queue takes no action on issue 15

### Requirement: The proposal PR links the work
The proposal PR body SHALL carry a `Refs #NN` line. The branch name SHALL carry the change id.

#### Scenario: The proposal PR links the work
- **WHEN** the loop opens the proposal PR for issue 15
- **THEN** the PR body carries a `Refs #15` line
- **AND** the branch name carries the change id

### Requirement: The approval resumes the change into the apply and archive phases
On `human-approved`, the loop SHALL fold the human spec edits into the change artifacts. The fold SHALL read the issue body and the comments posted after the gate label. The newest text SHALL win. The loop SHALL recognize its own comments by their fixed first line, and its comments SHALL stay out of the fold. The loop SHALL run the apply phase and the archive phase, post the results, and close the issue as completed.

#### Scenario: The fold applies a comment edit
- **GIVEN** issue 15 is `human-approved` with a comment that changes a requirement
- **WHEN** the loop folds the edits
- **THEN** the change artifacts carry the new requirement text

#### Scenario: The newest text wins
- **GIVEN** two comments edit the same requirement
- **WHEN** the loop folds the edits
- **THEN** the change artifacts carry the newer comment text

#### Scenario: No edits apply as approved
- **GIVEN** issue 15 is `human-approved` with no edits after the gate label
- **WHEN** the loop folds the edits
- **THEN** the change artifacts stay as the proposal PR merged them

#### Scenario: The loop closes after the archive merge
- **WHEN** the archive PR for issue 15 merges
- **THEN** the loop posts the results on issue 15 and closes it as completed

### Requirement: The fix path runs without a gate
A change that restores intended behavior needs no spec. The loop SHALL run the full pipeline with the archive phase and no gate labels for such an issue.

#### Scenario: A bug fix runs to the end
- **GIVEN** issue 17 reports a defect that needs no spec
- **WHEN** the loop runs
- **THEN** the implementation PR and the archive PR merge
- **AND** the loop closes issue 17 as completed
- **AND** issue 17 carries no `waiting-human-approval` label

### Requirement: The informational path answers and marks
The loop SHALL post an answer comment, add the `answered` label, and leave an informational issue open. The `answered` label SHALL stop a second scan.

#### Scenario: A question gets an answer
- **WHEN** the loop processes an informational issue
- **THEN** the issue carries the answer comment and the `answered` label
- **AND** the issue stays open

#### Scenario: The label stops a second scan
- **WHEN** a later scan classifies an issue with the `answered` label
- **THEN** the state is answered and the loop takes no action

### Requirement: The loop skips handover issues
The loop SHALL skip an issue with the `handover` label. The loop SHALL NOT comment, label, or close that issue.

#### Scenario: A handover issue stays untouched
- **GIVEN** issue 18 carries the `handover` label
- **WHEN** the loop runs
- **THEN** the loop makes no change to issue 18

### Requirement: Gate failures post and continue
A gate failure SHALL produce one issue comment that names the failed gate. The loop SHALL continue with the next issue and SHALL NOT retry in the same run. A propose phase failure SHALL leave the issue unlabeled. An apply phase failure SHALL keep the `human-approved` label. The next run SHALL resume the failed phase from the change artifacts.

#### Scenario: A propose failure leaves no label
- **WHEN** a gate fails in the propose phase for issue 19
- **THEN** issue 19 carries one comment that names the failed gate
- **AND** issue 19 carries no new label
- **AND** the loop processes the next issue

#### Scenario: An apply failure keeps the approval
- **WHEN** a gate fails in the apply phase for issue 15
- **THEN** issue 15 keeps the `human-approved` label
- **AND** the next run resumes the apply phase

### Requirement: The run examines the peak window first
The loop SHALL examine the z.ai peak window before the first issue. The loop SHALL process no issue and SHALL report the window block when the window blocks model-backed work.

#### Scenario: A mid-window run stops
- **WHEN** the operator starts the run inside the peak window
- **THEN** the run processes no issue and reports the window block

### Requirement: Human and agentic issues share the propose phase
The loop SHALL treat a human issue and an agentic issue the same way. A free-form body SHALL produce drafted specs. A body that carries spec content SHALL transfer that content into the change artifacts.

#### Scenario: A free-form body drafts specs
- **WHEN** the propose phase runs on a free-form body
- **THEN** the change artifacts carry the drafted specs

#### Scenario: A spec body transfers
- **WHEN** the propose phase runs on a body with spec content
- **THEN** the change artifacts carry the spec content of the body

### Requirement: The loop pauses on a missing decision
When the pipeline needs a decision that the issue has not answered, the loop SHALL post the question on the issue and stop that issue. The issue label state SHALL stay unchanged.

#### Scenario: A question pauses the issue
- **WHEN** the pipeline needs a decision on issue 16
- **THEN** issue 16 carries the question comment
- **AND** the label state of issue 16 stays unchanged

### Requirement: The scan CLI reports the queue
The `scan` subcommand SHALL print one line per open issue with its number, state, and pull request links. The `--json` flag SHALL print the same data as JSON, and each entry SHALL carry the author login. The lock examination SHALL run before the first `gh` call, and the authors-config read SHALL run between the lock examination and the first `gh` call. The CLI SHALL exit 0 on success. The CLI SHALL exit 2 on an operational failure. The failures are a failed `gh` call, an unreadable state directory, a fresh foreign lock, or a missing, unparsable, or wrong-shape authors config. A config failure SHALL print one stderr note that names the config path and no queue. A usage error SHALL exit 64.

#### Scenario: A scan prints the queue
- **WHEN** the scan runs with `--json`
- **THEN** the output is a JSON array
- **AND** each entry carries the issue number, the state, the author login, and the pull request links

#### Scenario: A broken gh fails the run
- **GIVEN** the `gh` call fails
- **WHEN** the scan runs
- **THEN** the exit code is 2
- **AND** stderr names the failure

#### Scenario: A broken authors config fails the run
- **GIVEN** the authors config does not parse
- **WHEN** the scan runs
- **THEN** the exit code is 2
- **AND** stderr names the config path
- **AND** stdout carries no queue

#### Scenario: A usage error exits 64
- **WHEN** the scan runs with an unknown flag
- **THEN** the exit code is 64
- **AND** stderr carries the parser message
### Requirement: The blocked state
The scan SHALL map an open issue that carries the `blocked` label to the
state `blocked` and the action `blocked`. The label SHALL sit in the
precedence between `handover` and `answered`. The loop SHALL never retry a
blocked issue, and only the operator SHALL clear the label.

#### Scenario: A blocked issue reports the blocked state
- **GIVEN** an open issue that carries the `blocked` label and no other gate
  label
- **WHEN** the scan runs
- **THEN** the issue reports the state `blocked` and the action `blocked`

#### Scenario: A handover issue stays above a blocked label
- **GIVEN** an open issue that carries both the `handover` and the `blocked`
  labels
- **WHEN** the scan runs
- **THEN** the issue reports the state `skip`

#### Scenario: A blocked label outranks a stale answered label
- **GIVEN** an open issue that carries both the `blocked` and the `answered`
  labels
- **WHEN** the scan runs
- **THEN** the issue reports the state `blocked`

### Requirement: The loop takes and releases the run lock

The loop SHALL take the lock with `acquire --holder LABEL` before the
first scan, and the label SHALL name one run. The run SHALL release the
lock with `release --holder LABEL` at its end. The release SHALL remove
the file only on an exact holder label match, or behind `--force`. A
release with no lock file SHALL NOT be an error.

#### Scenario: A release without a lock is not an error

- **GIVEN** no lock file exists
- **WHEN** `release` runs with the holder `loop-20261108-a`
- **THEN** the exit code is 0

#### Scenario: A foreign holder release refuses

- **GIVEN** the lock file records the holder `loop-20261108-a`
- **WHEN** `release` runs with the holder `loop-20261108-b`
- **THEN** the exit code is 2
- **AND** the lock file stays

#### Scenario: A force release clears a lost lock

- **GIVEN** the lock file records a holder label that no run carries
- **WHEN** `release --force` runs
- **THEN** the lock file is gone and the exit code is 0

### Requirement: The run lock record

The lock file SHALL sit under the primary checkout root, resolved from
the git common directory, and a non-git root SHALL use the working
directory. The record SHALL carry the holder label, the host, the boot
id, the process id, the process start time, and the acquire time. The
record SHALL pin the session anchor of the calling session, or no
process id when the chain carries none.

#### Scenario: An acquire takes a free lock

- **GIVEN** no lock file exists
- **WHEN** `acquire` runs with the holder `loop-20261108-a`
- **THEN** the exit code is 0
- **AND** the lock file records the holder, the host, the boot id, the
  process id, the process start time, and the acquire time

### Requirement: The scan refuses a fresh foreign lock

The scan SHALL examine the lock before the first `gh` call, and a refused
scan SHALL make no `gh` call. A fresh foreign lock SHALL exit 2 with the
holder details on stderr. A scan whose holder label matches the lock in
force SHALL proceed. The scan SHALL NOT write the lock file.

#### Scenario: A fresh foreign lock refuses the scan

- **GIVEN** the lock file records a holder with a live process on this
  host and a young acquire time
- **WHEN** the scan runs with no holder label
- **THEN** the exit code is 2 and stderr names the holder
- **AND** no `gh` call runs

#### Scenario: The holder label exempts the scan

- **GIVEN** the lock file records the holder `loop-20261108-a` with a
  live process on this host
- **WHEN** the scan runs with the holder `loop-20261108-a`
- **THEN** the scan prints the queue

#### Scenario: The session anchor exempts the scan

- **GIVEN** the lock file records the process that anchors this calling
  session, with a live process on this host
- **WHEN** the scan runs with no holder label
- **THEN** the scan prints the queue

#### Scenario: A missing lock does not refuse the scan

- **GIVEN** no lock file exists
- **WHEN** the scan runs
- **THEN** the scan prints the queue

### Requirement: The stale rules of the run lock

The lock is stale when the record does not parse, the schema version is
unknown, the boot id differs from this boot, the recorded process id no
longer runs, the recorded start time differs from the running process, or
the acquire time is older than 24 hours. A lock recorded on another host
SHALL stay fresh until the acquire time passes the age rule.

#### Scenario: A dead holder marks the lock stale

- **GIVEN** the lock file records a process id that no longer runs on
  this host
- **WHEN** the scan runs
- **THEN** stderr reports the stale lock and the scan prints the queue

#### Scenario: A foreign-host lock stays fresh

- **GIVEN** the lock file records another host with a young acquire time
- **WHEN** the scan runs
- **THEN** the exit code is 2 and stderr names the holder

#### Scenario: An anchorless record ages out

- **GIVEN** the lock file records no process id and an acquire time
  more than 24 hours old
- **WHEN** the scan runs
- **THEN** stderr reports the stale lock and the scan prints the queue

#### Scenario: An old acquire time marks the lock stale

- **GIVEN** the lock file records an acquire time more than 24 hours old
- **WHEN** the scan runs
- **THEN** stderr reports the stale lock and the scan prints the queue

#### Scenario: A corrupt record is stale

- **GIVEN** the lock file does not parse
- **WHEN** the scan runs
- **THEN** stderr reports the stale lock and the scan prints the queue

### Requirement: A stale lock never wedges the loop

A stale lock SHALL draw a report on stderr, and the scan SHALL proceed.
`acquire` SHALL clear a stale lock and take it behind one exclusive file
create.

#### Scenario: The acquire clears a stale lock

- **GIVEN** the lock file records a process id that no longer runs
- **WHEN** `acquire` runs with the holder `loop-20261108-b`
- **THEN** the lock file records the holder `loop-20261108-b`
- **AND** the exit code is 0

#### Scenario: A different boot id marks the lock stale

- **GIVEN** the lock file records a boot id that differs from this boot
- **WHEN** `acquire` runs with the holder `loop-20261108-b`
- **THEN** the acquire clears the lock and takes it

#### Scenario: A start-time mismatch marks the lock stale

- **GIVEN** the lock file records a start time that differs from the running process
- **WHEN** `acquire` runs with the holder `loop-20261108-b`
- **THEN** the acquire clears the lock and takes it

### Requirement: The pre-flight stops on the halt file first

The pre-flight SHALL examine the `.claude/halt` file in the session root
or in the primary checkout before the peak window examination and the
lock. The run SHALL process no issue and SHALL report the stop when the
file exists.

#### Scenario: A halt file stops the run before the lock

- **GIVEN** the `.claude/halt` file exists in the primary checkout
- **WHEN** the run starts
- **THEN** the run takes no lock and processes no issue
- **AND** the run reports the stop

### Requirement: The status operator rows examine the loop

The `status` subcommand SHALL examine the loop components in a fixed
order. The first matched row SHALL decide the exit. The operator rows
SHALL run first: the halt file, the auth probe, the authors config, the
issue list, the blocked issues. The halt file SHALL sit at `.claude/halt`
in the working root or the primary checkout root. A failed
`gh auth token` probe SHALL decide the setup row. No token value SHALL
reach the output. A missing, unparsable, or wrong-shape authors config
SHALL decide the config row with exit 2 and the level `config`. The
blocked detection SHALL reuse the scan classification. The admission
gate SHALL run before the blocked test, so a refused foreign issue
with the `blocked` label gives no exit 2 from that issue.

#### Scenario: A halt file reports stopped

- **GIVEN** the `.claude/halt` file exists in the primary checkout root
  with `operator pause` on the first line
- **WHEN** the status runs
- **THEN** the exit code is 1 and the reason names `operator pause`
- **AND** no `gh` call runs

#### Scenario: A missing token reports setup

- **GIVEN** the `gh auth token` call exits non-zero
- **WHEN** the status runs
- **THEN** the exit code is 3
- **AND** no token value reaches the output

#### Scenario: A broken authors config reports a component error

- **GIVEN** the authors config does not parse
- **WHEN** the status runs
- **THEN** the exit code is 2 and the level is `config`

#### Scenario: A failed issue list reports a component error

- **GIVEN** the open-issue list call exits non-zero
- **WHEN** the status runs
- **THEN** the exit code is 2 and the reason names the failure

#### Scenario: A blocked issue reports a component error

- **GIVEN** an open issue carries the `blocked` label and no gate label
  above it
- **WHEN** the status runs
- **THEN** the exit code is 2
- **AND** the payload names the issue number and title

#### Scenario: A refused blocked issue stays out of the operator rows

- **GIVEN** an open issue carries the login `stranger` and the
  `blocked` label
- **WHEN** the status runs
- **THEN** the exit code is not 2 from that issue

#### Scenario: A handover label outranks a blocked label in status

- **GIVEN** an open issue carries the `handover` label and the
  `blocked` label
- **WHEN** the status runs
- **THEN** the exit code is not 2 from that issue
### Requirement: The status lock rows follow the operator rows

The lock rows SHALL run after the operator rows, and status SHALL
reuse the lock verdict with no holder and no session anchor. A fresh
lock SHALL give exit 0. A stale lock SHALL give exit 1 with the stale
rule as the reason. No lock SHALL give exit 1 as idle. A lock record
that the process cannot read SHALL give exit 2 with the read error. A
record that fails to parse SHALL stay in the stale row. A blocked
issue SHALL outrank a fresh lock.

#### Scenario: A fresh lock reports running

- **GIVEN** the lock file records a live holder
- **WHEN** the status runs
- **THEN** the exit code is 0

#### Scenario: A stale lock reports restartable

- **GIVEN** the lock file records a process id that no longer runs
- **WHEN** the status runs
- **THEN** the exit code is 1 and the reason names the stale rule

#### Scenario: No lock reports restartable

- **GIVEN** no lock file exists
- **WHEN** the status runs
- **THEN** the exit code is 1

#### Scenario: An unreadable lock reports a component error

- **GIVEN** the lock file exists and the process cannot read it
- **WHEN** the status runs
- **THEN** the exit code is 2 and the reason names the read error

#### Scenario: A blocked issue outranks a fresh lock

- **GIVEN** a blocked issue and a lock file with a live holder
- **WHEN** the status runs
- **THEN** the exit code is 2

### Requirement: The status output carries the level and the code

Plain mode SHALL print nothing on exit 0 and one reason line on stderr
on every other exit. The `--json` flag SHALL print one object on
stdout on every exit, with the level, the code, the reason, the
blocked entries, and the lock summary. The blocked entries SHALL carry
the number and the title of each blocked issue, or null. The lock
summary SHALL carry the lock state, the holder, and the matched rule,
or null. A component the examination did not reach SHALL carry null.

#### Scenario: The json payload carries the level and the code

- **WHEN** the status runs with `--json`
- **THEN** the output is one JSON object
- **THEN** the object carries the level, the code, the reason, the
  blocked entries, and the lock summary

#### Scenario: The plain mode stays silent on running

- **GIVEN** a fresh lock and no blocked issue
- **WHEN** the status runs without `--json`
- **THEN** stdout and stderr carry nothing

### Requirement: The scheduled-run recipe order

The scheduled run SHALL follow the recipe order: status, the action,
the peak-hours-gate command, the acquire, the scan, the oldest
actionable issue, and the release. The recipe SHALL run one issue per
fire. The recipe SHALL honor the halt file as the intentional stop.

#### Scenario: The recipe order runs status before the peak command

- **WHEN** the scheduled-run recipe runs
- **THEN** the status call comes before the peak-hours-gate command
  and the acquire

#### Scenario: The halt level stops the run silently

- **GIVEN** the status reports exit 1 from the halt row
- **WHEN** the scheduled run starts
- **THEN** the run takes no lock and reports nothing

### Requirement: The scheduled-run actions

The recipe SHALL stop quietly on exit 0, stop silently on the halt
level, proceed on the stale and idle levels, stop and report on exit 3
and on the issue-list, config, and lock rows, and proceed with a report
on the blocked row. The pipeline stop rules SHALL govern the issue work:
a fresh spec-carrying propose stops at the human spec gate, and the
other paths continue as the spec pins.

#### Scenario: A fresh spec-carrying propose stops at the gate

- **GIVEN** the oldest actionable issue is a fresh spec-carrying
  propose
- **WHEN** the scheduled run works it
- **THEN** the run stops at the human spec gate and releases the lock

#### Scenario: The blocked row proceeds and reports

- **GIVEN** the status reports exit 2 from the blocked row
- **WHEN** the scheduled run works the oldest actionable issue
- **THEN** the run proceeds, and the result names the blocked issues

#### Scenario: A config fault stops the scheduled run

- **GIVEN** the status reports exit 2 from the config row
- **WHEN** the scheduled run starts
- **THEN** the run stops and reports the config reason