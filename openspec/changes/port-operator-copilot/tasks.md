## 1. Pack build

- [x] 1.1 Write `crm/domains/garage/manifest.json`: the twelve manifest
  keys, the vocabulary section (the money format, the repair-desk labels,
  the agreement card rows, the refusal messages, the benefit word
  `repair`), `documents` `wording` and `manual`, and the five seed names.
- [x] 1.2 Write `crm/domains/garage/rules.py`. `work_out_award` sums the
  covered fault lines, subtracts the base excess once, caps at
  `per_repair_cap`, and records every step. `needs_sign_off` compares
  against the limit of 600.
- [x] 1.3 Write `crm/domains/garage/protocol.py` with `resolve`, `gate`,
  `execute`, `summarize`, and `metric`, grounded on the library protocol.
- [x] 1.4 Write the policy documents. `policy/wording.md` carries the
  coverage rules of the three tiers, with the fault classes, the base
  excess, the per-repair cap, and the certified EV requirement.
  `policy/manual.md` carries the routing order, the certified EV gate, the
  escalation rule, and the desk authority. Both carry YAML front matter.
- [x] 1.5 Write the context files. `glossary.yaml`, `plans.yaml` with the
  three tiers and their fields (`base_excess` at 25 on standard and at 0
  on EV and fleet, `per_repair_cap` at 500 on standard, 400 on EV, and 900
  on fleet, the fault classes, and the certified EV requirement on the EV
  tier), `data_dictionary.yaml`, `case_rules.yaml`, and
  `reference_data.yaml` with the curated fleet of about 40 garages
  across five UK cities, with brands, specialisms, the certified EV mark,
  and free slots.
- [x] 1.6 Write the seed files. Eight cases from the source demo calls,
  six customers, the agreements on the three tiers, two desk workers with
  the service manager over the limit, the network record (AutoFix, GBP,
  600), and `improvement.json` and `models.json` beside the library
  shapes, with the `security/` redacted set.
- [x] 1.7 Write the four instruction files `case.md`, `queue.md`,
  `recipe.md`, and `improver.md`, naming served tools only and teaching
  the line shape (kind `item`, a `description` with the fault text, a
  `quantity` at 1, `amount` per fault line, zero nights and hours).
- [x] 1.8 Write the evals. `decisions.json` carries one decision per seed
  case. The held-out files name no queued case.
- [x] 1.9 Write the pack tests at `crm/domains/garage/tests/`. They pin
  the contract signatures, the seed records into the engine models, the
  served tools over the four instruction files, the eval set proofs, and
  the fleet match: every seed case's city, brand, and specialisms match a
  garage of the curated fleet, and every EV case matches a certified
  garage.
- [x] 1.10 Extend `crm/playwright.config.ts` with the garage branch: the
  `CRM_DOMAIN` passthrough, the garage ignore set, and the auth state, in
  the library pattern. The default run stays on insurance.

## 2. Gates and integration proof

- [x] 2.1 Run the validator: `uv run python validate.py garage` from
  `crm/` exits 0.
- [x] 2.2 Run the smoke run: `uv run python smoke.py garage` from `crm/`
  exits 0 with three decision lines.
- [x] 2.3 Run the pack test suite from `crm/` and the root suite. Both run
  green.
- [x] 2.4 Run the quality gates on the rules and the protocol modules.
  Expect 100 percent line and branch coverage, mutation with no survivors
  with a fresh lcov per surface, and crapper, dryer, and complexity clean.
- [x] 2.5 Run the e2e garage flow spec with `CRM_DOMAIN=garage` and the
  stack up. The flow signs in, opens the queue, and sees the pack words.
- [x] 2.6 Run the STE gate over the new openspec text. Expect no finding.

## 3. Docs and harness sync

- [x] 3.1 Add the garage rows to `CLAUDE.md` (the pack list and the
  projects section).
- [x] 3.2 Add the garage rows to `crm/README.md`.
- [x] 3.3 Add the garage sign-in rows to the `crm-app` skill.

## 4. Review and merge

- [ ] 4.1 Confirm the staged set is exactly the pack tree, the e2e spec,
  the playwright config branch, the docs rows, the change folder, the ADR,
  and the regenerated eval manifest before every commit.
- [ ] 4.2 Fold the review findings. Re-run the suite and the gates.
- [ ] 4.3 Merge through one squash-merged pull request with a clean port
  commit group, delete the branch, and resync the mainline.
- [ ] 4.4 Archive the change after the implementation merge.
- [ ] 4.5 Open the handover issue with the telemetry block. Record the
  capacity-planner follow-up in it.
- [ ] 4.6 Task 4.5 completes this change. Close the loop on the memory
  thread.
