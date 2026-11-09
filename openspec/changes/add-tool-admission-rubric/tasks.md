# Tasks: add-tool-admission-rubric

## 1. The skill text

- [x] 1.1 Add the admission rubric bullet to Step 2 of
      `.claude/skills/feature-pipeline/SKILL.md`, after the
      remediation rule, with the two sentences.

## 2. Tests

- [x] 2.1 Add `test_tool_admission_rubric_present` to
      `tests/claude_infra/test_pipeline_rules.py`, with one assertion
      per rule sentence.

## 3. Spec and delivery

- [x] 3.1 Carry the delta-less declaration and pass the strict
      validate and the STE gate.
- [x] 3.2 Run the root suite and ruff on the changed test path.
- [ ] 3.3 Commit, push, open the pull request, and merge after review.
