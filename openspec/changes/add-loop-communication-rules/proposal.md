# Proposal: add-loop-communication-rules

## Why

The loop posts gate comments, result comments, answers, and question
comments, but no rule pins the traffic shape beyond the fixed first
line. A person who reads an issue sees no acknowledgement that names
the object of the work. No rule keeps the loop quiet while the phases
run. Proposal P5 of
`reports/2026-11-07-issue-103-dsh-superagent-analysis.md` requests the
communication discipline. The report requests one concrete
acknowledgement per request, one sentence of reason for a declined
suggestion, and silence while the work runs. The scheduled runs are
live, so no operator watches the loop, and the traffic rules carry
their weight there. The report says this lab starts with the written
rules, and a later change can add a mechanical limit.

## What Changes

### The communication rules in the feature-pipeline skill

The skill gains one `Communication rules` section between Step 10 and
Step 11. The section carries six rules:

- the `On it:` acknowledgement form with the object and the expected
  result
- the ban on the plan sentence without an object
- silence while the work runs
- the silent resolution of a fixed and verified review thread
- one sentence of reason for a declined suggestion
- the unfinished label for a draft

### The acknowledgement in the process-issues skill

The Phases section gains one `Pick` bullet at its head. When the loop
takes an actionable issue for a pipeline path, it posts one pick
comment first. The comment carries one `On it:` line behind the fixed
`process-issues loop` first line. The line names the object and the
expected result. The ledger steps wrap the write. The loop posts one
pick comment per issue, and it posts no progress comment before the
phase result. The informational path posts no pick comment, because
the answer comment serves that request.

## Capabilities

### New Capabilities

None. The capability is the existing process-issues.

### Modified Capabilities

- `process-issues`: the pick acknowledgement, with the `On it:` line
  form, the one-comment-per-issue rule, the silence rule before the
  phase result, and the informational exception.

The feature-pipeline skill is a harness surface and carries no
capability spec, so the delta touches `process-issues` only.

## Out of scope

- No mechanical word budget and no code gate on comment length. The
  report defers the dsh budgets to a later change.
- No reply-gate machinery and no purpose classification. The written
  rules approximate the purpose line, and no code examines it.
- No new comment kind beyond the pick comment. The gate, result,
  answer, question, and blocked comments keep their rules.
- No change to the fold rule. The pick comment is a loop comment
  behind the fixed first line, and it stays out of the fold.
- No ledger change. The live spec wraps every loop GitHub write in the
  ledger steps, and the pick comment is one of those writes.
- No README change. The CLI has no new command.
- No registry unit. The change adds no installable unit.

## Impact

- `.claude/skills/feature-pipeline/SKILL.md`: the `Communication
  rules` section between Step 10 and Step 11, with the six rules.
- `.claude/skills/process-issues/SKILL.md`: the `Pick` bullet at the
  head of the Phases section.
- `tests/process_issues/test_process_issues_skill_guard.py`: the pick
  guard with one assertion per delta scenario.
- The spec delta at
  `openspec/changes/add-loop-communication-rules/specs/process-issues/spec.md`:
  the acknowledgement requirement.
- `tools/project_setup/registry.json`: no change. The change adds no
  installable unit.
- No code module. The CLI, the README, and the registry stay
  unchanged.
