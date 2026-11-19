## Context

The lab carries the crm engine with four domain packs: insurance, helpdesk,
opsdemo, and library. The pack seam is `crm/domains/loader.py` plus the
manifest contract of ADR 0007. The vocabulary feature (ADR 0019) lets a
pack rename every engine noun on the dashboard. The private source
repository `ArtemKoval/operator-copilot` carries one commit, `445ed56`, no
shared history with lab, no tests, unpinned dependencies, and deliberate
prototype gaps. The operator settled the shape of this port: the behavior
re-homes as a domain pack, at lab standards, with the source repository
kept untouched as the archive.

The grill pass walked the plan branches and left no operator question:
placement, depth, source disposition, and commit shape are settled. The
remaining unknowns were codebase-answerable, and the codebase answered
them: the pack data file set mirrors the library pack, the award arithmetic
mirrors the insurance award shape, the contract trip block re-semantics to
vehicle fields, and gates.yaml and rubrics sit outside the required
artifact closure of an ungoverned change.

The ported pieces attach at these points:

```
lab repository
  crm engine
    backend + agent + context + auth        engine core (lab, unchanged)
    pack seam: crm/domains/loader.py + manifest contract (ADR 0007)
      insurance | helpdesk | opsdemo | library | <<PORT>> garage
    GET /api/pack serves the declarations and the vocabulary payload
      <<PORT>> the garage vocabulary travels the existing feature
    dashboard renders the pack vocabulary (ADR 0019) — no dashboard edit
    e2e (playwright): default insurance | library flow | <<PORT>> garage flow
  <<PORT>> crm/domains/garage/**
           manifest, rules, protocol, policy, context, data,
           instructions, evals, tests
  <<PORT>> docs: CLAUDE.md pack rows, crm/README.md, crm-app skill rows
```

## Goals / Non-Goals

**Goals:**

- The prototype's business behavior runs end to end as the garage pack on
  the engine contract, with the engine untouched.
- The pack passes the validator, the smoke run, the pack tests, and the
  ordinary gates: 100 percent line and branch coverage of the pack code,
  mutation with no survivors on the rules and the protocol, crapper, dryer,
  and complexity at 10 or less.
- The docs carry the pack: the CLAUDE.md pack rows, the crm README, and the
  crm-app skill.
- The desk words of the pack render on the dashboard through the existing
  vocabulary feature.

**Non-Goals:**

- No engine edit. The pack skill bans it, and the pack contract already
  carries every surface the pack uses.
- No promotion of the pack into the dspy-gate governed registry.
- No port of prototype code: the FastAPI backend, the React console, and
  the LangGraph module stay in the source repository.
- No capacity planner surface. The pack contract carries no flag surface,
  and the follow-up is recorded, not built.

## Decisions

- **Pack name `garage`, display name `AutoFix Vehicle Repair`.** Case ids
  `JOB-1001` and up, case types `repair`, `service`, and `diagnostics`,
  worker ids `OPS-xx`, customer ids `CUS-10xx`. Alternative rejected: the
  pack name `repair` — it collides with the job type word and reads wrong
  in the pack list.
- **The manifest vocabulary carries the noun mapping.** The pack renames
  the engine nouns on the dashboard: the case is the job, the contract is
  the agreement, the award is the authorization in the pack's money unit,
  the outcome is `authorization`, the benefit word is `repair`. The trip
  block re-semantics to vehicle fields (destination is the make,
  departs_on is the first registration, returns_on is the service due
  date), and `travelers` carries the covered vehicle entries. This mirrors
  ADR 0019 and the library pack's trip reuse. Alternative rejected: a
  dashboard change per pack — the vocabulary feature exists exactly for
  this, and the core dashboard carries no domain word of its own.
- **The authorization arithmetic mirrors the insurance award shape.**
  `work_out_award` sums the covered fault lines, subtracts the base excess
  once, caps the total at the plan field `per_repair_cap`, records every
  step, and answers the sign-off question over the limit of 600. The
  request line carries the kind `item`, an `amount` per fault line, and
  zero nights and hours. Alternative rejected: a garage-aware engine
  parameter — the engine contract carries no garage parameter, and the
  pack skill bans the engine edit.
- **The routing rules live in pack policy, not code.** The wording carries
  the coverage rules of the three plan tiers. The manual carries the
  routing order (brand first, then specialisms, then location, then queue
  capacity), the certified EV gate, and the escalation rule. The desk
  names the chosen garage in the decision reason. The reference data
  carries the garage fleet as searchable facts. The engine's document
  search and read tools already serve these rules, so the pack needs no
  new surface. Alternative rejected: encode the triage scoring in
  the rules module. The engine calls `work_out_award` with contract,
  plans, request, and approval limit only, and no garage rides the call.
  ADR 0020 records the decision.
- **A curated fleet of about 40 garages in the reference data.** Each demo
  case has one decisive best garage under the routing order. The
  250-garage fleet of the source stays in the source repository. The
  garage facts carry name, city, brands, specialisms, the certified EV
  mark, and free slots. Alternative rejected: port all 250 garages — the
  context would bloat, and no demo case would turn on the tail garages.
- **The seed mirrors the source demo calls.** Eight cases: the Jenny Doyle
  Volkswagen Golf brake case (London, later Reading), the Julia Hart Ford
  Focus no-start case, a Leeds Nissan Leaf no-start job, a Tesla EV job
  with a charging fault, and four more drawn from the source issue list.
  Six customers, agreements on the three tiers, two desk workers with the
  service manager allowed over the limit, and the network record with
  currency GBP and the 600 limit. Alternative queue scale: more cases
  would not add a rule to prove.
- **The ordinary gates at lab standards.** The pack tests in
  `crm/domains/garage/tests/` pin the contract signatures, the seed
  records, the served tools over the four instruction files, and the eval
  sets, and they prove every seed case matches a garage in the curated
  fleet. The gates hold: 100 percent line and branch coverage of the rules
  and the protocol, mutation with no survivors on the two modules, crapper
  and dryer clean, complexity at 10 or less. The e2e lane adds the garage
  flow spec with `CRM_DOMAIN=garage`, opt-in through the gate variable,
  and extends `crm/playwright.config.ts` with the garage branch: the
  variable passthrough, the ignore set, and the auth state, in the library
  pattern. The suite and the gates run on the pull request, and the e2e
  lane stays opt-in because no gate variable exists in CI.
- **Docs and setup stay in the closed world.** The CLAUDE.md pack rows, the
  crm README pack rows, and the crm-app skill sign-in rows are edits to
  existing files. No new component kind appears: no new hook, no new tool,
  no new permission, no registry line. The pack tests and the e2e spec
  join existing test lanes.

## Divergences

- **The capacity planner stays out of the pack.** The source raises
  awareness flags before the queue overflows (specialism shortage, EV gap).
  The pack contract carries no flag surface, and the pack skill bans engine
  edits. The reference data carries the free-slot facts as static numbers,
  and the engine holds no live per-garage count behind them. The follow-up
  lives in the handover issue: a flag surface needs a proposal of its own,
  on the engine side.
- **The demo scope narrows to the UK network.** The source carries no
  prices anywhere, and its garage fleet spans the UK, Germany, and France.
  The pack narrows the curated fleet and the seed cases to UK cities
  (London, Reading, Leeds, Manchester, Birmingham), prices in GBP as its
  own choice, and the reference data names no German or French city. The
  full fleet of the source stays in the source repository.
- **The engine renders the money award with the dollar prefix.** The
  loader hard-codes the dollars format for the `money` unit, and the
  pack-vocabulary spec pins it. The pack prices in pounds in its own
  records and documents, and authors its refusal messages without the
  amount placeholder, so no engine money prefix reaches the refusals. A
  currency word is new engine vocabulary under ADR 0007's clause, and it
  stays a recorded follow-up with its own proposal.
