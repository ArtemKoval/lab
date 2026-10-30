# Proposal: add-crm-domain-onboarding

## Why

The engine runs on domain packs, but onboarding a new domain is still hand-work: an author must know the manifest schema, the rules contract, the file layout, and the validation gates. The user's goal is onboarding from a free-form description. This change ships the skill that does it, the dev-box and rollout skills around it, and a second domain onboarded by the skill as proof.

## What Changes

- Add `crm/validate.py`: a stdlib CLI that examines a pack — the manifest, the rules contract signature, the documents' front matter, seed referential integrity, eval decision legality, instruction tool names against the served tools, and domain nouns in engine code — and exits 0 or 2 with named findings.
- Add `crm/smoke.py`: a stdlib-driven runner that seeds a temporary database from the pack, works three cases through the harness on the stub model, and prints the decisions. No network, no model key.
- Add `.claude/skills/crm-onboard-domain/`: the skill walks a free-form domain description through extract, generate, validate, smoke, and review, and lands the new pack behind the engine's gates.
- Add `.claude/skills/crm-setup/`: installs everything a dev box needs for the crm engine (uv, Python and Node sets through the registry, the auth dev password file) and runs the product locally.
- Add `.claude/skills/crm-aws-rollout/`: rolls the stack out to a real AWS account and rolls it back, on the ADR 0008 variables, for a human to test.
- Onboard a second domain, `crm/domains/helpdesk/`, by walking the skill's own steps on a small IT-support description: cases are tickets, awards are service credits, and the held-out decisions come from the support team's records.
- Extend the `crm-app` skill and the registry for the new surfaces.

## Capabilities

### New Capabilities

- `crm-domain-onboarding`: The validator, the smoke run, and the skill that lands a new domain pack.
- `crm-aws-rollout`: The rollout and roll-down of the stack to a real AWS account on the ADR 0008 variables.

### Modified Capabilities

- `crm-domain-pack`: The pack contract grows the exact validation rules the validator enforces.

## Impact

- New `crm/validate.py` and `crm/smoke.py` (engine code, stdlib-only imports).
- New `crm/domains/helpdesk/` as the second pack, seeded and tested by the default suite.
- Three new skills, registry entries, and `.env.example` additions.
- The default suite runs the helpdesk pack's tests, so the engine's domain-genericity is regression-pinned.
