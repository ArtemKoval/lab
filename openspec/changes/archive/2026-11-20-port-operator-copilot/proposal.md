## Why

The private repository `ArtemKoval/operator-copilot` holds a prototype of a
call-centre copilot for a vehicle repair network. Operators take customer
calls, raise a repair job, and route the job to a garage. The prototype
runs end to end, carries one commit, no tests, and no shared history with
this repository. The behavior exists in one place only, outside the
mainline lab. This change ports the behavior into the crm engine as the
fifth domain pack, at lab standards.

## What Changes

- Add the `garage` domain pack at `crm/domains/garage/`: the manifest, the
  rules, the protocol, the policy documents, the context files, the seed
  data, the pack tests, and the pack evals.
- The pack maps the engine nouns to the network's nouns: a case is a repair
  job from one customer call, a contract is the vehicle's service
  agreement, the award is the repair authorization in pounds, and the
  outcome is the authorization. The desk worker decides `approve`,
  `decline`, or `refer`.
- The authorization arithmetic sums the covered fault lines, subtracts the
  plan's base excess, and caps the total at the plan's per-repair cap. An
  authorization over the 600 pound limit needs a service manager's
  sign-off.
- The routing rules of the source live in the pack manual as desk policy:
  brand first, then specialisms, then location, then queue capacity, with
  the certified EV gate. The desk names the chosen garage in the decision
  reason. The reference data carries a curated garage set of about 40
  garages, chosen so the routing rules decide the demo cases.
- Port the source demo calls as seed cases: the Jenny Doyle Volkswagen Golf
  brake case, the Julia Hart no-start case, a Leeds Nissan Leaf no-start
  job, and a Tesla EV charging-fault job among them.
- Carry no prototype code: the FastAPI backend, the React console, and the
  LangGraph module stay in the source repository. The engine already
  serves the queue, the desk, the agent, and the dashboard.
- Record the capacity planner of the source as an out-of-scope follow-up:
  the pack contract carries no flag surface, and the pack skill bans
  engine edits.
- Docs: the pack rows in `CLAUDE.md` and `crm/README.md`, and the garage
  rows in the `crm-app` skill.

## Capabilities

### New Capabilities

- `crm-garage-domain`: the garage domain pack. The capability pins the
  manifest, the authorization arithmetic, the sign-off question, the
  protocol verbs, the seed data, the queue fill, the policy documents, the
  instructions, the pack tests, the eval records and coverage, and the
  desk words of the pack.

### Modified Capabilities

## Impact

- New tree: `crm/domains/garage/` with about 30 files, among them the pack
  tests and the pack evals.
- One test-infra edit: `crm/playwright.config.ts` gains the garage branch
  for the opt-in e2e run, in the library pattern.
- Docs: `CLAUDE.md`, `crm/README.md`, and `.claude/skills/crm-app/SKILL.md`.
- No engine file changes: `crm/backend/`, `crm/agent/`, `crm/context/`,
  `crm/domains/loader.py`, `crm/validate.py`, and `crm/smoke.py` stay
  untouched.
- No new dependencies. No registry change: the loader discovers the pack
  by name, and `CRM_DOMAIN=garage` selects it.
- Merge method: clean port commits on one squash-merged pull request. The
  source repository stays untouched as the prototype archive.
