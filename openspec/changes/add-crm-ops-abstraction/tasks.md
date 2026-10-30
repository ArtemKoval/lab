# Tasks: add-crm-ops-abstraction

## Stage 1 — types move, no behavior change

- [ ] 1.1 Move `Award`, `AwardRequest`, `Line`, `Plan`, `Plans`, `Benefit`, and the decision kinds into `backend/pack_types.py`; `models.py` re-exports them.
- [ ] 1.2 The suite passes unchanged; no route or test edits.

## Stage 2 — the protocol and the execute seam

- [ ] 2.1 Add `protocol.py` to both packs with `resolve`, `gate`, `execute`, `summarize`; the loader validates the verbs.
- [ ] 2.2 Add the `outcomes` and `effect_runs` tables (unique per case and effect) and the generic execute route.
- [ ] 2.3 `pay_case` writes through the execute seam; the gateway effect moves into the insurance protocol.

## Stage 3 — the payload

- [ ] 3.1 Add `resolution` and `payload` to the decisions; the routes accept opaque outcomes.
- [ ] 3.2 The sign-off gate moves behind the pack (`gate` verb); the core holds and answers generically.
- [ ] 3.3 Scoring and the judge read the pack metric accessor.

## Stage 4 — the declarations

- [ ] 4.1 The manifests declare `resolutions`, `outcomes`, `config`, and `effects` (engine_api 2); the loader validates them.
- [ ] 4.2 The agent tools and the dashboard render from the declarations; per-stage aliases keep the old names.
- [ ] 4.3 The opsdemo pack (escalations, no money) proves a new domain needs no core edit.

## Stage 5 — removal

- [ ] 5.1 Drop `award`, `payments`, `award_rules`, the `/awards/over-limit` route, and the aliases.
- [ ] 5.2 The dashboard renders `summarize(payload)`; the suite moves to the payload shape.

## 6. Delivery

- [ ] 6.1 Each stage lands green: the crm suite, ruff, and the gates.
- [ ] 6.2 Commit, push, and open the pull request; adversarial review on the whole diff; fix and merge.
- [ ] 6.3 Archive through the archive pull request.
