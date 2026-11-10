# Design: add-pipeline-fast-mode

## Plan review

The clarifying interview ran as a three-fork question round, and the
user answered every fork. The forks: activation through the `fast:`
prefix, a pull request merged on a green local run, and one debt issue
per run.

The review consulted the prior lessons. The merge rule follows the
recorded discipline that the suite run, the diff read, and the merge
stay separate calls. Fast mode keeps the local suite run as the merge
bar, so the rule holds. The mainline branch has no protection rule
(observed on 2026-11-10), so the merge rule is executable as written.

ASIT: Object Removal and Unification. The mode removes steps from the
existing pipeline. The debt record reuses the issue template
machinery that the handover template established. The guard tests
extend `tests/claude_infra/test_pipeline_rules.py`, the file the
P4 change established. The activation reuses the existing arguments
channel of the skill invocation. No new tool, hook, registry unit, or
skill enters the repository. The issue template is one new file beside
the handover template, the same kind of component.

The author round examined the drafts and confirmed one blocking gap.
The process-issues classifier maps an issue with no label, no linked
pull request, and no artifacts to the start action
(`tools/process_issues/process_issues/core.py` line 74). A debt issue
matches that shape, so the loop would treat it as new work. The
classifier skip rule below closes the gap. The reviewer challenge
followed the revised drafts, and this file carries its accepted
findings.

Assumptions for the diagram: ASCII format, lightweight C4-inspired
rigor. The user did not pick a format for this speed-first change.

## The fast-mode flow

```
              invocation
                  |
         args start with fast: ?
             /              \
          no                 yes
           |                  |
      full flow           fast mode
      (all steps)         skips: spec artifacts,
           |              new test matrix, quality
      proposal PR         gates, agent dispatches
           |                  |
         merge          local suite run + smoke
           |            run + secret diff scan
      archive PR             |
           |                 |
       handover         debt issue opens, then
        issue           PR merges on the green
           |            local run, CI runs after
        (done)              |
         |             one tech-debt issue
        (done)         per run stays open
```

- The invocation boundary is the only switch. One prefix, one mode,
  no mid-run change.
- Fast mode keeps the branch, the pull request, the smoke run, the
  diff secret scan, and the local suite run. The run merges when the
  local suite is green. CI runs after the merge and confirms the
  result.
- The debt issue closes the loop: every skip carries a next action,
  and a normal-pipeline run pays the debt.
- Fast mode runs the plan review and the result review inline in one
  agent. It makes no agent dispatches, so the peak-hours window does
  not block its dispatch path.

## The rule texts

The skill gains a Fast mode section after the intro, before the
cross-cutting rules:

- Activation: the `fast:` prefix in the arguments selects fast mode
  for one invocation. Runs without the prefix keep the full flow.
- Skip set: the spec artifacts (Step 1.5), the new test matrix and
  the coverage target (Step 3), the quality gates (crapper, dryer,
  mutator, complexity), and the multi-agent review (Step 12). A
  skipped step that applies to the task becomes one debt item. A step
  that does not apply is not a skip.
- Keep set: the branch and the pull request (Step 1), the smoke run,
  the `sec-scan --diff` scan, the local suite run, and the reduced
  Step 13: open the debt issue, merge, delete the branch, and resync
  the mainline.
- Debt issue: the run opens one technical debt issue from the
  `tech-debt` template before the merge. The issue lists every skip
  with a next action and stays open until a normal run pays the debt.
  The pull request body carries `fast-mode: <issue-url>`. The pull
  request body does not carry a close keyword for the debt issue.
  The issue carries one item for the unwaited CI run. The next action
  names the post-merge CI run and the fix on a red result.
- Fast mode skips Steps 4, 6, and 7 (MCP tool, README, CLAUDE.md)
  under the same applies rule as the skip set.
- Handover: the debt issue replaces the handover issue in fast mode.
  The `## Task` section of the debt issue carries the pull request
  link and the run observations. The `## Telemetry` section carries
  the handover-telemetry block when the run produced observations
  later work can use.
- Governed capabilities: a fast task that touches a capability in the
  dspy-gate harness registry runs the normal flow. The spec gates
  need the artifacts that fast mode skips.

The template at `.github/ISSUE_TEMPLATE/tech-debt.md` mirrors the
handover template shape: `name: Tech debt`, the sections `## Task`,
`## Telemetry`, `## Debt items`, and `## Follow-ups`, the house
comments, and the Write None convention. The title always carries the
`tech-debt:` prefix. The classifier rule matches the prefix, not the
label alone. GitHub drops a frontmatter label that does not exist in
the repository. The frontmatter lists the `tech-debt` label for the
time after the operator creates it.

CLAUDE.md gains one Workflow line that names the prefix and the debt
issue: `A \`fast:\` prefix run opens the debt issue instead of the
handover issue.`

## The classifier rule

The process-issues classifier maps an issue with no known label and
no linked pull request to the start action. A debt issue matches that
shape without the rule. The change adds one rule to `classify` in
`tools/process_issues/process_issues/core.py`. The signature gains an
optional `title` keyword. A title that starts with `tech-debt:` maps
to the skip state and the none action. The rule also matches the
`tech-debt` label when the operator creates it. The rule sits after
the waiting branch and before the pull-request branches. The CLI at
`cli.py` passes the title. A unit test in
`tests/process_issues/test_process_issues_core.py` pins the rule, and
the README gains one line for it. The label table and the approval
branches keep their precedence over the rule.

## Edge cases

- A fast run with no skipped steps writes the CI item alone in the
  debt items section.
- A later normal run pays a debt item. The paying run links its pull
  request in the item and removes the item line. The paying run
  closes the issue when the `## Debt items` section shows None.
- A fast run on a task that touches a protected gate path still
  carries the `gate-integrity: acknowledged` line in the pull request
  body. The guard test runs in CI, and fast mode does not weaken it.
- Branch protection can hold a merge until CI finishes. When
  protection holds the merge, the run waits for the green CI result
  and writes no debt item for the CI wait.
- A fast pull request can close without a merge. The template tells
  the reader to close the linked debt issue with the reason.
- The normal run that pays the debt dispatches agents. That run
  starts outside the peak-hours window, or with the override.

## Verification

`tests/claude_infra/test_pipeline_rules.py` gains guard tests: one
assertion per rule sentence on the collapsed skill text, one
assertion per template section, and one assertion for the Workflow
line in `CLAUDE.md`. A removal fails the suite.
`tests/process_issues/test_process_issues_core.py` gains one unit
test for the title-prefix skip. The tasks carry the validate and STE
gate runs on the change directory, and the quality gates on the
changed classifier path.
