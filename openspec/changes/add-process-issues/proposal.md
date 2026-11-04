# Proposal: add-process-issues

## Why

The operator files ideas as GitHub issues, then starts and tracks one pipeline run per issue by hand. A loop skill turns the open-issue list into a work queue and puts one human approval gate on each spec change.

## What Changes

- Add the `process-issues` capability. The loop scans the open issues and runs the `feature-pipeline` skill for one issue at a time. One invocation processes all eligible issues in `createdAt` order, and each issue advances to its next gate or its close. The loop runs on operator invocation, and no hook starts it. The loop examines the z.ai peak window before the first issue, and it stops with a message when the window blocks model-backed work.
- Add a stdlib CLI at `tools/process_issues/` with the house layout. The CLI has the `scan` subcommand and a `--json` flag. The `scan` subcommand lists the open issues, reads their labels, and reads their open pull requests with bodies and branch names. The CLI maps the labels, the pull request links, and the artifact presence to loop states. The skill owns the judgment classes and runs the pipeline steps. The CLI exits 0 on success and 2 on operational failure.
- The loop states follow one precedence rule. `handover` wins over `answered`, `answered` wins over `human-approved`, `human-approved` wins over `waiting-human-approval`, and `waiting-human-approval` wins over no label. An issue in the apply state with change artifacts resumes the apply phase. An issue in the apply state without change artifacts runs the propose phase and continues into the apply phase.
- The loop links each issue to its work. Each proposal PR body carries a `Refs #NN` line, and each branch name carries the change id.
- Gate only the spec-carrying changes. The loop runs the propose phase and merges the proposal PR. The loop then posts the spec references on the issue, adds the `waiting-human-approval` label, and leaves the issue open. The loop takes no further action on that issue until the `human-approved` label appears.
- A fix that restores intended behavior needs no spec. The loop runs its full pipeline, archive included, with no stop.
- The operator puts spec edits in the issue body or in a comment after the `waiting-human-approval` label. The operator adds the `human-approved` label. The loop folds the spec edits from the body and those comments into the change artifacts, and the newest text wins. The loop ignores its own comments. The loop runs the apply phase and the archive phase. The loop posts the results on the issue and closes the issue as completed.
- The loop treats a human issue and an agentic issue the same way. Both variants enter the propose phase. The loop drafts the specs from a free-form body. The loop transfers the spec content of a spec-carrying body into the change artifacts.
- The loop drives the pipeline steps with the issue as the review surface. Issue comments and labels take the place of the interactive approval steps. The proposal PR with the `waiting-human-approval` label takes the place of the plan approval step. The loop still runs the spec validation and the git discipline gates. The loop pauses the issue with a comment when the pipeline needs a decision that the issue has not answered.
- An informational issue changes no repo files. The loop posts an answer comment, adds the `answered` label, and leaves the issue open. The label stops a second scan.
- The loop skips an issue with the `handover` label, and it never closes that issue. A handover issue closes only by human hand.
- The change implementation creates the three labels first. The loop repairs a missing label before the first tag.
- A gate failure produces one issue comment with the failure output, and the comment names the failed gate. The loop continues with the next issue and does not retry in the same run. A propose phase failure leaves the issue unlabeled. An apply phase failure keeps the `human-approved` label. The next run resumes the failed phase from the change artifacts.
- The operator runs one loop invocation at a time. The skill text carries this rule as run discipline, and no lock mechanism enforces it.

## Capabilities

### New Capabilities

- `process-issues`: loop over open GitHub issues and run the feature delivery pipeline for one issue at a time. A label state machine with one precedence rule gates, resumes, or skips each issue.

### Modified Capabilities

- (none)

## Impact

- The tool follows the house layout: `tools/process_issues/process_issues/` with `core.py`, `cli.py`, and `__main__.py`, plus `pyproject.toml`, `ruff.toml`, and `README.md`. The tool uses the Python standard library only, and it adds no dependency to any venv.
- The CLI runs `gh` for the issue list, the labels, and the pull request states.
- The tests live at `tests/process_issues/` and run in the root suite. Each test file name stays globally unique. The tool joins the default quality gates: CRAP, duplication, and mutation.
- The CI workflow `tests.yml` gains the coverage source and the gate paths for the tool. The pinned substrings in `tests/claude_infra/test_ci_workflow.py` update with it. `.coveragerc` gains the omit line for `__main__.py`.
- `tools/project_setup/registry.json` gains a `gh-cli` unit. The unit uses `gh --version` for its test, and the install text names the platform paths. The `openspec-cli` unit already exists, and the pipeline uses it.
- The skill lands at `.claude/skills/process-issues/`. The `feature-pipeline` skill gets no edit. CLAUDE.md gains a Projects entry for `tools/process_issues`.
- The GitHub repo gains the labels `waiting-human-approval`, `human-approved`, and `answered`. The loop treats the `handover` label as read-only.
- `.claude/settings.json` gains allow rules for the `gh` commands that the loop runs: `gh issue list`, `gh issue view`, `gh issue comment`, `gh issue edit`, `gh issue close`, `gh label list`, `gh label create`, `gh pr list`, `gh pr view`, `gh pr create`, and `gh pr merge`. The list covers the reads of the loop, because no `gh` read rule exists in the settings today. The `gh pr merge` rule is a deliberate authority grant, and the ADR records it. The `update-config` skill owns the settings edit.
- An ADR records the automation authority of the loop at archive. The authority covers self-merged pull requests, issue closes, and the fix path without per-PR review.
- This change adds no harness registry entry, no `gates.yaml`, and no `rubrics/`. The dspy-gate system governs only the capabilities that the harness registry declares.
