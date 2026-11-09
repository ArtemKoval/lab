# Tasks: add-setup-consent-mechanics

## 1. The code and the surfaces

- [ ] 1.1 Add `tools/project_setup_setup/project_setup_setup.py` with
      the validator, the plan builder, and the CLI, per the doctor
      contract in design.md.
- [ ] 1.2 Add the consent rules to
      `.claude/skills/project-setup/SKILL.md`, after the interview
      protocol.
- [ ] 1.3 Add the `project-setup-doctor` unit to
      `tools/project_setup/registry.json`, in the stdlib-only pattern.
- [ ] 1.4 Add the new directory to the gate lists in the workflow and
      the pin test, behind the operator acknowledgment line on the
      implementation pull request.
- [ ] 1.5 Add the doctor command to the Setup section of `CLAUDE.md`.

## 2. Tests

- [ ] 2.1 Add `tests/project_setup_setup/test_project_setup_doctor.py`
      with the validator, plan, install flow, readback mismatch,
      blanket refusal, unknown unit, and skill-rule guard tests.

## 3. Spec and delivery

- [ ] 3.1 Carry the delta-less declaration and pass the strict
      validate and the STE gate.
- [x] 3.2 Run the root suite, ruff, and the quality gates on the
      changed paths.
- [ ] 3.3 Commit, push, open the pull request, and merge after review.
