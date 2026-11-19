# Demo runbook: the library loan desk on the public address

This runbook drives the demo of the library domain pack on the crm engine,
with the AWS wiring pointed at the floci emulator and every port reachable
from the web. `crm/deploy/demo_up.sh` starts the whole stack and prints the
address to use in every URL below.

## Before the demo

1. Run `crm/deploy/demo_up.sh`. The script starts the emulator and the
   compose Postgres, runs the wiring gate, seeds the library pack into the
   Postgres, and starts the app. It takes about a minute. The laptop's
   `crm.db` keeps its data.
2. Read the URL block the script prints. The address in it is the one this
   run uses.
3. Open the dashboard URL from a device outside the host network, for example
   a phone on the mobile network. The sign-in page must show.
4. If the host restarted, run `crm/deploy/demo_up.sh` again. The script stops
   the processes of an earlier run, so a rerun is safe.

## What the demo exposes

The stack serves fictional seed data, and its doors are open: the context
server on port 8006 answers any caller with no sign-in, the auth service
accepts any worker email with the runbook's published password `crm-dev`,
and the emulator accepts any credentials. Anyone on the internet can sign in
as Rosa and change the demo state while you present, and on the
live route, work copilot turns that spend the model key. For a
demo of this fictional data that is the intended trade. Tear the stack down
when the demo ends.

## The URLs

| URL | What it is |
| --- | --- |
| `http://ADDR:5173` | The dashboard. The demo lives here. |
| `http://ADDR:8000/api/health` | The backend's health answer. |
| `http://ADDR:8004/api/health` | The auth service's health answer. |
| `http://ADDR:4566/_floci/health` | The emulator's health answer with its services. |
| `postgres://crm:crm@ADDR:5433/crm` | The demo database, for a database viewer. Schema `crm` holds the engine's tables and the LangGraph state. |
| `http://ADDR:8006/mcp` | The context server's MCP endpoint. It answers MCP clients, not a browser. |
| `http://ADDR:8080` | The agent service. Idle on the emulator route. |
| `http://ADDR:8081` | The copilot service. |

Sign-ins, with the dev password `crm-dev`:

| Worker | Email | Role |
| --- | --- | --- |
| Rosa Meridian | `rosa.meridian@northgate.example` | Library Lead. May approve over the limit. |
| Iris Bonnell | `iris.bonnell@northgate.example` | Desk Librarian. May not. |

## Pre-flight: what is ready on this laptop

The demo stack runs the live route by default: dispatches work the waiting
cases through the real agent, and the Copilot answers. Three of the four
needs are already met: the script generates the agent's key, the compose
stack carries the Postgres both services need, and the script waits for
every service to answer its readiness probe. The one value the script
cannot make is the model key: put a real `OPENROUTER_API_KEY` in
`crm/.env` before the launch, or run `crm/deploy/demo_up.sh --emulator`
for the canned route that needs no key.

| Variable | What needs it | State today |
| --- | --- | --- |
| `OPENROUTER_API_KEY` | The live agent, the improver, the judge, and the Copilot | empty: fill it before the launch |
| `CRM_AGENT_KEY` | Made and shared by `demo_up.sh` itself | ready |
| `DATABASE_URL` | Served by the compose Postgres at the loopback only | ready |
| `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` | Tracing. Both unset means tracing is silently off | empty: fill for traces |

One rule governs the whole demo: one piece of agent work runs at a time. A
dispatch, an evaluation, and a round refuse to start while other work runs,
with a 409 that names the work: `A dispatch is running`, `An evaluation is
running`, `Round 1 is running`. Work that the agent has not spoken of for 5
minutes is quiet. A start during the first 5 minutes answers 409. The first
start after the 5 quiet minutes marks the work stopped with `The agent
stopped answering`, and then proceeds. Every `demo_up.sh` run re-seeds the
demo database, so a restart wipes every round and evaluation the audience
saw.

## Part 1: the AWS wiring story

1. Open `http://ADDR:4566/_floci/health`. The local AWS emulator answers with
   its services. Say: this is floci, the emulator for the deployment targets.
2. Open `crm/deploy/compose.yaml`. Show the emulator as code, with the canned
   invoke answer `{"accepted": true}`.
3. Open `crm/target/demo/wiring.log`. It ends with
   `wiring ok: backend caller -> botocore -> emulator -> acceptance`. Say: the
   backend's own runtime caller reached the emulator through botocore, exactly
   as it reaches AgentCore Runtime on AWS.
4. Open `crm/.env.example`. Show the AWS target variables. Say: the same
   variables point at the emulator in development and at AWS at rollout.
   ADR `adr/0008-local-emulator-first-aws-targets.md` owns this rule.
5. Say the honest boundary: the emulator proves the wiring. The demo runs
   the live route, so dispatches work the cases through the real agent. The
   runtime route is one flag away (`--emulator`), and on it the canned
   answer means an agent dispatch shows as sent, and the agent does no work
   behind the emulator.

## Part 2: the loan desk

1. Open the dashboard. Sign in as Rosa Meridian with the password `crm-dev`.
2. The queue lists the seed requests `LN-5001`, `LN-5002`, and `LN-5003`, all
   in the status `Waiting`. Say: the library pack seeds the loan desk.
3. Open `LN-5001`. Marta Voss asks for The Lighthouse Keeper for the standard
   14-day term. A copy is free, her card is in good standing, and she holds
   two loans with none overdue. Say: the desk approves this at the base term.
4. Open `LN-5002`. Dev Okafor asks for Gardens of the Coast, and both copies
   are on loan, so no copy is free. Say: this request declines.
5. Open `LN-5003`. The renewal runs to 21 days. The approval limit is 14
   days, so the decision holds for the lead librarian's sign-off. Rosa signs
   off, and the case moves to `Decided`.
6. Open `/settings`. The approval limit reads `14` with a days label. This
   is the pack's own setting, and the manifest carries it. Say: packs carry
   their settings, the engine carries none.
7. Open `/scoreboard`. The run scores live here.

## Part 3: the code tour

| Path | What to show |
| --- | --- |
| `crm/domains/library/manifest.json` | The pack's identity: resolutions, outcomes, documents, and the 14-day approval limit. |
| `crm/domains/library/rules.py` | The term arithmetic: the base term, the renewal, the tier cap, and `needs_sign_off`. |
| `crm/domains/library/protocol.py` | The words the pack speaks: approve, decline, refer. |
| `crm/domains/library/data/cases.json` | The seed cases `LN-5001` to `LN-5003`, with their stories. |
| `crm/domains/library/instructions/` and `crm/domains/library/context/` | What the agent reads: the pack's wording and manual, and its context lookups. |
| `crm/domains/loader.py` | The one seam between the engine and the packs. Engine code carries no domain noun. |
| `crm/backend/agent_service.py` | The dispatch switch: `CRM_AGENT_RUNTIME` names a runtime, or the laptop route runs the agent on 8080. |
| `crm/backend/runtime_calls.py` | The invoke path with its retries, which the wiring gate proves. |
| `crm/deploy/verify_wiring.py` | The wiring gate: register, invoke, read the acceptance. |
| `crm/e2e/library_flow.spec.ts` | The loan desk flow, pinned by the end-to-end tests. |
| `openspec/specs/` | The behavior specs, the source of truth. |

## Part 4: the self-improving agent

The loop: the agent first evaluates the starting version on the labeled
sets, then an improver agent reads the results and proposes a change or a
recipe, a worker approves or rejects, an approved change becomes a version
under test, evaluations score it, and a verdict keeps it or rolls it back.

1. Sign in as Rosa Meridian. Only the Library Lead sees the start button on
   `/improvement`. Iris sees a message that names the pack's 14-day limit
   instead.
2. The page shows, top to bottom: the round panel with its six stage steps,
   the proposal waiting for review with its diff, the versions chart against
   the version 1 line, the rounds table with verdicts and who reviewed what,
   and the recipes table. The page reloads every 2 seconds.
3. The page walks a round through six stages on its progress bar: the
   first evaluations, the improver at work, a change that waits for
   approval, the evaluations of the version under test, the verdict, and a
   new recipe that waits for approval. An open stage carries its count, for
   example `First evaluations, 2 of 3`. Read the labels off the screen as
   you go.
4. On the live route a round costs real model money and takes minutes: 24
   case runs, the improver's calls, and the judge's grades against the
   $0.50 limit. Do not start one on stage unless the plan is to wait. On
   the `--emulator` route, a started round waits at `First evaluations, 0
   of 3`, and the cost line reads `$0.0000 of $0.50`. Stop the round before
   you return to the queue part, because an open round refuses every
   dispatch start.
5. A full round runs 6 whole-set evaluations, which is 24 case runs on
   this pack, plus the improver's calls, capped at 20 model calls, plus the
   judge's grade on each case. The pack's spending limit is $0.50, and a
   version without grades rolls back with `it has no grade`.
6. The held-out set stays sealed: the improver reads held-out scores only,
   never held-out cases. The keep rule lives in `/settings` under Objectives
   on the held-out set: accuracy at least 80 percent, grade at least 2 of 3,
   plus the noise and tolerance gates.
7. `POST http://ADDR:8000/api/improvement/rounds` with Rosa's bearer token
   starts a round and answers 202. The stop and the review endpoints sit
   under the same prefix. Approval is the only path from a proposal to a
   version or a recipe.

## Part 5: evals and the scoreboard

An evaluation replays labeled cases through the agent and scores it against
the workers' pinned decisions. The library pack carries two sets: the
evaluation set of 8 cases, LN-5001 to LN-5008, and the held-out set of 2
cases, LN-5101 and LN-5102, which stays out of the queue.

1. Open `/scoreboard`. The Start an evaluation panel has the set, the cases,
   and the agents dropdowns. Sign in as Rosa, pick Held-out set, and press
   Start. The dropdown labels read `All 25` and `The five tiny cases` on
   every pack. Read the row subtitle for the true size: `Held-out set, 2
   cases`.
2. On the live route the judge grades every decided copy and the columns
   fill as the copies finish. On the `--emulator` route the row sits at
   Running with the wiring-only zeros: 0 percent accuracy on the held-out
   set, 12.5 percent on the evaluation set, and `Not graded`, because the
   judge is never called. The run blocks new starts for 5 minutes. After
   that, the next start marks it `The agent stopped answering` and
   proceeds.
3. With a model key, the judge grades the explanation of each decided copy
   on a 0 to 3 scale with an F, C, B, A rubric. The grade never touches the
   decision. The decision match is plain code against the pinned label. The
   judge calls OpenRouter and adds its own cost per graded copy.
4. The columns read: Decision accuracy, Accuracy, Cost of mistakes, Without
   sign-off, Grade of 3, Model cost per case, Time per case. On this pack
   the award is a loan term in days, so the cost columns read days, not
   dollars. Present the accuracy columns as the signal.
5. After a dispatch, open `LN-5006`. The agent referred it: the special
    collection shelves hold the title, and rule 7 sends the request to the
    lead librarian. As Rosa, the case now shows Issue the loan, with the
    term in days, and Decline the request. Issue it, and the case shows the
    loan record. Say: the referral hands the decision to the lead, in
    person.
6. `/scoreboard/{run_id}` shows each copy beside the worker's decision and
   the judge's grade, and marks evaluation copies `LN-5101-E1`. The copy
   never joins the queue and nobody signs it off.
7. Version scores come only from a round's own evaluations. A scoreboard
   evaluation you start by hand never changes a version's scores on
   `/configuration`. On a fresh seed, version 1 reads `Not scored yet`:
   kept, never evaluated.
8. `POST http://ADDR:8000/api/evaluations` with a worker bearer token and
   `{"evaluation_set":"held_out","tiny":true,"agents":3}` starts one and
   answers 202. An unknown set or more than 25 agents answers 422.

## Part 6: Langfuse traces

The case agent and the improver trace to Langfuse. The Copilot, the judge,
and the backend never trace.

1. Tracing needs a Langfuse project's key pair in `crm/.env`:
   `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY`, plus
   `LANGFUSE_BASE_URL` for a self-hosted host. Without the keys the client
   disables itself and logs a warning, and the app runs as normal. This
   laptop has no keys today, so no trace exists yet.
2. Traces are produced only on the live route. On the emulator route the
   canned answer means no agent code runs, so no handler is ever built.
   Prepare traces with the keys in `crm/.env`, then
   `crm/deploy/demo_down.sh && crm/deploy/demo_up.sh`.
3. Open the traces at the project's traces list, at
   `https://cloud.langfuse.com/project/<project-id>/traces`, with the
   sessions list beside it. The app stores no trace id, so navigate by
   session name: a case sits in session `LN-5001:<thread_id>`, an improver
   round in session `Round 1:<round_id>`. Traces arrive after a short
   batch delay.
4. One case trace reads top to bottom in the order the case ran: the
   safety gate, each model step with its inputs and outputs, a tool span
   per case tool call, and the pay node. Say: the app and Langfuse share
   session names, not ids.

## The emulator fallback

The live route is the default. The emulator route proves the deployment
wiring when no model key is available:

```bash
crm/deploy/demo_down.sh && crm/deploy/demo_up.sh --emulator
```

On that route a dispatch shows as sent, the emulator answers the canned
acceptance, and no model money is spent. To go back to the live route, run
`crm/deploy/demo_up.sh` again.

## After the demo: teardown

1. Run `crm/deploy/demo_down.sh`.
2. The script stops the app's processes, removes the `crm-floci` container,
   and makes sure that ports 4566, 8000, 8004, 5173, 8080, 8081, and 8006 no
   longer answer on the host. It exits 2 when a port still answers. The
   port probe reaches the host's own address. It proves the processes are
   gone, not the view through an external firewall.
3. The script writes `crm/.env` never, so nothing needs an undo. The demo
   database lives in the compose Postgres and goes with its container, and
   the logs stay at `crm/target/demo/`. The next `npm run dev` runs on the
   laptop defaults, and the laptop's `crm.db` keeps its data.

## Troubleshooting

- A URL does not answer from outside: run `crm/deploy/demo_up.sh` again. If
  it still fails, examine the firewall of the host and its network.
- A port is busy: run `crm/deploy/demo_down.sh`, then `demo_up.sh` again.
- The end-to-end suite and the demo stack share port 8004. Run one at a
  time.
