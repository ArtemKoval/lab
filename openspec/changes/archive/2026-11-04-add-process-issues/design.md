# Design: add-process-issues

## Source

GitHub issue 86 names the loop skill and the two issue types. A grill round with the operator settled the forks. The gate covers spec-carrying changes only. Informational issues get an answer plus the `answered` label. One invocation processes all eligible issues oldest first. The adversarial council added the state precedence rule, the failure semantics, the work-link convention, and the automation-authority ADR topic.

## Plan review

The proposal went through grill-me and the adversarial-authoring council. The council raised 12 challenges. The accepted resolutions cover the label precedence rule and the unattended substitution mechanism. They cover the `Refs #NN` link convention, the close-after-archive rule, the failure semantics, and the exact allow-rule patterns. They cover the fold scope and the automation-authority ADR topic. The resolutions rejected the `ensure-labels` subcommand and the lock file. Gate 0 lint passes on the delta spec.

## Diagrams

### Container diagram

```
Operator ──invokes──> process-issues loop (skill, Claude Code session)
                          │
                          ├──scan──> process_issues CLI ──gh──> GitHub
                          │            (state per issue)        (issues, labels, PRs)
                          │
                          ├──per actionable issue──> feature-pipeline steps
                          │        (opsx propose/apply/archive, gates, PRs)
                          │
                          └──writes──> GitHub (comments, labels, closes, merges)
                                       and repo (openspec/changes/<id>/, branches)
Peak-hours gate ──denies──> model-backed dispatches in the window
```

### Component view

```
tools/process_issues/process_issues/
  core.py   classify(labels, pr_links, has_artifacts) -> state   pure logic, no I/O
  cli.py    scan subcommand, --json, exit 0/2    shells out to gh, reads artifact presence
  __main__.py shim
.claude/skills/process-issues/SKILL.md
  reads the scan queue, walks issues oldest first,
  runs the pipeline phases, posts comments, tags, closes
GitHub state store: labels hold the loop state, PRs link the work
```

## Decisions

- The GitHub issue is the state store. Labels hold the loop state, and pull requests link the work. No local database exists, so any clone can resume the queue.
- The label precedence rule is `handover` over `answered` over `human-approved` over `waiting-human-approval` over no label. The rule resolves every contradicting-label case with one reading order.
- The CLI stays read-only. It scans and classifies, and the skill owns every GitHub write and every judgment class. The division keeps the state machine testable without a model.
- The gate covers spec-carrying changes only. A fix that restores intended behavior runs with no stop, per the grill round.
- The work link is a `Refs #NN` line in the proposal PR body and the change id in the branch name. The link makes resume detection mechanical.
- The loop derives the change id from the issue title. The id takes the house form `<type>-<kebab title>`, and the type follows the work: `add` for new work, `fix` for a repair, and `chore` for upkeep.
- The judgment classes follow the pipeline rules. A change is spec-carrying when its behavior is visible outside one unit. A fix that restores intended behavior is not spec-carrying. An issue that changes nothing in the repo is informational.
- The loop replays the pipeline steps per issue in its own session. The opsx skills own the propose, apply, and archive steps, and the issue surface carries the approvals.
- The loop marks its own comments with a fixed first line. The fold reads the comments after the newest marked comment and orders them by their `createdAt` time.
- A gate failure posts one comment, continues with the next issue, and does not retry in the same run. A propose phase failure leaves the issue unlabeled, and an apply phase failure keeps `human-approved`. The next run resumes the failed phase from the change artifacts.
- The loop replaces the interactive approval steps with the issue surface. Comments and labels carry the decisions, and the pipeline keeps its validation and discipline gates. A missing decision pauses the issue with a comment.
- The loop examines the z.ai peak window before the first issue. A mid-window start stops before any state change.
- The `gh pr merge` allow rule is a deliberate authority grant. ADR 0012 records the automation authority.
- The single-invocation rule stays operator discipline with no lock mechanism. A stale lock would wedge the loop worse than the race it prevents.

## Failure modes

- `gh` is missing or fails, or the push account is not active. The scan exits 2 with the reason, and the skill stops the run with the same reason.
- The proposal PR merge fails. The run posts the gate-failure comment, leaves the issue unlabeled, and continues.
- The loop tags the issue, and the merge comment step fails. The next run finds the proposal PR merged and repairs the comment and the tag.
- The operator tags mid-run. The precedence rule resolves the state at the next scan, and the run finishes its current issue first.
- The fold finds conflicting edits. The newest text wins, and the comments of the loop stay out of the fold.
- The loop posts a question and the operator never answers. The issue stays paused, and the pause comment does not repeat because the loop ignores its own comments.

## Entropy (ASIT)

- Unification: the loop reuses `gh`, `openspec`, and the `feature-pipeline` skill. It adds no API layer and no issue-service abstraction.
- Multiplication: none. No copies of existing steps exist.
- Division: the pure classification lives in `core.py`, and the `gh` I/O lives in the CLI runner. The skill owns the judgment classes.
- Breaking symmetry: the CLI is read-only and the skill is write-side. The `handover` label makes handover issues an explicit rare path outside the loop.
- Object removal: the design removed the `ensure-labels` subcommand, the lock file, and the author-classification split. Both issue types converge on one propose phase.
- New components: one tool and one skill carry the capability, and the `gh-cli` registry unit covers the clean-clone contract. No other component is new.
