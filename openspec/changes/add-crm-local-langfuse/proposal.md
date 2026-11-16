# Proposal: add-crm-local-langfuse

## Why

The case agent and the improver carry the Langfuse callback handler in
their model configs. No environment sets the variables, so the handler
exports no trace, and each run leaves no record of its model calls.

## What Changes

The change adds two components: the Langfuse server stack and the
copilot callback config. The compose file, the SETTINGS seam, and the
case agent and improver handlers already exist.

### The compose profile

- `crm/deploy/compose.yaml` gains a profile with the Langfuse server
  services. The profile adds services beside the emulator service.
- The local run and the floci run start the profile with one command.
  The emulator service itself stays unchanged.
- Docker stays optional. Without Docker, the app runs as it runs today.
- The tracked compose seeds the first boot with literal dev values
  through the `LANGFUSE_INIT_*` variables.

### The traces

- The traced surfaces are the case agent, the improver, and the
  copilot.
- The case agent and the improver need no code change. Their existing
  handlers export when the three variables are set.
- The copilot turn config gains the handler. Each turn traces under
  its conversation id as the session id, with one trace name.
- The backend judge stays untraced. The Lambda backend keeps no
  langfuse dependency.

### The AWS stack

- The deployment gains a Langfuse server stack as a new CDK app beside
  the AgentCore stack, with a separate app bin. The agentcore deploy
  path stays untouched.
- The stack holds the web and worker services and the Postgres, Redis,
  ClickHouse, and object storage the server needs, behind one public
  address. The object store is S3 in place of MinIO.
- The Langfuse login guards the public endpoint. The design carries
  the network guard in detail.
- The operator gives the init values at deploy time, like
  `OPENROUTER_API_KEY` today. The stack seeds the first boot with them.

### The env contract and the keys

- The contract is `LANGFUSE_BASE_URL`, `LANGFUSE_PUBLIC_KEY`, and
  `LANGFUSE_SECRET_KEY`. The pinned SDK reads `LANGFUSE_BASE_URL` as
  its canonical name.
- The dev services read the variables from `crm/.env` through
  `--env-file`. The agent CLI reads them through `load_dotenv`. The
  runtimes read them from the SETTINGS seam.
- The local compose seeds dev keys, so the values sit once in the
  tracked file and once in `crm/.env`.
- Missing keys keep the disabled client. The suite stays green, and no
  run fails on tracing. Each traced surface carries this rule in its
  delta.
- The change adds no bootstrap script.

### Order

- The compose profile and the env contract land first, and the CDK
  stack follows.

## Capabilities

### New Capabilities

None. The change extends three existing capabilities.

### Modified Capabilities

- `crm-runtime`: The delta names the tracing target for each
  environment: the compose profile for the local run and the floci
  run, the new stack for AWS. It pins the `LANGFUSE_*` env contract
  and the SETTINGS read path. It also records the second CDK app,
  since the runtime spec owns the deployment shape.
- `crm-copilot`: The delta pins one trace per turn, with the
  conversation id as the session id and a trace name. It carries the
  no-fail rule.
- `crm-engine`: The delta pins one session per case thread, the trace
  names, and the tags for the case agent and improver traces. It
  carries the no-fail rule too.

## Impact

- `crm/agentcore/cdk/`: the new app bin and the Langfuse stack file.
  `runtime/main.py` and the agentcore deploy path stay untouched. The
  AgentCore stack file keeps its app, and its SETTINGS list gains the
  three names.
- `crm/agent/copilot/turns.py`: the turn config gains the handler.
  `crm/agent/harness.py` and `crm/agent/improver.py` need no code
  change, and the three variables alone start their export.
- `crm/deploy/compose.yaml`: the profile adds services beside the
  emulator service.
- `crm/.env.example` gains the `LANGFUSE_*` variables.
- The skills gain steps. `crm-setup` and `crm-local-aws` gain the
  profile start and the key handover. `crm-aws-rollout` gains the
  stack Up and Down steps and the caution about the public endpoint.
- `crm/README.md` gains the Langfuse address.
- `adr/0017-self-hosted-langfuse-tracing.md` records the durable
  decisions.
- No new Python dependency. `crm/uv.lock` pins `langfuse` 4.16.0, and
  the runtime dependency group already holds it. The server images
  come from the compose file and the CDK stack, not from the Python
  environment.
- No schema or database change. The case, conversation, and turn
  records stay as they are.
- The suite stays hermetic. Absent variables keep the disabled
  client, so no test sends a trace.
- No new unit in `tools/project_setup/registry.json`. All touched
  items exist in the clone.
- No `.claude/settings.json` change, and the diff touches no protected
  gate path, so the pull request needs no `gate-integrity:
  acknowledged` line.
- The crm capabilities sit outside the dspy-gate harness registry, so
  this change carries no spec gate beyond `openspec validate` and the
  STE rule.
