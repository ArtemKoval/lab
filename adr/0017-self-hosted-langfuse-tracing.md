# 0017 - Self-hosted Langfuse tracing for the crm engine

- Status: proposed
- Date: 2026-11-16

## Context

The case agent and the improver carry the Langfuse callback handler in
their model configs, and the copilot carries none. No environment sets
the variables, so the SDK holds a disabled client and no trace leaves
any process. The engine runs three ways: the local run, the floci run
against the emulator, and the AWS deployment. ADR 0008 owns the rule
that one compose file serves the local targets and that one set of
variable names holds at rollout. The engine needs a record of its
model calls, their cost, and their steps, in each environment.

## Decision

Self-host one Langfuse server per environment. The compose file gains
a profile that serves the local run and the floci run. The AWS
deployment gains a dedicated CDK app beside the AgentCore app, so the
agentcore deploy path stays untouched. The environment contract is
`LANGFUSE_BASE_URL`, `LANGFUSE_PUBLIC_KEY`, and
`LANGFUSE_SECRET_KEY`, the same names everywhere, per the ADR 0008
pattern. Operator-given init values seed the first boot of both
environments. Traces never fail work: the export runs in the
background, and a server that answers nothing changes no outcome.
Rejected options:

- Langfuse Cloud. The traces leave the lab boundary, and the local
  loop needs no outside account.
- The `LANGFUSE_HOST` alias. The pinned SDK reads `LANGFUSE_BASE_URL`
  as its canonical name, and the alias is deprecated.
- The Langfuse stack inside the AgentCore CDK app. Every
  `agentcore deploy` would carry the Langfuse topology.
- A trace per model call in the copilot. The house precedent is one
  trace per graph run, with the calls as children.
- A bootstrap script for the keys. The init seeding of the server
  removes the need.

## Consequences

Positive: each environment holds one trace store for every model call,
with the cost and the steps. One contract carries the target across
all three runs. The compose profile proves the wiring before any
deploy, and one destroy command removes the AWS stack.

Negative: the AWS stack bills each month while it runs, and its
endpoint serves plain HTTP in the lab. ClickHouse runs on one task, so
a task replacement can lose trace history. The init seeding fires on
the first boot only.

Follow-up: the operator names the TLS certificate, the domain, and the
trace retention window at a production rollout.
