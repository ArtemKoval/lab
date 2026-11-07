# Proposal: add-loop-status-schedule

## Why

The loop advances only when the operator asks. An approved issue waits
for an operator prompt before the apply phase. The dsh-superagent
prototype runs an hourly task that repairs its agent and stays silent
when all is well. Proposal P2 of
`reports/2026-11-07-issue-103-dsh-superagent-analysis.md` asks for the
same shape. The shape is a status contract for the loop and a
scheduled-run recipe. The recipe advances the oldest actionable issue.
The operator chose the Claude Code cron. The schedule is 08:00 and
20:00 Singapore time, outside the peak window. The peak-hours gate
stays as the backstop.

## What Changes

### The status subcommand

`tools/process_issues` gains a `status` subcommand with the dsh
four-level contract: exit 0 running, exit 1 stopped or restartable,
exit 2 running with a component error, exit 3 waiting for setup. The
examination is a fixed table. The first match wins:

1. Halt file. A `.claude/halt` file in the working root or in the
   primary checkout root gives exit 1 with the first line of the file
   as the reason. Status makes no `gh` call in this row.
2. Auth probe. A failed `gh auth token` call, or a call that returns
   no token, gives exit 3. Status discards the stdout of the probe
   and prints no token value.
3. Issue list. A failed open-issue list call gives exit 2 with the
   `gh` reason. One list call with `number`, `title`, and `labels`
   serves this row and the next row.
4. Blocked issues. An open issue whose classification maps to the
   blocked state gives exit 2, and the payload names its number and
   title. The classification reuses the label precedence of the scan,
   so a handover label outranks a blocked label.
5. Fresh lock. Exit 0, no output. Status reuses the lock verdict with
   no holder and no session anchor, so any holder counts.
6. Stale lock. Exit 1 with the stale rule as the note.
7. No lock. Exit 1 as idle. A lock record that the process cannot
   read gives exit 2 with the read error.

The blocked row sits above the lock rows on purpose. The table answers
whether anything needs the operator before whether anything runs, in
the manner of the dsh stage table. Exit 0 says nothing, and a blocked
issue needs the operator, so a fresh lock with a blocked issue gives
exit 2. A record that fails to parse is not unreadable: it falls in
the stale row, and the acquire heals it, exactly as the lock spec
pins.

The auth probe uses `gh auth token`, not `gh auth status`. The token
call touches no network. A network outage then lands in the issue-list
row with exit 2. Only missing local credentials give exit 3. This
keeps the dsh line exact: a restart fixes neither 2 nor 3. A revoked
token that the probe still accepts surfaces as a failed list call in
exit 2, not in exit 3.

Status examines the lock after the `gh` probes. The scan keeps its own
order, lock first, because the spec pins it for the scan. Status is a
read-only diagnostic, and it needs the component facts under every
lock state. The blocked detection shares the 200-issue list bound of
the scan.

### The status output

Plain mode prints the reason on stderr and nothing on stdout. Exit 0
prints nothing. The `--json` flag prints one object on stdout on every
exit, with the fields the delta spec pins: the matched level, the exit
code, the reason, the blocked entries, and the lock summary. A
component the examination did not reach carries null. The status
contract defines its own exit codes. The scan contract stays as the
spec pins it.

### The scheduled-run recipe

The process-issues skill gains a Scheduled run section. The recipe
runs one issue per fire, in this order:

1. Run `status --json`, and select the action from the level and the
   code.
2. Exit 0: stop quietly. A run holds the lock and owns the work.
3. Exit 1 with the halt level: stop silently. The halt file is the
   intentional stop, and the recipe reports nothing.
4. Exit 1 with the stale or idle level: proceed. The acquire clears a
   stale lock.
5. Exit 2 from the issue-list row or the lock row, or exit 3: stop
   and report the reason. The scan would fail with the same fault, or
   the setup is missing.
6. Exit 2 from the blocked row: proceed, and report the named blocked
   issues with the run result. The loop never retries a blocked
   issue.
7. On proceed: run the peak-hours-gate command, and stop with a
   message when it denies.
8. Take the lock with `acquire --holder LABEL`, and stop and name the
   holder when the acquire refuses.
9. Run the scan with the same `--holder LABEL`.
10. Work the oldest actionable issue through the pipeline phases
    under their own stop rules. A fresh spec-carrying propose stops
    at the human spec gate. A propose-then-apply approval and the fix
    path continue under the rules the spec already pins.
11. Release the lock, and report only exceptions.

### The cron registration

The cron registers in the harness after the merge, and the skill
documents the registration step. The schedule is 08:00 and 20:00
Singapore time. When the cron takes no timezone field, the registered
times fall back to the UTC equivalents, 00:00 and 12:00, because
Singapore sits at UTC+8 with no daylight saving. Both fires sit
outside the 14:00 to 18:00 weekday window. The repository carries no
crontab, no timer unit, and no workflow for the schedule.

### The module placement

A new `status.py` sits under `tools/process_issues/process_issues/`.
The pure decision table takes the injected facts and returns the
level, the code, and the reason. The halt examination resolves the
primary checkout root through the same git common-directory
resolution as the state dir. `lock.py` stays unchanged. The CLI wires
the real probes through the existing runner seam, the state-dir
resolution, and the lock inputs.

## Capabilities

### New Capabilities

None. The capability is the existing process-issues.

### Modified Capabilities

- `process-issues`: the `status` subcommand with the four-level exit
  contract, the output shape, and the scheduled-run recipe with the
  per-level action table.

## Out of scope

- No automatic repair of a failed run. The recipe reports and stops,
  and the next scheduled run resumes from the change artifacts.
- No peak-window mathematics in the status command. The window is a
  clock condition that ends without a repair, and the gate command
  and the hook own the window.
- No scheduler state in the repository. The cron lives in the
  harness.
- No change to the scan exit contract, to `lock.py`, or to the scan
  order of lock before the first `gh` call.
- No writes in the status command. Status makes no GitHub write and
  no notification.

## Impact

- `tools/process_issues/process_issues/status.py` (new): the pure
  level table and the exit decision over injected inputs.
- `tools/process_issues/process_issues/cli.py`: the `status` command
  in the parser choices and the wiring over the runner seam.
- `tests/process_issues/`: the table cases in a new
  `test_process_issues_status.py`, the CLI cases with fake runners,
  and the recipe rows in the skill guard test.
- `.claude/skills/process-issues/SKILL.md`: the Commands section, the
  Discipline section, the Pre-flight section, and the new Scheduled
  run section with the action table and the cron registration step.
- `tools/process_issues/README.md`: the status contract.
