# Tasks: add-testing-lane-honesty

## 1. The skill texts

- [x] 1.1 Add the lane rule bullet to Step 3 of
      `.claude/skills/feature-pipeline/SKILL.md`, after the e2e
      bullet, with the two sentences.
- [x] 1.2 Add the lifecycle rule bullet to Step 9 of
      `.claude/skills/feature-pipeline/SKILL.md`, after the
      quality-gates paragraph, with the two sentences.

## 2. Tests

- [x] 2.1 Add `test_testing_lane_honesty_present` to
      `tests/claude_infra/test_pipeline_rules.py`, with one assertion
      per rule sentence.

## 3. Spec and delivery

- [x] 3.1 Carry the delta-less declaration and pass the strict
      validate and the STE gate.
- [x] 3.2 Run the root suite and ruff on the changed test path.
- [ ] 3.3 Commit, push, open the pull request, and merge after review.
