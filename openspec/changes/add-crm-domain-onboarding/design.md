# Design: add-crm-domain-onboarding

## Source

The onboarding design was settled by the change-1 tournament and ADR 0007: the skill extracts a domain model from the description, generates the pack, validates, smokes, and hands the held-out decisions to a human. ADR 0008 owns the rollout variables this change's rollout skill walks.

## Plan review

One adversarial review round runs on the artifacts before the proposal pull request, and one on the diff before the merge. The implementation itself uses a workflow for the parallelizable pieces: the second domain's pack draft, the three skill documents, and an adversarial pass on each.

## Key decisions

- The validator is one stdlib module at `crm/validate.py` with one named check per contract rule, so the skill's generate step can run it in a loop until clean. It never imports the engine's FastAPI app; it imports the loader and the rules module only.
- The smoke runner reuses the harness's own stub model and the pack's own seed, in a temporary database, so what it proves is exactly what a dev run would do.
- The second domain is an IT-support helpdesk: tickets with service-credit awards, support plans, the support team's held-out decisions. It is small (three cases, two workers, one plan tier) but carries every artifact the contract requires, so it proves the seam without doubling the suite's runtime.
- The rollout skill carries a checklist of commands, not Terraform: the engine's AWS surface is two Lambda-style apps plus the variables, and the human tests it, so the checklist keeps the account inspectable.
- The skill never edits engine code; a domain that needs new engine behavior is an engine change, not an onboarding.

## Failure modes

- A generated pack drifts from the schemas. The validator names the file and the field, and the skill loops on it.
- The second domain's tests duplicate the insurance pack's wholesale. They pin only the helpdesk's own decisions, through the same helpers.
- The rollout checklist rots against the account. Each step's command prints what it will do before it runs.
