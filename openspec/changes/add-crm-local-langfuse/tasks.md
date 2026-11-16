## 1. The compose profile and the env contract

- [x] 1.1 Add the Langfuse server services to `crm/deploy/compose.yaml`
      under the `langfuse` profile, with the literal dev seeds in the
      `LANGFUSE_INIT_*` variables, the pinned image tags, and port 3000
      alone on the host
- [x] 1.2 Start Docker if it is down, run the profile with
      `docker compose -f crm/deploy/compose.yaml --profile langfuse up -d`,
      and wait for the web service health
- [x] 1.3 Add the `LANGFUSE_BASE_URL`, `LANGFUSE_PUBLIC_KEY`, and
      `LANGFUSE_SECRET_KEY` lines to `crm/.env.example`
- [ ] 1.4 Write the seeded dev values into `crm/.env`, work one case with
      `uv run -m agent CLM-1001`, and find the trace in the web UI at
      `http://localhost:3000`
- [x] 1.5 Run `docker compose -f crm/deploy/compose.yaml up -d` with no
      profile. Gate: no Langfuse service starts

## 2. The copilot tracing

- [x] 2.1 Add the callback handler and the metadata to the turn config in
      `crm/agent/copilot/turns.py`, with the conversation id as the
      session id and `Copilot turn` as the trace name
- [x] 2.2 Add the unit tests beside the copilot tests: the config carries
      the handler, the session, and the name, and absent variables keep
      the config whole
- [x] 2.3 Run the crm Python suite with no variables set. Gate: the run
      is green

## 3. The skills and the README

- [x] 3.1 Give `crm-setup` the profile start step, the key handover, and
      the Langfuse address in its visit table
- [x] 3.2 Give `crm-local-aws` the profile in its start step and the three
      variables in its wiring step
- [x] 3.3 Give `crm-aws-rollout` the stack deploy and destroy steps, the
      init values handover, and the caution about the public endpoint
- [x] 3.4 Give `crm/README.md` the Langfuse address row and the profile
      command
- [x] 3.5 Read the crm line in CLAUDE.md, and change it only if it now
      names a wrong fact

## 4. The AWS stack

- [x] 4.1 Write `crm/agentcore/cdk/lib/langfuse-stack.ts` and
      `crm/agentcore/cdk/bin/langfuse.ts`, with the CDK context flags for
      the `LANGFUSE_INIT_*` values
- [x] 4.2 Add the package script that builds and runs the langfuse app
- [x] 4.3 Add the three `LANGFUSE_*` names to `SETTINGS` in
      `crm/agentcore/cdk/lib/cdk-stack.ts`, and update its comment for the
      operator values
- [x] 4.4 Run the CDK build from `crm/agentcore/cdk`. Gate: the
      typecheck passes

## 5. Tests and gates

- [x] 5.1 Add the compose test that checks the profile on the Langfuse
      services, its absence on the emulator service, and the absence of
      real-key literals
- [x] 5.2 Run the full crm suite from `crm/`, and run the root suite with
      the shared interpreter
- [x] 5.3 Run `openspec validate add-crm-local-langfuse --type change
      --strict` and the STE gate on the change text before the archive
- [x] 5.4 Run ruff, pyright, and the coverage run on the touched Python,
      and hold the coverage floor

## 6. Delivery

- [ ] 6.1 Commit `adr/0017-self-hosted-langfuse-tracing.md` with the
      implementation pull request
- [ ] 6.2 Commit the implementation in conventional commits with the
      attribution trailer, and publish the branch
- [ ] 6.3 Open the implementation pull request with the summary, the
      mechanism, the file list, and the test plan
- [ ] 6.4 Run the adversarial review of the diff, fix each confirmed
      finding, and re-run the gates
- [ ] 6.5 Merge, archive the change on its own archive branch, and merge
      that branch after the implementation merge
