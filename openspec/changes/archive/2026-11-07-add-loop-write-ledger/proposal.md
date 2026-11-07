# Proposal: add-loop-write-ledger

## Why

A loop run makes GitHub writes between two commands. A run can lose a
write: a label set, a comment posted, a merge done. Nothing records the
intent before the write, so a lost write gives a duplicate comment or a
missed step, and the repair action reads no record of the dropped
writes. Proposal P4 of
`reports/2026-11-07-issue-103-dsh-superagent-analysis.md` asks for a
write-ahead ledger. dsh stores each external write before it runs, and
this change ports that rule to the loop phases. The scheduled runs are
live, so no operator watches the loop, and the cost of a lost write
grew with them.

The report names the plan_exec ledger as the form to follow. The
plan_exec ledger is append-only and per-run scratch. The loop ledger
keeps the append-only form and gains a store that survives across runs.

## What Changes

### The ledger store

The CLI keeps the ledger at `.process_issues/ledger.jsonl`, beside the
lock file in the state dir that the git common directory resolves. A
run from a worktree shares the store with the primary checkout. The
store is append-only JSONL. An intent line carries `event`, `id`,
`kind`, `key`, and `at`. A confirmation line carries `event`, `id`, and
`at`. The `at` value is an ISO 8601 UTC time. The appends carry a
newline guard, so a torn append cannot glue onto the next record.

### The marker

Each intent gets one fresh marker id, in the form
`loop-<yyyymmddhhmm>-<4 hex>`, generated per write and never reused
from the holder label of the run. A comment embeds its marker at the
end of the body as `<!--process-issues:MARKER-->`, and the body still
starts with the fixed `process-issues loop` line, so the fold rule and
the loop-comment rule stay intact. The id generator takes the clock and
the random source as parameters, and the writer regenerates on a
collision with an existing id.

### The ledger command

The CLI gains the `ledger` command with a second positional action:
`write`, `confirm`, or `pending`. The parser choices give the usage
error exit 64 through the existing mapping. The exit contract is 0 on
success, 2 on an operational failure, and 64 on a usage error. The
operational failures are an unreadable store file and a confirm for an
unknown id. A missing store gives `write` a created store, `pending` an
empty list with exit 0, and `confirm` the unknown-id failure.

`ledger write --kind K --key N` generates the marker, appends the
intent, and prints the marker. The kind names the write family
(`comment`, `label`, `merge`, `close`). The key is the issue or pull
request number, or `number:label-name` for a label write. A write for a
group that already carries an unconfirmed intent prints one stderr
note, because a second live intent for one group is a recipe violation.

`ledger confirm --id MARKER` appends the confirmation line. A second
confirm for a confirmed id is a no-op with exit 0. `ledger pending
[--json]` prints the unconfirmed intents oldest first, with a
superseded flag per row: a row is superseded when a newer unconfirmed
intent of the same kind and key exists. The newest row of a group owns
the decision, and every unconfirmed marker of the group stays visible
for the reconcile scan. The JSON rows carry `id`, `kind`, `key`, `at`,
and `superseded`. The plain rows use tab separators. A line that is not
a valid event record is skipped with one numbered stderr note, and the
exit stays 0, because the ledger is an audit trail and a skipped line
degrades the run to the pre-change behavior with a visible trace.

### The recipe steps

The skill Phases section gains the ledger steps for every loop GitHub
write: the propose comment, the gate label, the result comment, the
issue close, and the informational, pause, and blocked writes. Before
each write, the phase runs `ledger write` and embeds the marker in the
write content. After the write exits 0, the phase runs `ledger
confirm`. The resume, repair, and start actions run `ledger pending`
first, so one uniform read serves all three.

For each pending comment intent, the phase fetches the issue comments
and tests each body for the literal marker string, without the GitHub
search endpoint. A found marker means the write landed, and the phase
confirms that marker. A missing marker on the newest row decides the
retry, and the retry repeats the write with the same marker, so no new
intent joins the group. A label intent retries as a plain re-add,
because the call is idempotent. A merge or close intent retries and
tolerates the already-done error, and the tolerated error confirms the
intent. A superseded intent that can no longer confirm stays in the
audit trail and out of the decision. The recipe runs every ledger
command under the run lock, and the single-writer rule is recipe
discipline in the plan_exec manner, so a manual call stays an operator
action outside the contract.

A ledger exit 2 mid-phase behaves like a gate failure: one comment
names the ledger fault, the phase stops, and the next run resumes from
the pending list. The stderr notes of skipped lines reach the run
report.

## Capabilities

### New Capabilities

None. The capability is the existing process-issues.

### Modified Capabilities

- `process-issues`: the write-ahead ledger for the loop writes, with
  the durable store, the `ledger` command and its three actions, the
  fresh per-write marker embedded in loop comments, the newest-wins
  decision with the full unconfirmed audit view, the skip rule for bad
  lines, the per-kind resume rules, and the ledger steps in the loop
  recipe.

## Out of scope

- No retries with backoff. A failed write stays pending, and the next
  run decides from the pending list.
- No effect queue and no dispatch worker. The phases stay the only
  writers.
- No marker reconciliation for non-comment writes. A label retries as
  a re-add, and a merge or close retries with the tolerated error.
- No ledger rotation or pruning. The file grows for the life of the
  clone, and the unknown future event values fall to the skip rule.
- No pending surface in `scan` or `status`. The status rows stay
  unchanged.
- No backfill of writes that ran before this change.
- No lock examination in the ledger commands. The single-writer rule is
  recipe discipline, in the plan_exec manner.
- No schema version field. The skip rule carries the forward
  compatibility.

## Impact

- `tools/process_issues/process_issues/ledger.py` (new): the store
  path from the lock state dir, the newline-guarded append, the read
  with the numbered skip notes, the pending view with the superseded
  flags, and the id generation over an injected clock and random
  source.
- `tools/process_issues/process_issues/cli.py`: the `ledger` command
  with the second positional action, the flag rules, and the exit
  mapping.
- `tools/process_issues/README.md`: the commands, the line shapes, the
  failure set, and the exit codes.
- `.claude/skills/process-issues/SKILL.md`: the Commands section, the
  Phases steps with the numbered ledger sub-list, the resume, repair,
  and start rules, the Failures line that names the pending list, and
  the comment fetch form for the reconcile scan.
- `tests/process_issues/test_process_issues_ledger.py` (new): the unit
  cases for the append, the read, the dedup, and the id generation.
- `tests/process_issues/test_process_issues_skill_guard.py`: the guard
  function for the Phases order and the Failures presence.
- The spec delta at
  `openspec/changes/add-loop-write-ledger/specs/process-issues/spec.md`:
  the ledger requirement and the recipe requirement.
- `tools/project_setup/registry.json`: no new unit, because the module
  ships inside the process_issues unit.
