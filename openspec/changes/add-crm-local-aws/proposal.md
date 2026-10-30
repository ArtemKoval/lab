# Proposal: add-crm-local-aws

## Why

The engine's AWS targets run against the local emulator in development (ADR 0008), but nothing joins the steps: the devcontainer has no Docker access, the emulator's answers don't match what the backend's runtime caller accepts, and no skill walks "run the app with the AWS wiring live". This change ships that skill and makes the wiring actually verifiable.

## What Changes

- Add `.claude/skills/crm-local-aws/`: the skill that starts the emulator, creates the emulated runtime, points the variables at it, starts the app, verifies the wiring end to end, and tears it back down.
- Extend `crm/deploy/compose.yaml`: the emulator answers a runtime invoke with the acceptance the backend reads, and the container gets a fixed name.
- Extend `crm/.devcontainer/devcontainer.json`: a Docker feature, so compose runs from inside the container.
- Add `crm/deploy/verify_wiring.py`: a small script that invokes the emulated runtime through the backend's own `runtime_calls` and asserts the acceptance. The skill's gate runs it.
- Extend `crm/.env.example` with the AWS wiring variables and the emulator credentials note.

## Capabilities

### New Capabilities

- `crm-local-aws`: The skill and the gate that run the app with the AWS wiring pointed at the local emulator.

### Modified Capabilities

## Impact

- `crm/deploy/compose.yaml` and `crm/.devcontainer/devcontainer.json` change.
- New skill directory and `crm/deploy/verify_wiring.py`.
- `.env.example` and the `crm-app` and `crm-setup` skills gain cross-references.
- No engine code changes: the bridge is boto3's native `AWS_ENDPOINT_URL`.
