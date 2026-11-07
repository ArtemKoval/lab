# Proposal: add-loop-admission-gate

## Why

This repository is public. Any GitHub account can open an issue, and the
scan admits every open issue into the loop rotation. A stranger can start
model-backed work this way, and the work costs tokens and attention.
Proposal P3 of `reports/2026-11-07-issue-103-dsh-superagent-analysis.md`
asks for the admission gate. dsh-superagent keeps an allowed list per
source. An unlisted person gets nothing by default, and a bot never
passes the gate as a person. This change ports that rule to the loop
intake.

## What Changes

### The refused state

The scan examines the issue author against the allowed-author list
before the label precedence. An author outside the list maps to the
state `refused` with the action `none`. The refusal sits above every
label state, because the gate runs before any assessment and fail-closed
tells the operator more than skip. The observables differ from skip: the
`--json` state and action say `refused` and `none`, the plain output
prints `refused`, and the entry carries the author. A foreign issue with
the `human-approved` label and change artifacts then maps to refused,
and the loop never folds stranger content. A foreign issue with the
`blocked` label then stays out of the status operator rows, and a
stranger cannot buy operator attention with labels.

The loop makes no change to a refused issue. The loop posts no comment,
adds no label, and closes nothing. Refused entries keep scan exit 0. The
refusal is a classification, not a failure.

### The allowed-author list

The list ships with the module at
`tools/process_issues/process_issues/authors.json`. The file shape is
one JSON object: `{"allowed_authors": ["ArtemKoval"]}`. The scan
resolves the path against the module file through one injectable path
constant, so the tests point it at a fixture file and a worktree cwd
cannot break the resolution. An empty list is a valid shape and refuses
everyone. The comparison is case-insensitive, because GitHub logins are
case-insensitively unique. The operator edits the list through a pull
request, so the list stays code-tracked.

### The bot rule

A login whose lowercase form ends with `[bot]` refuses, even when the
list names it. GitHub renders the shadow accounts of GitHub Apps with
that suffix in the login, and a human login cannot contain brackets, so
the rule cannot refuse a person. The rule reads the login string only.

### The config failure

A missing, unparsable, or wrong-shape authors config is an operational
failure, not missing setup. The file ships in the clone, so its absence
is a broken deployment, and a restart fixes it only when the clone
repairs. Exit 2 fits that line better than exit 3. The scan prints one
stderr note that names the config path, exits 2, and prints no queue.
The scan reads the config after the lock examination and before the
first `gh` call. The required shape is `allowed_authors` as a list of
strings, with extra top-level keys ignored.

### The scan output

The issue fetch gains the top-level `author` field, and the code reads
`author.login`, because `gh` returns an object. Every `--json` entry
carries the login string, or null when the payload carries no author
object. A null or absent author refuses, in the fail-closed direction.
The plain output stays unchanged except the refused state column. Tests
pin the field list of both fetches, because a forgotten `author` field
produces a silent full refusal.

### The status rows

Status gains three small changes that keep its spec sentence true: the
issue-list fetch gains the `author` field, the blocked detection applies
the same refusal before the label test through one author-aware
predicate, and a new config row sits between the auth row and the
issue-list row with the level `config` and exit 2. A refused foreign
issue with the `blocked` label gives no exit 2, because admission
refusal is not operator attention. Status gains no refused row, and the
payload keys stay the same.

### The loop account and the recipe

The loop account gets no special list entry. The operator entry already
admits the account that files the handover issues, so handover intake
needs the allowed account. A future dedicated loop account with a
`[bot]` login stays refused with no code change, and its handover issues
report refused with the action none. The scheduled-run recipe needs no
new step, because a config fault is an exit-2 component error and the
recipe already stops and reports on that category. The skill and README
texts gain the new row, the payload key, the refusal rule, and the list
edit path.

## Capabilities

### New Capabilities

None. The capability is the existing process-issues.

### Modified Capabilities

- `process-issues`: the author admission gate with the refused state
  above the label precedence, the shipped allowed-author list with the
  fail-closed config rule at exit 2, the `[bot]` suffix rule, the
  `author` field in the scan payload, the config row in the status
  order, and the refusal before the status blocked test.

## Out of scope

- No comment, label, close, or notification on a refused issue. A
  stranger gets nothing, in the manner of dsh.
- No per-source or per-author admission cells with strength levels. One
  repository takes one flat list.
- No gate on pull request authors. A foreign pull request with a
  `Refs #NN` line stays outside this change.
- No server-side author filter and no fetch-limit raise. An issue flood
  can put older issues outside the 200-issue fetch window. A later
  change can address that residual.
- No reliance on a `gh` bot field. The suffix rule reads the login
  string only.

## Impact

- `tools/process_issues/process_issues/core.py`: the `STATE_REFUSED`
  constant and the pure admission predicate over the login, the allowed
  set, and the bot suffix. Core stays free of I/O.
- `tools/process_issues/process_issues/authors.py` (new): the
  module-relative config path constant, the load, and the shape
  validation.
- `tools/process_issues/process_issues/authors.json` (new): the list
  with the operator login.
- `tools/process_issues/process_issues/cli.py`: the `author` field in
  both issue fetches, the `author` key in each queue entry, the config
  read between the lock and the first `gh` call, the refusal in the
  queue walk, and the config row and refusal in the status path.
- `tests/process_issues/`: the admission cases, the bot suffix cases,
  the case-insensitive list case, the no-author case, the config
  failures for scan and status, the fetch field-list pins, and the
  regression case that proves the allowed path leaves every existing
  classification and the plain line format unchanged.
- `tools/process_issues/README.md`: the refused state row, the config
  path, the exit-2 line, and the status table row.
- `.claude/skills/process-issues/SKILL.md`: the States section, the
  payload key list, the Scheduled run stop list, and the list edit path
  through a pull request.
- The spec deltas under
  `openspec/changes/add-loop-admission-gate/specs/process-issues/`:
  the scan-classification requirement, the scan-CLI queue requirement,
  the status operator-rows requirement, and the scheduled-run actions
  requirement.
- `tools/project_setup/registry.json`: no new unit, because the config
  ships inside the process_issues unit directory.
