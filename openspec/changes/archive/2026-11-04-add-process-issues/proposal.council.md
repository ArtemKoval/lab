# Council Notes: proposal.md

## Author Summary

The author drafted the proposal with the four required sections, the new capability `process-issues`, and no modified capabilities. The draft carries the settled grill decisions. They cover the gate on spec-carrying changes only, the two label states, and the handover skip. They cover the informational path, the oldest-first order, and the mechanical scan CLI. The author added the `ensure-labels` subcommand, the settings allow rules, an ADR bullet, and a no-hook note beyond the settled list.

## Reviewer Challenges

- The draft named no loop states, no transition triggers, and no winner for contradicting labels.
- The claim that the `feature-pipeline` skill gets no edit left the unattended approval problem unsolved. The pipeline gates on interactive questions and plan approval.
- The draft named no link between an issue, its change directory, and its pull requests.
- The draft closed an issue after the apply phase and omitted the archive phase.
- The failure bullet left the in-run retry rule and the merge-failure class open, with a repeat-comment risk.
- The settings allow-rule bullet named no patterns and hid the `gh pr merge` authority grant.
- The single-invocation rule had no mechanism, and the draft stated no exit codes.
- The `ensure-labels` subcommand conflicted with the scan-only CLI role and gave one action two owners.
- A mid-window start could fail after the loop already changed issue state, because the peak-hours gate denies model-backed dispatches.
- The fold scope did not say which comments count and how conflicts resolve.
- The ADR bullet recorded the state policy that the spec already holds, and missed the durable automation-authority decision.
- The `gh-cli` unit needed its test command and a platform note, the order needed a sort key, and `reprocessing` broke the gerund rule.

## Resolutions

- Accepted: the states follow one precedence rule, `handover` over `answered` over `human-approved` over `waiting-human-approval` over no label. The apply state resumes only with change artifacts, and the spec delta will carry the full transition table.
- Accepted: the loop drives the pipeline steps with the issue as the review surface. Comments and labels take the place of the interactive approval steps, and the pipeline keeps its validation and discipline gates.
- Accepted: a `Refs #NN` line in each proposal PR body and the change id in each branch name link the work.
- Accepted: the loop runs the apply phase and the archive phase, and it closes the issue after the archive merge.
- Accepted: one failure comment per issue per run, no in-run retry, and a failed proposal PR merge counts as a gate failure. A propose phase failure leaves the issue unlabeled, and an apply phase failure keeps `human-approved`.
- Accepted: the Impact section names the exact allow-rule patterns, and the ADR records the `gh pr merge` grant.
- Accepted in part: the CLI exit contract is in the proposal. Rejected: a lock file. A stale lock wedges the loop worse than the race it prevents, so the single-run rule stays operator discipline.
- Accepted: the CLI stays read-only scan. The skill repairs a missing label with `gh label create`, and the change implementation creates the labels first.
- Accepted: the loop examines the peak window before the first issue and stops with a message.
- Accepted: the fold reads the body and the comments after the gate label, the newest text wins, and the loop ignores its own comments.
- Accepted: the ADR records the automation authority that covers self-merged pull requests, issue closes, and the fix path.
- Accepted: the unit test command, the platform note, the `createdAt` sort key, and the gerund rewrite.

## Remaining Risks

- The `gh pr merge` allow rule lets any session in this repo merge to main without a prompt. The ADR records the grant, and the two-label gate is the control.
- A persistently failing issue posts one failure comment per run, and no cap bounds the count.
- The single-invocation discipline relies on the operator, and no mechanism enforces it.
- The loop needs the push account active on the host, and the account switch is a host convention.
