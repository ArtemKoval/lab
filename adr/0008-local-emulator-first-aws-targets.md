# 0008 - Local emulator first for the crm AWS targets

- Status: proposed
- Date: 2026-10-30

## Context

The crm engine's week three milestones deploy the backend and the agent to AWS. They add a Lambda-style handler for the backend, an agent runtime, a gateway for the tools, and a memory. The engine must run in a devcontainer with no cloud account. A later change rolls the same stack out to a real account for a human to test.

## Decision

Every AWS target of the crm engine runs against a local emulator in development. One compose file starts the emulator with the services the targets need. The target addresses resolve from the same environment variables the real AWS rollout sets. Agent behavior tests stay hermetic on stand-ins, because the emulator's runtime data plane answers with canned payloads by design. The emulator is for wiring, not for behavior. The rollout change owns the real deploy and adds no second set of variables. Rejected options:

- Keep the deployment targets cloud-only and test them by hand. The devcontainer contract would break, and the rollout would carry untested wiring.
- Mock each service in pytest. The emulator already speaks the wire protocols, and a second mock would drift from it.

## Consequences

The development loop needs Docker for the runtime wiring only, and every behavior test stays hermetic. The rollout change provisions the real account with the same variable names, and a human tests the result. The emulator's canned data plane limits what the wiring tests can assert, so the payload shapes are pinned by the stand-ins this change ships.
