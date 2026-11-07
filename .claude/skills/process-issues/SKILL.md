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

Run one loop invocation at a time. No lock mechanism enforces the rule, so
the operator carries it.

## Commands

```bash
PYTHONPATH=tools/process_issues tools/zai_routing_audit/.venv/bin/python -m process_issues scan
PYTHONPATH=tools/process_issues tools/zai_routing_audit/.venv/bin/python -m process_issues scan --json
```

Exit 0 on success and 2 on operational failure, with the reason on stderr.
The `--json` payload carries `number`, `title`, `labels`, `state`, `action`,
`prs`, and `changeDir` per issue.

## Pre-flight

Examine the z.ai peak window before the first issue, with the `check`
command from the `peak-hours-gate` skill. Stop the run with a message when
the window blocks model-backed work.

## States

The scan maps each issue to one state and one action. The precedence is
`handover`, then `blocked`, then `answered`, then `human-approved`, then
`waiting-human-approval`, then no label. `handover` skips the issue.
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

## Failures

A gate failure posts one comment that names the failed gate. The loop
continues with the next issue and does not retry in the same run. A propose
failure leaves the issue unlabeled. An apply failure keeps the
`human-approved` label. The next run resumes the failed phase from the
change artifacts.

## Labels

Repair a missing label before the first tag:

```bash
gh label create waiting-human-approval --description "Specs wait for human review" --color FBCA04
gh label create human-approved --description "Specs approved; run the apply phase" --color 0E8A16
gh label create answered --description "The loop answered this informational issue" --color 0E8A16
```

The label create call needs the label-write authority on the token.
