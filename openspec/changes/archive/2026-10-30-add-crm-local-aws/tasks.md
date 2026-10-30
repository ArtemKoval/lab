# Tasks: add-crm-local-aws

## 1. The emulator and the gate

- [ ] 1.1 Extend `crm/deploy/compose.yaml`: the canned runtime acceptance, a fixed container name, and the invoke env the backend reads.
- [ ] 1.2 Write `crm/deploy/verify_wiring.py`: invoke the emulated runtime through `backend.runtime_calls` and and assert the acceptance. Exit 0 or 2.
- [ ] 1.3 Verify both against real Docker and the real emulator on this host, and record the commands run.

## 2. The skill and the wiring surface

- [ ] 2.1 Write `.claude/skills/crm-local-aws/SKILL.md`: readiness, up, variables, app start, the wiring gate, and the tear-down, with the honest boundary named.
- [ ] 2.2 Add the Docker feature to `crm/.devcontainer/devcontainer.json`, so compose runs from inside the container.
- [ ] 2.3 Extend `crm/.env.example` with the wiring variables and the emulator credentials note.
- [ ] 2.4 Cross-reference the skill from `crm-app` and `crm-setup`, and the README.

## 3. Delivery

- [ ] 3.1 Run the root suite, the crm suite, and ruff. Nothing proceeds on red.
- [ ] 3.2 Commit, push, and open the pull request.
- [ ] 3.3 Run the adversarial review on the diff, fix the confirmed findings, and merge, then archive through the archive pull request.
