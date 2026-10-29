# Design: add-crm-durable-swarm-improve

## Source

The upstream briefs `docs/DURABLE.md`, `docs/SWARM.md`, and `docs/IMPROVE.md` at `week2day5-end` are the behavior source. Each brief carries a sidenote that names the course lab as the style reference. The lab style is the `-end` branch code this change ports, and the brief wins where they differ. The port order is `week2day3`, `week2day4`, `week2day5`, one milestone commit each.

## Plan review

The seam comes from the accepted tournament in `add-crm-engine-pilot` and ADR 0007. This change adds no new kind of component to the seam. One review pass settled four transformation decisions:

- Supabase stays out. The upstream backend already switches on `DATABASE_URL`: Postgres when set, SQLite when not. The port keeps that switch, and the devcontainer default stays SQLite, so the tests stay hermetic with no network.
- The checkpoint saver becomes a factory. The port adds SQLite as the local saver and keeps PostgresSaver for the Postgres case, because a devcontainer has no Postgres. The factory is one function behind the graph builder.
- Supabase Auth becomes a local auth service. The backend verifies any JWT against a JWKS URL, so the port serves JWKS from a small Node service at `AUTH_URL` and the dashboard signs in against it. The e2e stand-in from upstream becomes the shape of that service. The AWS rollout later points the same variables at Cognito.
- The payout engine becomes the pack rules. The port moves `backend/payout.py` to `domains/insurance/rules.py` behind a fixed contract, and the pack manifest names the module.

## Port mechanics

The `crm/port/port.py` tool carries the rename map. This change runs three passes:

```bash
python3 crm/port/port.py --ref week2day3-end --base week1day5-end --dest crm
python3 crm/port/port.py --ref week2day4-end --base week2day3-end --dest crm
python3 crm/port/port.py --ref week2day5-end --base week2day4-end --dest crm
```

The passes port `data/models.json` and `data/improvement.json` into the pack. Supabase client code in the dashboard is replaced by hand with the auth service client. The lockfiles regenerate.

## Key decisions

- The saver factory: `checkpoints.py` returns a saver from `DATABASE_URL`; SQLite locally, Postgres when set. Tests keep the SQLite saver.
- The rules contract: `rules.work_out(lines, contract, plans, settings) -> list[steps]`, pure code, no engine imports. `backend/calculation.py` stays engine: it pins one calculation per case per attempt and refuses a mismatched approval.
- The auth service: `crm/auth/server.mjs`, Node built-ins only, signs ES256, serves JWKS at `/jwks.json`, accepts any pack worker email with the dev password from `AUTH_DEV_PASSWORD`, and runs as `npm run dev:auth` on port 8004. `backend/auth.py` reads `AUTH_URL`. The dashboard replaces `supabase-js` with a fetch sign-in and stores the token in the session storage.
- The improver, judge, versions, rounds, recipes, spending, and verdict port as engine code with the rename. The improvement settings and models data live in the pack.
- Langfuse stays optional: the handler attaches only when the keys are in the environment, so hermetic runs trace nothing.
- Port 8002 hosts the agent service; `npm run dev` starts backend, agent, auth, and dashboard. `CRM_AGENT_SERVICE` names its address.

## Mandated skills

The tournament and review machinery ran for the seam in change one. This change runs one adversarial review round on the artifacts before the proposal pull request, and one on the diff before the merge. The specs follow the schema shape and the STE gate.

## Failure modes

- A saver mismatch loses state on restart. The restart tests carry a case across two graph builds on one database file.
- The auth service and the backend drift on claims. One test signs a token with the service's key and passes the backend gate.
- The rules module drifts from the engine contract. The pack tests import it and pin the signature.
