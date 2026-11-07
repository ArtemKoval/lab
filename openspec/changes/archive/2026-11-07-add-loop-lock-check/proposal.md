# Proposal: add-loop-lock-check

## Why

The Discipline section of the process-issues skill says: run one loop
invocation at a time. No mechanism enforces the rule, so two concurrent
runs can work the same issue and open duplicate pull requests. Proposal P1
of `reports/2026-11-07-issue-103-dsh-superagent-analysis.md` asks for a
lock in the manner of the dsh-superagent state lock. ADR 0012 rejected a
lock file for this rule because a stale lock wedges the loop worse than
the race it prevents. This change revisits that rejection with
liveness-based staleness and an operator release path, and a superseding
ADR records the new decision.

## What Changes

- `tools/process_issues` gains a loop lock. `acquire --holder LABEL`
  takes the lock behind one exclusive file create, and `release
  --holder LABEL` drops it on an exact label match. `release --force`
  is the operator escape for a lock whose holder is gone or hung. The
  acquire command enforces the lock. The scan exemption is cooperative.
- The lock file sits at `.process_issues/lock.json` under the primary
  checkout root, resolved from the git common directory. A non-git root
  uses the working directory instead. The record carries a schema version,
  the holder label, the host, the boot id, the process id, the process
  start time, and the acquire time.
- The `scan` subcommand examines the lock before the first `gh` call, and
  a refused scan makes no `gh` call. A fresh foreign lock exits 2 with the
  holder details on stderr. A scan with the label of the lock in force
  proceeds. The scan never writes the lock file.
- The lock is stale when the record does not parse, the schema version is
  unknown, the boot id differs from this boot, the recorded process id no
  longer runs, the recorded start time differs, or the acquire time is
  older than 24 hours. A stale lock draws a report on stderr, and the scan
  proceeds. `acquire` clears a stale lock and takes the lock.
- The CLI maps an argparse usage error to exit 64. Exit 0 stays success.
  Exit 2 stays the operational failure category: a failed `gh` call, an
  unreadable state directory, or a fresh foreign lock.
- The process-issues skill pre-flight follows the order: examine the halt
  file, examine the peak window, take the lock, scan. The holder label is
  unique per run. The run releases the lock at its end. A crashed session
  leaves the lock to the stale rules.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `process-issues`: the lock protocol, the halt pre-flight step, and the
  scan lock examination with the exit-64 usage rule.

## Out of scope

- No scheduled run and no status contract (P2).
- No admission gate on the intake (P3).
- No write-ahead ledger (P4).
- No heartbeat and no force take on acquire. A live but wedged holder
  needs the operator.
- The stale-clear race between two simultaneous acquirers stays a
  documented best-effort window.

## Impact

- `tools/process_issues/process_issues/`: a new `lock.py` module carries
  the record shape, the liveness inputs, and the stale judgment. The CLI
  gains the lock commands, the scan examination, and the exit-64 rule.
  `core.py` stays free of I/O.
- `tools/process_issues/README.md`: the Commands section gains the lock
  calls and the exit contract line.
- `tests/process_issues/` gains the lock cases, the exit-64 case, and the
  fake root resolver case.
- `.gitignore` gains `.process_issues/`.
- `.claude/skills/process-issues/SKILL.md`: the Discipline, Commands, and
  Pre-flight sections change.
- A new repository-level ADR supersedes ADR 0012 and restates the
  automation authority with the lock decision.
