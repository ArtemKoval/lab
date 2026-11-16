---
name: crm-local-aws
description: Run the crm app with its AWS wiring pointed at the local floci emulator. Use this skill when the user asks to run crm locally with the AWS targets, to test the runtime, gateway, or memory wiring against an emulator, or to exercise the AgentCore invoke path without a real AWS account. Gives the readiness checks, the emulator startup, the runtime registration, the variables, the app start, the wiring gate, and the tear-down.
---

# crm-local-aws

ADR `adr/0008-local-emulator-first-aws-targets.md` owns the rule. This skill
runs the crm app with its AWS wiring pointed at the floci emulator, and proves
the runtime invoke path end to end: the backend's own runtime caller, botocore,
the emulator, and the acceptance the backend reads.

**The honest boundary:** the emulator proves the wiring. Its runtime answers
are canned (`{"accepted": true}`), so the agent's behavior is not exercised
here — the hermetic tests and the human's checks own behavior. With
`CRM_AGENT_RUNTIME` set, the backend sends real work to the emulator and gets
the canned acceptance, so runs show as dispatched while the agent does nothing
behind the emulator. Unset `CRM_AGENT_RUNTIME` to return to the laptop route,
where the real agent runs.

## Readiness

1. Docker answers: `docker info`. Gate: it prints server info. If not, start
   Docker or add the `docker-outside-of-docker` devcontainer feature (this
   repo's `crm/.devcontainer` carries it).
2. The floci image is pulled: `docker images floci/floci`. Gate: one row. If
   not: `docker pull floci/floci:latest`.
3. Port 4566 is free: `curl -sf http://localhost:4566/_floci/health` fails.
   If it answers, the emulator is already up — skip to step 3 of Start.

## Start the emulator

From the repository root:

```bash
docker compose -f crm/deploy/compose.yaml --profile langfuse up -d
```

The profile starts the emulator and the Langfuse server beside it. Gate:
`curl -sf http://localhost:4566/_floci/health` prints the services JSON, and
`curl -sf http://localhost:3000/api/public/health` prints the Langfuse status.
The server stores its event blobs in the emulator's S3, and the `langfuse`
bucket must exist before the first trace. Create it after every `up` that
made a new emulator container:

```bash
uv run --project crm python -c "import boto3; s3 = boto3.client('s3', endpoint_url='http://localhost:4566', region_name='us-east-1', aws_access_key_id='test', aws_secret_access_key='test'); names = [b['Name'] for b in s3.list_buckets().get('Buckets', [])]; s3.create_bucket(Bucket='langfuse') if 'langfuse' not in names else print('bucket exists')"
```

On hosts without the compose plugin, run the container directly:

```bash
docker run -d --name crm-floci -p 4566:4566 \
  -e FLOCI_HOSTNAME=localhost \
  -e 'FLOCI_SERVICES_BEDROCK_AGENT_CORE_INVOKE_RESPONSE={"accepted": true}' \
  floci/floci:latest
```

The invoke-response variable matters: the backend's runtime caller accepts
only `{"accepted": true}` or a refusal string, and the emulator's default
answer is something else.

## Set the wiring variables

In `crm/.env` (or the shell):

```bash
AWS_ENDPOINT_URL=http://localhost:4566
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
CRM_AGENT_RUNTIME=<the ARN the wiring gate prints>
LANGFUSE_BASE_URL=http://localhost:3000
LANGFUSE_PUBLIC_KEY=pk-lf-crm-local-aaaaaaaaaaaaaaaa
LANGFUSE_SECRET_KEY=sk-lf-crm-local-aaaaaaaaaaaaaaaa
```

The credentials are dummies: the emulator's IAM soft mode accepts any
non-empty values. `AWS_ENDPOINT_URL` is read natively by boto3 1.28+, so the
backend's runtime caller reaches the emulator with no engine change. The
Langfuse values are the seeded dev keys of the compose profile, and the case
agent, the improver, and the copilot send their traces to
`http://localhost:3000` while they are set.

## Run the wiring gate

From `crm/`, with the variables set:

```bash
AWS_ENDPOINT_URL=http://localhost:4566 AWS_DEFAULT_REGION=us-east-1 \
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test \
.venv/bin/python deploy/verify_wiring.py
```

Gate: the script prints `wiring ok: backend caller -> botocore -> emulator ->
acceptance` and exits 0. It registers the runtime on first run (name
`crm_agent`, ARN printed), then invokes through the backend's own
`runtime_calls.invoke`, which retries conflicts and reads the answer exactly
as a real dispatch does. The emulator's runtime-name pattern allows only
letters, digits, and underscores, and the session id must be at least 33
characters — the gate carries both facts.

## Start the app

With the variables set, start the app as usual: `npm run dev` from `crm/`.
Every dispatch, evaluation, and resume now flows through the runtime invoke
path to the emulator. Leave `CRM_AGENT_RUNTIME` unset to return the backend
to the laptop route (`CRM_AGENT_SERVICE`, the agent on 8080), where the real
agent works.

## Tear down

```bash
docker rm -f crm-floci
```

And remove `CRM_AGENT_RUNTIME`, `AWS_ENDPOINT_URL`, the AWS credentials, and
the three `LANGFUSE_*` values from `crm/.env`, so the next `npm run dev` is
back on the laptop route with no tracing. The database, the logs, and the
registered runtime live only inside the container and go with it. To take
the Langfuse server down too:

```bash
docker compose -f crm/deploy/compose.yaml --profile langfuse down
```

## Visit after launch

- Dashboard: `http://localhost:5173` — sign in with a pack worker email and
  the dev password `crm-dev` (insurance: `dana.whitfield@undercover.example`;
  helpdesk: `priya.nair@fastfix.example`).
- Emulator health: `http://localhost:4566/_floci/health`
- Langfuse: `http://localhost:3000` (sign in with `dev@crm.local` and
  `crmdevpass12`)
- Backend health: `http://localhost:8000/api/health`
- Auth service: `http://127.0.0.1:8004`

With `CRM_AGENT_RUNTIME` set, dispatches flow to the emulator's canned
answer; the agent's real work stays on the laptop route.
