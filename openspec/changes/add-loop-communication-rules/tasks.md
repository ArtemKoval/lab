# Tasks: add-loop-communication-rules

## 1. The skill texts

- [ ] 1.1 Add the `Communication rules` section to
      `.claude/skills/feature-pipeline/SKILL.md` between Step 10 and
      Step 11, with the six rules.
- [ ] 1.2 Add the `Pick` bullet at the head of the Phases section of
      `.claude/skills/process-issues/SKILL.md`, with the fixed first
      line, the `On it:` line, the ledger wrap, the silence rule, and
      the informational exception.

## 2. Tests

- [ ] 2.1 Extend
      `tests/process_issues/test_process_issues_skill_guard.py` with
      the pick guard, and map the three delta scenarios to it: the
      object line to the `On it:` assertions, the fixed first line to
      the order assertion, and the silence rule to the
      progress-comment assertions.

## 3. Spec and delivery

- [ ] 3.1 Carry the spec delta and pass the strict validate and the
      STE gate.
- [ ] 3.2 Run the root suite, ruff, and the quality gates on the
      changed test path.
- [ ] 3.3 Commit, push, open the pull request, and merge after review.
