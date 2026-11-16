# Design: add-crm-local-langfuse

## Context

The case agent and the improver construct a Langfuse callback handler
in their model configs. The copilot builds a turn config with no
handler. The SDK, `langfuse` 4.16.0 in `crm/uv.lock`, builds a
disabled client when no variable is set, so the suite stays green and
no trace leaves any process. No Langfuse server exists in the compose
file or in the AWS deployment. The CDK stack carries a SETTINGS seam
that adds environment variables to both runtimes from
`crm/agentcore/.env.local` or the deploy environment. ADR 0008 owns
the rule that one compose file serves the local targets and the same
variable names hold at rollout.

Container view:

```
        engine surfaces, one process each
+---------------------+ +-------------+ +------------------+
| case agent          | | improver    | | copilot          |
| (harness.case_config)| (improver)  | | (turns.work)     |
| CallbackHandler     | | Callback..  | | CallbackHandler  |
+----------+----------+ +------+-----+ +--------+---------+
           |                   |                |
           |  LANGFUSE_BASE_URL, LANGFUSE_PUBLIC_KEY,
           |  LANGFUSE_SECRET_KEY  (process environment)
           v  OTLP batch export, one trace per graph run or turn
+----------------------------------------------------------------+
| Langfuse server v4                                              |
|   web: UI + trace intake        worker: queue and writes        |
+----+----------+----------+------------------+------------------+
     |          |          |                  |
     v          v          v                  v
 Postgres   ClickHouse   Redis          object store
                                        MinIO (compose) / S3 (AWS)

values reach the surfaces through:
  crm/.env (--env-file, load_dotenv)     the dev services
  SETTINGS seam (.env.local or env)      the AgentCore runtimes

environments:
  compose profile "langfuse": local run and floci run, web on :3000
  LangfuseStack (new CDK app bin): AWS, one public address
```

Bullets:

- Boundary one: the engine surfaces hold only the handler and the
  config. The server stack stays outside the engine process.
- Boundary two: the two environments differ in the server stack only.
  The surfaces and the variables are the same in both.
- The runtimes already reuse `agent.entrypoint`, so the case agent and
  improver wiring rides to AWS with no runtime code change.
- Assumption: the five server images publish arm64 builds, so the
  local profile pulls on the Apple Silicon host.
- Open question: the AWS endpoint holds prompts and transcripts behind
  one public address. TLS and a domain are operator decisions at
  rollout (Open Questions).

## Goals / Non-Goals

**Goals:**

- One trace per case run, improver round, and copilot turn, visible in
  one Langfuse server per environment.
- One environment contract, `LANGFUSE_BASE_URL`,
  `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, the same at the laptop
  and at rollout, per ADR 0008.
- A compose profile that starts the server for the local run and the
  floci run with one command.
- A CDK stack that starts the server in AWS with one deploy and takes
  it down with one destroy.
- Work that never fails on tracing.

**Non-Goals:**

- No trace of the backend judge. The Lambda keeps no langfuse
  dependency.
- No trace retention policy, export pipeline, or alerting.
- No TLS certificate, domain, or multi-AZ posture for the AWS stack.
- No dashboard, schema, or database change.
- No change to the agentcore deploy path or to `runtime/main.py`.

## Decisions

1. **One compose file with a profile.** The Langfuse services join
   `crm/deploy/compose.yaml` under the profile `langfuse`. The
   emulator service carries no profile, so `docker compose up -d`
   starts the emulator alone, and `--profile langfuse` starts both.
   The profile seeds the first boot with literal dev values through
   the `LANGFUSE_INIT_*` variables, and only port 3000 publishes to
   the host. Alternative rejected: a second compose file. ADR 0008
   names one compose file for the local targets.
2. **Server v4 images.** The profile runs the `langfuse` 4 server line
   with Postgres 17, ClickHouse 26, Redis 7, and MinIO. Alternative
   rejected: the v2 server image with Postgres alone. The pinned SDK
   4.x exports through the OTLP intake that server v3 and later
   carry.
3. **`LANGFUSE_BASE_URL` in the contract.** The pinned SDK reads
   `LANGFUSE_BASE_URL` as its canonical name and `LANGFUSE_HOST` as a
   deprecated alias. The check read the SDK wheel of version 4.16.0.
   Alternative rejected: the alias. A deprecated name ages out.
4. **The copilot trace point is the turn config.** `turns.work` adds
   the handler and the metadata to the config it already builds, with
   the conversation id as the session id and `Copilot turn` as the
   trace name. One trace covers the turn, with the model calls as its
   children. Alternative rejected: the handler on each model call in
   `call_model`. That shape gives one trace per call, no tree, and
   breaks the case agent precedent of one trace per graph run.
5. **The AWS stack is a separate CDK app bin.** `bin/langfuse.ts` and
   `lib/langfuse-stack.ts` join `crm/agentcore/cdk/`, and a package
   script runs the app. The AgentCore bin, `bin/cdk.ts`, stays the
   agentcore CLI's property. Alternative rejected: the stack inside
   the AgentCore app. Every `agentcore deploy` would then carry the
   Langfuse topology, and the deploy times and the blast radius grow.
6. **The AWS topology is lean.** One VPC with public subnets in two
   AZs, tasks with public addresses, and no NAT gateway. One public
   ALB reaches the web service. Security groups admit traffic from the
   ALB to the web service, and from the web and worker to Postgres,
   Redis, and ClickHouse, and from nothing else. ClickHouse runs as
   one Fargate task with one EBS volume. Postgres runs on one RDS
   instance of the smallest general purpose class, single AZ. Redis
   runs on one ElastiCache node of the smallest class. The object
   store is one S3 bucket with encryption on and public access
   blocked. Alternative rejected: MinIO on Fargate. Real S3 removes
   one service, one set of keys, and one failure mode.
7. **The secrets split two ways.** The stack generates
   `NEXTAUTH_SECRET`, `SALT`, `ENCRYPTION_KEY`, the ClickHouse
   password, the Redis password, and the database password into
   Secrets Manager at synth. The operator gives the `LANGFUSE_INIT_*`
   values as CDK context at deploy, because the project keys must
   equal the keys the runtimes carry. The same values go into
   `crm/agentcore/.env.local`, and the SETTINGS seam moves them to the
   runtimes. Alternative rejected: AgentCore credential providers for
   the Langfuse keys. The SDK reads plain environment variables, not
   the provider API.
8. **The no-fail rule stays SDK property.** The export runs in a
   background batch, the client catches its own errors, and missing
   keys give the disabled client. The deltas pin the rule with
   scenarios. No engine code carries it.

## Risks / Trade-offs

- [ClickHouse on one task with one volume] -> a task replacement can
  lose trace history. Traces are diagnostic records, and retention is
  a non-goal. The stack re-seeds a fresh ClickHouse on boot.
- [A public ALB address holds prompts and transcripts] -> the Langfuse
  login guards the endpoint, the security groups admit the ALB alone
  to the web service, and the rollout skill carries the caution about
  the exposure.
- [The ALB serves plain HTTP] -> the lab rollout owns no domain. The
  login travels over HTTP at rollout, and an ACM certificate is an
  operator follow-up (Open Questions).
- [The server stack costs money while it runs] -> the bill is about
  one ALB, three small Fargate tasks, one EBS volume, one small RDS
  instance, and one small ElastiCache node each month. The destroy
  command removes it all.
- [The init seeding fires on the first boot only] -> changed init
  values need a fresh database. The skill carries the note.
- [A down server drops traces] -> the SDK batches in the background
  and drops what it cannot send. The deltas pin this as the no-fail
  rule.

## Migration Plan

1. The compose profile, the `.env.example` lines, and the skill and
   README steps land first. The traces story proves out on the laptop
   with the profile up.
2. The copilot config and its tests land second, behind the same
   contract.
3. The CDK stack, the SETTINGS names, and the rollout skill steps land
   third. The rollout exercises them at the next deploy.
4. Rollback: remove the three variables and the profile, and the
   engine returns to the disabled client. `cdk destroy` removes the
   AWS stack in one command.

## Open Questions

- The operator names the TLS certificate and the domain for the ALB at
  a production rollout. This change ships the HTTP endpoint.
- The operator names the trace retention window. This change ships the
  server defaults.
