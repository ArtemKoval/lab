---
name: crm-aws-rollout
description: Roll the crm stack out to a real AWS account, and roll it back. Use this skill when the user asks to deploy the crm engine to AWS, to move the crm targets from the local emulator to a real account, or to delete the crm AWS deployment after a rollout. Gives the readiness gates, the ordered up steps, the failed-step stop, and the down path.
---

# crm-aws-rollout

ADR `adr/0008-local-emulator-first-aws-targets.md` owns the decision. In
development, the crm AWS variables point at the local emulator on 4566. At
rollout, the same variables point at real AWS. The variables are
`CRM_AGENT_RUNTIME`, `CRM_GATEWAY_URL`, `CRM_MEMORY_ID`,
`CRM_COPILOT_RUNTIME`, `DATABASE_URL`, `CRM_AGENT_KEY`, `AUTH_URL`, and
`VITE_AUTH_URL`. The rollout adds no second set of variables.

This skill deploys. It never claims production readiness. A human does the
tests after the rollout.

## Stop rule

If a step fails, stop. Do not run the next step. The error output names the
failed step. Report that name to the user, with the stack as it is.

## Readiness

Run these examinations before the first up step.

1. Show the identity: `aws sts get-caller-identity`. Gate: the account is
   the target account.
2. Show the region: `aws configure get region`. Gate: the region is the
   target region.
3. Probe the emulator: `curl -sf http://localhost:4566/_floci/health`.
   Gate: the command fails. If it answers, the emulator still runs. Stop it
   with `docker compose -f crm/deploy/compose.yaml down`.
4. Reach the database: `psql "$DATABASE_URL" -c 'select 1'`. Gate: the
   command prints one row. The database is a Postgres database that this
   account can reach.

## Up

Do the steps in this order.

### 1. The database

1. Use an existing Postgres database in the account, or create one with the
   AWS CLI.
2. Write its address in `DATABASE_URL`.
3. Run the examination in Readiness step 4 again.

### 2. The secrets

The deploy reads three credentials: `OPENROUTER_API_KEY`, `CRM_AGENT_KEY`,
and `DATABASE_URL`. The file `crm/agentcore/agentcore.json` names them as
API key credential providers. Have the values ready. Give them when the
deploy step asks for them.

**CAUTION:** Write no key into `crm/agentcore/agentcore.json`, `crm/.env`,
or any file that git tracks. A pushed key is a security problem.

### 3. The backend package

Run these from `crm/`:

```bash
# makes an empty build folder
rm -rf target/lambda && mkdir -p target/lambda
# copies the backend code into the build folder
cp -r backend target/lambda/backend
# copies the domains package: the backend reads the active pack from disk
cp -r domains target/lambda/domains
# writes the server dependency group, with Mangum and psycopg, for the zip
uv export --only-group server --no-hashes --no-emit-project -o target/lambda/requirements.txt
# installs the server packages into the build folder
uv pip install -r target/lambda/requirements.txt --target target/lambda
# makes target/crm-app.zip
cd target/lambda && zip -qr ../crm-app.zip . && cd ../..
```

### 3b. The database seed

The Lambda handler runs with `lifespan="off"`, so nothing seeds the
database on deploy. From `crm/`, with `DATABASE_URL` set:

```bash
uv run --env-file .env -m backend.seed
```

Gate: the command prints the seeded counts. The human test in step 6
fails on missing tables without it.

### 4. Deploy

1. Send the package to the function:
   `aws lambda update-function-code --function-name crm-app --zip-file fileb://target/crm-app.zip`.
   If AWS has no `crm-app` function yet, create it first, with runtime
   `python3.12`, handler `backend.main.worker`, and an execution role.
2. Give the function a URL:
   `aws lambda create-function-url-config --function-name crm-app --auth-type NONE`.
   If the function has a URL already, this command fails. Then read the
   address with
   `aws lambda get-function-url-config --function-name crm-app`.
3. **CAUTION:** The function URL is public. The routes that change data
   refuse requests without the `X-API-Key` header.
4. Write the function URL into `crm/agentcore/.env.local` as `CRM_API`.
   The CDK stack gives it to the runtimes.
5. Deploy the runtimes, from `crm/`. The `agentcore` CLI ships in the
   `deploy` extra, not the base install: run `uv sync --extra deploy`
   once. Then `uv run agentcore deploy`. The command packages
   `runtime/main.py` as the agent runtime and `runtime/copilot.py` as the
   copilot runtime. It deploys the CDK stack at `crm/agentcore/cdk`. It
   asks for the three credential values of step 2. It prints the
   addresses of the runtimes, the gateway, and the memory.

### 5. The variables

The CDK deploy reads `crm/agentcore/.env.local` and gives the values to
the runtimes. After the deploy prints the addresses:

1. Write `CRM_AGENT_RUNTIME`, `CRM_COPILOT_RUNTIME`, `CRM_GATEWAY_URL`,
   and `CRM_MEMORY_ID` into `crm/agentcore/.env.local`.
2. Run `uv run agentcore deploy` again, so the runtimes receive them.
3. Set the function's own variables:
   `aws lambda update-function-configuration --function-name crm-app --environment "variables={DATABASE_URL=<address of step 1>, CRM_AGENT_KEY=<key of step 2>, CRM_DOMAIN=<pack name>, CRM_AGENT_API=<function URL>}"`.
4. Write the same values into `crm/.env` for the local tools, plus
   `AUTH_URL` and `VITE_AUTH_URL`: the address of the deployed auth
   service.

### 6. Smoke through the real address

1. Probe the queue on the function URL of step 4:
   `curl -sf "<function-url>/api/health"`. Gate: the command prints a JSON
   answer.
2. Work one case through the deployed stack, in the dashboard. This is
   human work, with the agent runtime live.

The engine's own tests cover the wiring, not the behavior. The emulator's
canned answers bound what the wiring tests assert. The human tests after
the rollout decide the rest.

## Down

The stop rule holds. Delete in the reverse order of Up:

1. Remove the rollout values of the variables from `crm/.env` and
   `crm/agentcore/.env.local`.
2. Delete the runtimes, from `crm/`: `uv run agentcore destroy`. The
   command deletes the agent runtime, the copilot runtime, the gateway, and
   the memory that the deploy made. The CLI ships in the `deploy` extra
   (`uv sync --extra deploy`) if it is gone from the venv.
3. Delete the function URL:
   `aws lambda delete-function-url-config --function-name crm-app`.
4. Delete the function:
   `aws lambda delete-function --function-name crm-app`.
5. Delete the build folder: `rm -rf crm/target`.

Then print this remainder for the human. This skill does not delete it:

- the database, with its records
- the CloudWatch log groups of the function and the runtimes
- every resource that a human made by hand
