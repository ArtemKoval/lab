# Design: add-crm-engine-pilot

## Source

The upstream repo is `github.com/ed-donner/undercover`. Its product milestones are branch pairs from `week1day3-end` to `week3day5-end`. This change ports `week1day3-end` and `week1day5-end`. Later changes port weeks two and three in order. The upstream briefs `docs/SPEC.md` and `docs/HARNESS.md` are the behavior source for this change.

## Plan review

Three independent tournament attempts designed the engine and domain seam. The attempts agree on five points. Each domain is one pack folder. The deterministic rules are a pure Python module, not a data language. The `CRM_DOMAIN` variable names the pack. The engine carries the rename, and a guard bans domain nouns in engine code. A validator with a smoke run serves the onboarding. The attempts diverge on the package layout and the name of the customer record. This design judges each divergence and synthesizes the winner.

- The attempts B and C merge the backend and the agent into one `crm/engine/` package. The winner keeps the upstream layout: `crm/backend/`, `crm/agent/`, and later `crm/context/` and `crm/runtime/`. The upstream import graph, the deploy targets, and the tool configs stay one to one, so each later milestone diff stays mechanical. A merged package buys nothing and rewrites every import.
- The attempts name the customer record `record` or `account`. The winner is `contract`. `record` collides with database rows, and `account` collides with the customer itself in a CRM. The insurance pack can display the word policy through labels.
- The attempt A adds a per-pack `adapters.py`. The winner drops it: the pack files use engine schemas, and the manifest carries the display labels. One boundary, no translation layer.

## Layout

The project root is `crm/`. The Python path root is `crm/`, so the imports match the upstream names.

```text
crm/
  backend/        FastAPI app, database, models, routes, seed
  agent/          harness, tools, api client, stub model, tests
  dashboard/      React, Vite, TypeScript
  e2e/            Playwright specs and stand-in servers
  domains/
    insurance/    the first domain pack
      manifest.json
      policy/wording.md, manual.md
      data/       cases, customers, contracts, plans, workers, company, knowledge
      instructions/case.md, queue.md
      evals/      held-out decision sets for later changes
  docs/           BRIEF, HARNESS, PROCESS, TECH_STACK, STATUS, CODE_STANDARDS
  e2e/            see above
  .devcontainer/  devcontainer.json and README
  pyproject.toml  uv project with dev dependencies
  package.json    npm scripts that drive uv and vite
```

The engine is `crm/` without `crm/domains/`. No engine module imports a pack by name. The loader resolves the pack folder, and the engine reads the pack only through the loader.

## Vocabulary

The rename applies to engine code, tables, routes, tools, and dashboard text. The pack keeps the insurance wording in its content, its labels, and its data values.

| Upstream | Engine | In the pack |
| --- | --- | --- |
| claim | case | case label is claim |
| payout | award | award label is payout |
| handler | worker | worker label is handler |
| policy, policy record | contract | contract label is policy |
| UnderCover | crm | brand in the manifest |

Guard: a root-suite test greps `crm/backend`, `crm/agent`, `crm/dashboard/src`, and `crm/e2e` for the banned nouns `claim`, `payout`, `handler`, and `undercover`. The test keeps an allowlist for false hits. A new domain noun goes into the test list.

## Environment variables

| Upstream | Engine | Purpose |
| --- | --- | --- |
| `UNDERCOVER_DB` | `CRM_DB` | SQLite path, default `crm/crm.db` |
| `UNDERCOVER_API_KEY` | `CRM_AGENT_KEY` | later changes. Absent in week one |
| `UNDERCOVER_API` | `CRM_AGENT_API` | agent base URL, default `127.0.0.1:8080` |
| `UNDERCOVER_CONTEXT` | `CRM_CONTEXT_URL` | later change |
| `DATABASE_URL` | `DATABASE_URL` | Postgres for later changes. Absent means SQLite |
| `MODEL_NAME` | `MODEL_NAME` | model override on OpenRouter |
| `OPENROUTER_API_KEY` | `OPENROUTER_API_KEY` | model key, not needed by tests |
| `CRM_DOMAIN` | new | the pack name, default `insurance` |

## Key decisions

### ASIT

The closed world holds the upstream components. The one new kind is the domain pack and its loader, because the goal is to onboard a new domain without engine changes. Everything else is a port with a rename. The contract, adapter, and merged-engine ideas from the attempts are removed or refused.

### Data shape first

The pack schemas use engine nouns from the first commit. The seed JSON carries `case_id`, `award`, and `contract_id`. A port script applies the rename map to the upstream data files, and a test compares counts with the upstream source. The pack files keep story text, section text, and eval content verbatim.

### Sign-off and payment

The sign-off rule and the payment block stay in engine code, as upstream week one has them. The limit comes from the manifest settings.

### Hermeticity

The stub model replaces OpenRouter in pytest. The e2e specs run against a stand-in agent server that replays decisions, so Playwright needs no model key. The upstream stand-in pattern ports as is. The e2e config pins its own database file and empty model settings.

### Devcontainer and registry

The devcontainer uses the Python 3.12 image with the Node feature and installs uv, the Python packages, and the Node packages. The registry gains three units: the `uv` system tool, the crm Python set, and the crm Node set. The root suite gains `tests/crm_infra/` guards for the devcontainer file, the registry entries, and the skill. The `fde/.devcontainer` masters stay untouched.

### Skills and docs

The `crm-app` skill gives the dev, seed, and gate commands, on the model of the `fde-app` skill. `crm/docs/` rewrites the upstream product documents in this house style. The lab `README.md` and `CLAUDE.md` gain the project entry.

### Later seams, noted now

Change two ports the deterministic award engine into `domains/<name>/rules.py`. It also adds durable checkpoints with a saver factory. The factory uses SQLite locally and Postgres when `DATABASE_URL` is set. Change three ports the auth. The upstream Supabase sign-in becomes a local auth service with the same JWT and JWKS shape, so the pack stays testable in the devcontainer. The AWS rollout points the same variables at Cognito.

## Mandated skills

The project config names a skill for each artifact. This change runs their outcome patterns, because the pipeline machinery already carries them and the run is autonomous:

- The proposal got the tournament instead of `grill-me`: three independent attempts, a synthesis, and no open question for the user. The task text orders autonomous work with tournaments.
- The specs follow the schema template, the house Gherkin shape, and the mechanical STE gate instead of a separate `gherkin-authoring` load.
- The design carries the layout tree here. The C4 diagram set is a deliverable of the final wiki change, with the `c4-diagrams` skill there.
- The ADR files follow the six accepted records in `adr/` and the `architectural-decision-records` shape they share.
- An `adversarial-reviewer` round runs on the artifacts before the proposal pull request, and a builder check follows.

## Failure modes

- A rename miss puts a domain noun in engine code. The guard test fails the root suite, and the fix is one rename.
- A pack file drifts from the engine schema. The seed command refuses it and names the file.
- The stub model drifts from the real tool contract. The harness tests bind the same tool list to both, and a test compares the tool names.
