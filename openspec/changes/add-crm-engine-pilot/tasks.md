# Tasks: add-crm-engine-pilot

## 1. Project scaffold and pack

- [ ] 1.1 Write the port script map: the upstream path to the crm path, and the rename map for engine nouns and variables.
- [ ] 1.2 Scaffold `crm/`: `pyproject.toml` with uv and the dev group. Add `package.json` with the dev, seed, and gate scripts, `.gitignore`, `.python-version`, and the ruff config with the complexity cap.
- [ ] 1.3 Port `crm/domains/insurance/`: the manifest, the renamed seed data, the policy documents verbatim, the instructions, and the evals verbatim.
- [ ] 1.4 Write the pack loader in `crm/domains/`: read the manifest by `CRM_DOMAIN`, refuse a name mismatch, and fall back to `insurance`.

## 2. Backend pilot (week1day3)

- [ ] 2.1 Port the database module: the schema, the SQLite engine, the idempotent seed from the pack, and the helpers.
- [ ] 2.2 Port the models and the routes: health, cases, case detail, start, steps, decision, payment, sign-off, instructions, workers.
- [ ] 2.3 Apply the sign-off rule: an approval over the manifest limit waits, payment is refused, and a sign-off pays once.
- [ ] 2.4 Port the backend tests on a seeded temporary database.

## 3. Harness (week1day5)

- [ ] 3.1 Port the agent API client, the tools with the rename, and the documents table with section search and read.
- [ ] 3.2 Port the harness: the queue agent and one fresh subagent per case. Add the to-do list, the model call caps, and the refusals as text.
- [ ] 3.3 Port the failure path. A failed case returns to waiting. A second failure leaves it for a worker. The run examines the queue for missed cases at the end.
- [ ] 3.4 Port the stub model and the harness tests to full coverage of the new code.
- [ ] 3.5 Add the run routes and the agent entrypoint service on port 8080.

## 4. Dashboard and e2e

- [ ] 4.1 Port the dashboard: queue page with the to-do list, case page with steps and decision, instructions page, data loading, and styles.
- [ ] 4.2 Port the vitest tests and the TypeScript gate.
- [ ] 4.3 Port the e2e specs and the agent stand-in server, with the pinned database and empty model settings.

## 5. Infra, docs, and setup

- [ ] 5.1 Add `crm/.devcontainer/` with the Python 3.12 image, the Node feature, and the uv install steps.
- [ ] 5.2 Register the crm units in `tools/project_setup/registry.json` and keep the completeness test green.
- [ ] 5.3 Add the `crm-app` skill with the commands.
- [ ] 5.4 Write `crm/docs/` and `crm/README.md` in the house style, and update the lab `README.md` and `CLAUDE.md`.
- [ ] 5.5 Add `tests/crm_infra/` guards for the devcontainer, the registry entries, and the skill. Add the guard test that bans domain nouns in engine code.

## 6. Gates and delivery

- [ ] 6.1 Run the crm pytest suite, the root suite, and the three gate tools on the changed paths, and fix what fails.
- [ ] 6.2 Raise the coverage floor to the new total and keep the complexity cap at 10.
- [ ] 6.3 Commit the implementation in two milestone commits. Commit one takes the scaffold, the pack, and the backend. Commit two takes the harness, the dashboard, the e2e, the infra, and the docs. Push and open the implementation pull request.
- [ ] 6.4 Run the adversarial review on the diff, fix the confirmed findings, and merge. Budget the noun-guard allowlist volume here.
- [ ] 6.5 After the merge, archive this change through the archive pull request, as `openspec-git-discipline` orders.
