# Design: add-crm-aws-context-copilot

## Source

The upstream briefs `docs/SECURE.md`, `docs/CONTEXT.md`, `docs/RUNTIME.md`, and `docs/COPILOT.md` at `week3day5-end` are the behavior source. The port order is `week3day2`, `week3day3`, `week3day4`, `week3day5`, one milestone commit each, run through `crm/port/port.py` and `crm/port/rewire.py`.

## Plan review

The seam comes from ADR 0007. This change adds three decisions of its own, reviewed against the port:

- The local AWS emulator stands in for the deployment targets. One compose file at `crm/deploy/compose.yaml` starts the emulator on port 4566. The runtime and gateway targets resolve from `CRM_AGENT_RUNTIME` and `CRM_GATEWAY_URL` exactly as real AWS would at rollout. The agent-behavior tests stay hermetic on stand-ins, because the emulator's runtime answers with canned payloads by design.
- The context server is the upstream `context/` package ported as `crm/context/`, serving the pack's governed files through the loader instead of its own folder. The file list moves into the pack manifest.
- The copilot's sign-off confirmation stays code, as upstream has it: the graph pauses, and the worker's confirmation card fires the recorded action.

## Key decisions

- The agent key: `CRM_AGENT_KEY` gates the agent routes. A request with both the key and a worker token is refused, as upstream has it.
- Memory: `CRM_MEMORY_ID` is optional. The memory client sits behind the same factory as the saver, so a run without memory works hermetically.
- The runtime entry points land at `crm/runtime/` as plain ASGI apps. The AgentCore-specific packaging stays out until the rollout change, which owns the real deploy.
- Send-back adds a status and a decisions table. The agent resumes a sent-back case with the note, and the old calculation is cleared.
- Langfuse stays optional behind its keys, as in change two.

## Mandated skills

One adversarial review round runs on the artifacts before the proposal pull request. Another runs on the diff before the merge, as in the changes before.

## Failure modes

- The key gate locks the tests out. The test client posts the key from a fixture, and the no-key refusal has its own test.
- The emulator drifts from the payloads the backend sends. The runtime stand-in pins the payload shape, and the compose file is exercised by the e2e gate variable only.
- The copilot fires a sign-off without confirmation. The graph's pause is a code path with its own test on the stub model.
