# Tasks: add-crm-domain-onboarding

## 1. The validator

- [ ] 1.1 Write `crm/validate.py`: one named check per contract rule, over the manifest, the rules contract, the documents' front matter, the seed references, the eval decisions, the instruction tool names, and the file names.
- [ ] 1.2 Write the validator's tests, including a deliberately broken pack fixture per check.
- [ ] 1.3 Fold the checks into the pack spec's wording, so the spec and the validator agree.

## 2. The smoke run

- [ ] 2.1 Write `crm/smoke.py`: seed a temporary database, work three cases on the stub model, print the decisions.
- [ ] 2.2 Write the smoke run's test, asserting no network and no model key.

## 3. The skills

- [ ] 3.1 Write `.claude/skills/crm-onboard-domain/SKILL.md`: the five steps, the gates at each, and the human review of the held-out decisions.
- [ ] 3.2 Write `.claude/skills/crm-setup/SKILL.md`: the dev-box install and the local run.
- [ ] 3.3 Write `.claude/skills/crm-aws-rollout/SKILL.md`: the readiness checks, the up path, the failed-step stop, and the down path.
- [ ] 3.4 Update the `crm-app` skill, the registry, and `.env.example` for the new surfaces.

## 4. The second domain

- [ ] 4.1 Draft the helpdesk description and walk the skill's steps on it: manifest, rules, documents, seeds, instructions, evals.
- [ ] 4.2 Write the helpdesk pack's own tests: seed, decisions, and the noun guard with `CRM_DOMAIN=helpdesk`.
- [ ] 4.3 Run the validator and the smoke run on the helpdesk pack and record the output.

## 5. Delivery

- [ ] 5.1 Run the crm suite, the root suite, and the gate tools, and raise the coverage floor to the new total.
- [ ] 5.2 Commit, push, and open the pull request.
- [ ] 5.3 Run the adversarial review on the diff, fix the confirmed findings, and merge, then archive through the archive pull request.
