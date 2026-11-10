---
name: process-issues
description: Loop over the open GitHub issues and run the feature delivery pipeline for each issue, with a human spec gate between the propose phase and the apply phase. Use this skill when the operator asks to process the issues, to run the issue loop, to advance a gated issue, or to resume an approved spec. Gives the commands, the state rules, and the exit conditions.
---

# process-issues

The loop scans the open issues of this repo and runs the `feature-pipeline`
steps for one issue at a time, oldest first. The scan CLI lives at
`tools/process_issues/`, and the capability spec lives at
`openspec/specs/process-issues/`. The GitHub labels carry
the loop state, and the issue comments carry the decisions.

## Discipline

Run one loop invocation at a time. The loop lock enforces the rule: take
the lock before the first scan, and release it at the end of the run.
Build the holder label per run in the form `loop-<yyyymmddhhmm>-<4 hex>`.
The acquire command enforces the lock, and the scan examination is
cooperative. A stale lock never blocks: the scan reports it and proceeds,
and the next acquire clears it. Release the lock before the run stops at
the human spec gate, because the propose phase ends the run there.

## Commands

```bash
PYTHONPATH=tools/process_issues tools/zai_routing_audit/.venv/bin/python -m process_issues scan
PYTHONPATH=tools/process_issues tools/zai_routing_audit/.venv/bin/python -m process_issues scan --json
PYTHONPATH=tools/process_issues tools/zai_routing_audit/.venv/bin/python -m process_issues acquire --holder LABEL
PYTHONPATH=tools/process_issues tools/zai_routing_audit/.venv/bin/python -m process_issues release --holder LABEL
PYTHONPATH=tools/process_issues tools/zai_routing_audit/.venv/bin/python -m process_issues status
PYTHONPATH=tools/process_issues tools/zai_routing_audit/.venv/bin/python -m process_issues status --json
PYTHONPATH=tools/process_issues tools/zai_routing_audit/.venv/bin/python -m process_issues ledger write --kind K --key N
PYTHONPATH=tools/process_issues tools/zai_routing_audit/.venv/bin/python -m process_issues ledger confirm --id MARKER
PYTHONPATH=tools/process_issues tools/zai_routing_audit/.venv/bin/python -m process_issues ledger pending
```

Exit 0 on success, 2 on operational failure, and 64 on a usage error, with
the reason on stderr. The `--json` payload carries `number`, `title`,
`author`, `labels`, `state`, `action`, `prs`, and `changeDir` per issue. The status
command carries its own contract in the Scheduled run section: exit 0
running, exit 1 stopped or restartable, exit 2 component error, exit 3
waiting for setup, and its `--json` payload carries `level`, `code`,
`reason`, `blocked`, and `lock`.

## Scheduled run

The cron fires a session that runs the recipe once per fire. The recipe
runs one issue per fire, in this order:

1. Run `status --json`, and select the action from the level and the
   code.
2. Exit 0: stop quietly. A run holds the lock and owns the work.
3. Exit 1 from the halt row: stop silently. The halt file is the
   intentional stop, and the recipe reports nothing.
4. Exit 1 from the stale or idle row: proceed. The acquire clears a
   stale lock.
5. Exit 2 from the config, issue-list, or lock row, or exit 3: stop and
   report the reason. The scan would fail with the same fault, or the
   setup is missing.
6. Exit 2 from the blocked row: proceed, and report the named blocked
   issues with the run result. The loop never retries a blocked issue.
7. On proceed: run the gate command from the `peak-hours-gate` skill,
   and stop with a message when it denies.
8. Take the lock with `acquire --holder LABEL`, and stop and name the
   holder when the acquire refuses.
9. Run the scan with the same `--holder LABEL`.
10. Work the oldest actionable issue through the pipeline phases under
    their own stop rules. A fresh spec-carrying propose stops at the
    human spec gate. A propose-then-apply approval and the fix path
    continue under the rules the spec pins.
11. Release the lock, and report only exceptions.

The cron registers in the harness with the CronCreate tool after this
skill lands. The schedule is 08:00 and 20:00 Singapore time, written
`0 8,20 * * *` in Asia/Singapore, outside the peak window. When the
cron takes no timezone field, register `0 0,12 * * *`, the UTC
equivalents. The peak-hours gate stays the backstop, and the halt file
stays the intentional stop.

## Pre-flight

Examine the `.claude/halt` file in the session root or in the primary
checkout first. Stop the run with a message when the file stands. Examine
the z.ai peak window next, with the `check` command from the
`peak-hours-gate` skill. Stop the run with a message when the window blocks
model-backed work. Take the lock with `acquire --holder LABEL`. Stop the
run when the acquire refuses, and name the holder from the message. Run
the scan with the same `--holder LABEL`.

## States

The admission gate runs before the labels. An author outside
`process_issues/authors.json`, a login whose lowercase form ends with
`[bot]`, or an issue with no author maps to the state `refused` with the
action `none`, and the loop makes no change to a refused issue. The list
edits only through a pull request.

The scan maps each issue to one state and one action. The precedence is
`handover`, then `blocked`, then `answered`, then `human-approved`, then
`waiting-human-approval`, then no label. A `tech-debt:` title prefix or a
`tech-debt` label skips the issue. `handover` skips the issue.
`blocked` stops the issue: the loop never retries it. `answered`
takes no action. `waiting-human-approval` waits. `human-approved` applies
when the change artifacts exist, and proposes and then applies when they do
not. No label proposes, with `start` on an empty record, `resume` on an open
linked PR or artifacts, and `repair` on a merged linked PR.

## The blocked state

When a run cannot proceed on an issue, it writes one structured reason
comment on the issue, starting with the fixed line `process-issues loop`,
and sets the `blocked` label. The loop never retries a blocked issue, and
no other label moves it back into the rotation. Only the operator clears
the label, after reading the reason.

## Phases

For each actionable issue, oldest first:

- Pick. When the loop takes an actionable issue for a pipeline path,
  it posts one pick comment first. The fixed `process-issues loop`
  line stays the first line. The next line names the object and the
  expected result in the form `On it: <object and expected result>`.
  The ledger steps wrap the write. The loop posts one pick comment per
  issue. A resume confirms a posted pick through its ledger marker,
  with no second post. The loop posts no progress comment on the issue
  before the phase result. The informational path posts no pick
  comment. The answer comment serves that request.
- Propose phase (`start`, `resume`, `repair`, `propose-then-apply`). Derive
  the change id from the issue title with the house form `<type>-<kebab
  title>`. Run the propose steps: the change artifacts, the gates, the
  proposal PR with a `Refs #NN` line and the change id in the branch name,
  and the squash merge. Post the spec references on the issue, add the
  `waiting-human-approval` label, and stop that issue. On `repair`, skip the
  re-propose and repair the comment and the tag. On `resume`, continue the
  interrupted phase from the change artifacts.
- Apply phase (`apply`, `propose-then-apply`). Fold the human spec edits from
  the issue body and the comments posted after the gate label. The newest
  text wins. Loop comments start with the fixed line `process-issues loop`
  and stay out of the fold. Run the apply and archive steps, post the
  results, and close the issue as completed.
- Fix path. A fix that restores intended behavior needs no spec. Run the
  full pipeline, archive included, with no gate and no stop.
- Informational path. Post the answer comment, add `answered`, and leave the
  issue open.
- Pause path. Post the question when the pipeline needs a decision that the
  issue has not answered, and stop that issue. The state stays unchanged.

Ledger steps wrap every loop GitHub write, in every path above:

1. Before each GitHub write, run `ledger write --kind K --key N`. The
   kind carries the family (`comment`, `label`, `merge`, `close`). The
   key carries the issue or pull request number, or `number:label-name`
   for a label. Embed the printed marker at the end of a comment body
   as `<!--process-issues:MARKER-->`, behind the fixed
   `process-issues loop` first line.
2. After the write exits 0, run `ledger confirm --id MARKER`.
3. The `resume`, `repair`, and `start` actions run `ledger pending`
   first. For each pending comment intent, fetch the issue comments and
   scan the bodies for the literal marker string, without the GitHub
   search endpoint. Confirm every marker you find. Retry only a missing
   newest marker, with the same marker and no new intent. Retry a label
   as a plain re-add. Retry a merge or close and treat the already-done
   error as the confirmation.
4. The recipe runs every ledger command under the run lock. A ledger
   exit 2 mid-phase behaves like a gate failure, and the stderr notes of
   skipped lines reach the run report.

## Failures

A gate failure posts one comment that names the failed gate. The loop
continues with the next issue and does not retry in the same run. A propose
failure leaves the issue unlabeled. An apply failure keeps the
`human-approved` label. The next run resumes the failed phase from the
change artifacts. A failed write leaves its intent in the pending list,
and the next run reads it before any write.

## Labels

Repair a missing label before the first tag:

```bash
gh label create waiting-human-approval --description "Specs wait for human review" --color FBCA04
gh label create human-approved --description "Specs approved; run the apply phase" --color 0E8A16
gh label create answered --description "The loop answered this informational issue" --color 0E8A16
```

The label create call needs the label-write authority on the token.
