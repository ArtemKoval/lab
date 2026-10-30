# Proposal: add-crm-domain-onboarding

## Why

The engine runs on domain packs, but onboarding a new domain is still hand-work. An author must know the manifest schema, the rules contract, the file layout, and the validation gates. The user's goal is to onboard from a free-form description. This change ships the skill that does it, the dev-box and rollout skills around it, and a second domain onboarded by the skill as proof.

## What Changes

- Add `crm/validate.py`. The stdlib CLI examines a pack against the contract, and exits 0 or 2 with named findings. The contract covers the manifest, the rules signature, the documents, the seed references, the eval decisions, and the instructions' tool names.
- Add `crm/smoke.py`. The runner seeds a temporary database from the pack, works three cases through the harness on the stub model, and prints the decisions. It makes no network call and needs no model key.
- Add `.claude/skills/crm-onboard-domain/`. The skill walks a free-form domain description through five steps: extract, generate, validate, smoke, and review. The new pack lands behind the engine's gates.
- Add `.claude/skills/crm-setup/`. It installs the dev box's needs: uv, the Python and Node sets through the registry, and the auth dev password file. It also runs the product locally.
- Add `.claude/skills/crm-aws-rollout/`. It rolls the stack out to a real AWS account and rolls it back, on the ADR 0008 variables, for a human to test.
- Onboard a second domain, `crm/domains/helpdesk/`, by walking the skill's own steps on a small IT-support description. Cases are tickets, awards are service credits, and the held-out decisions come from the support team's records.
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
