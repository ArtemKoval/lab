# Proposal: add-crm-aws-context-copilot

## Why

The engine now holds the queue, the swarm, and the improver, but it runs only as a dev stack. It has no guard against injected instructions, no enterprise context layer, no deployment target, and no assistant for the workers. The upstream week three milestones add all four. This change ports them with the AWS targets running against the local emulator first.

## What Changes

- Port milestone `week3day2` as security. An API key gates the agent's routes, and a screening step refuses injected instructions. The backend gains a Lambda-ready handler, and the pack seeds the injection case.
- Port milestone `week3day3` as the context layer. An MCP server serves the pack's governed files, and every context step carries its sources. The agent gains a memory and direct or gateway tool routing.
- Port milestone `week3day4` as the runtime. The agent becomes an AgentCore-style app with a heartbeat, and the backend invokes it as a service or a runtime. A held case takes a sign-off or a send-back.
- Port milestone `week3day5` as the copilot. A worker's chat app has its own graph and tools, keeps conversations and turns in the database, and docks in the dashboard sidebar.
- Wire the local AWS emulator for the runtime targets. One compose file starts it, and the runtime targets resolve by environment. Real AWS stays behind the same variables for the rollout change.
- Keep every test hermetic. SQLite runs locally, stand-in servers take the agent, the context, the judge, and the auth service, and a stub model stands in for OpenRouter.

## Capabilities

### New Capabilities

- `crm-secure`: The agent key gate, the screening step, and the Lambda-ready handler.
- `crm-context`: The MCP context server, sources on context steps, memory, and tool routing.
- `crm-runtime`: The agent app, the heartbeat, runtime invocation with a local emulator, and send-back.
- `crm-copilot`: The worker chat, its tools, and the conversation records.

### Modified Capabilities

- `crm-engine`: The case page carries send-back decisions, and a held case returns to its agent or waits for a worker to take it.

## Impact

- `crm/backend` gains the API key gate, the screening route, the Lambda handler, send-back, and the copilot and conversation routers.
- `crm/agent` gains screening, the context tools, memory, the AgentCore-style app, the heartbeat, and the copilot subpackage.
- `crm/context` is a new MCP server package over the pack's governed files.
- `crm/runtime` and `crm/deploy` hold the runtime entry points and the local emulator compose file.
- `crm/dashboard` gains the send-back form and the copilot sidebar.
- The registry, the devcontainer, `.env.example`, and the `crm-app` skill gain the new services and variables.
