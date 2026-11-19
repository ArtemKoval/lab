# Tasks: add-library-domain

## 1. The pack scaffold

- [x] 1.1 Create `crm/domains/library/` with `manifest.json`. Verify the loader loads the pack under `CRM_DOMAIN=library`, with no loader edit. The manifest carries all twelve keys the validator requires. `engine_api` is 2. The resolutions are `approve`, `decline`, and `refer`. The outcome `loan` binds to `resolve`. The effect on `loan` is gated. `award_approval_limit` is 14.0. The documents are `wording` and `manual`, which the engine pins. The seed names the five files.
- [x] 1.2 Write the pack tests in the shape of the opsdemo pack tests. A `CRM_DOMAIN=library` fixture loads the pack. An examiner run over the pack raises no finding. The tests pin the rules and protocol contract signatures.

## 2. The rules and the protocol

- [x] 2.1 Write `crm/domains/library/rules.py` test first. `work_out_award` reads the requested days from the line `nights` field. It names the base term step. It caps the term at the tier `max_loan_days`. It returns the term with its steps. `needs_sign_off` returns true above the limit. Tests cover 14 nights on standard. Tests cover 21 nights on research. Tests cover 35 nights over the research cap.
- [x] 2.2 Write `crm/domains/library/protocol.py` test first. Tests cover `resolve` against the rules award. Tests cover `gate` above the limit. Tests cover `execute` with the title from the case record items and the days. Tests cover `summarize`. Tests cover `metric`.

## 3. The policy and the context

- [x] 3.1 Write `policy/wording.md`. Cover the membership tiers. Cover the copy availability rule. Cover the 14-day term. Cover the tier term caps. Cover the cap of three concurrent loans per borrower on both tiers. Cover the overdue and damage conduct. Cover the special collection referral. Add the front matter with source and version.
- [x] 3.2 Write `policy/manual.md`. State when the desk declines. State when it refers. State when the lead signs off. Add the front matter with source and version.
- [x] 3.3 Write the five context files. `glossary.yaml` holds the library terms. `plans.yaml` carries the source block, the two tiers `standard` and `research` with `base_loan_days` and `max_loan_days`, and the two empty keys `deductible_applies_to` and `add_ons`. `data_dictionary.yaml` holds the loan request fields and pins the line shape: kind `item`, `nights` with the requested days, and zero hours. `case_rules.yaml` holds the desk intake facts. `reference_data.yaml` holds the book catalog.

## 4. The seed

- [x] 4.1 Write `data/company.json`, `data/workers.json`, `data/customers.json`, and `data/contracts.json`. Northgate Public Library is the company. Two librarians serve the desk, and the lead approves over the limit. At least six borrowers hold memberships on both tiers. Each membership carries the engine fields: `add_ons`, `purchased_on`, `sold_through`, the trip fields, `travelers`, and `status`, with the active loan count beside them. Each borrower carries `previous_cases`.
- [x] 4.2 Write `data/cases.json` with at least eight loan requests. The set holds the approved checkout. It holds the no copy decline. It holds the cap decline. It holds the special collection refer. It holds the over limit renewal. The bulk request is a decline case, so no approval carries more than one line. Each case carries the engine fields: case type, dates, summary, story, items with description, category, and amount, `amount_claimed`, and documents. Each item carries the title, the ISBN, the copy counts, and the price. Add `data/security/` with the held-out cases, contracts, and customers, which the seed requires.
- [x] 4.3 Write `data/improvement.json` and `data/models.json`. Use the shape of the helpdesk pack. Tune the values for the library desk.
- [x] 4.4 Write the pack test that loads every seed record into the engine model of its kind: `Case`, `Item`, `Contract`, and `PreviousCase`. No record raises.

## 5. The instructions and the evals

- [x] 5.1 Write `instructions/case.md` and `instructions/queue.md`. Name the served tools only. The case instruction teaches the line shape: kind `item`, `nights` with the requested days, and zero hours. Write `instructions/recipe.md` and `instructions/improver.md` in the helpdesk shape.
- [x] 5.2 Write `evals/decisions.json` with one pinned decision per seed case. Each record carries `case_id`, `decision`, `award`, `tiny`, `reason`, and `reference`. Write `evals/held_out_cases.json` with `evals/held_out_decisions.json` for the held-out set. Add the pack tests: every seed case id names a decision, and no held-out case id names a queued case. Add the pack test that pins the served tool list over the instruction files.

## 6. The gates

- [x] 6.1 Run `uv run python validate.py library` from `crm/`. Repair the named files. Repeat until the exit is 0.
- [x] 6.2 Run `uv run python smoke.py library` from `crm/`. Repair the named files. Repeat until three decision lines print with exit 0.
- [x] 6.3 Run the crm Python suite. Run the complexity, duplication, and mutation gates on the new Python. Prove the pack tests cover the new lines and branches at 100 percent.

## 7. The e2e flow

- [x] 7.1 Make the e2e pack aware. The worker selection reads the workers of `CRM_DOMAIN`. The storage state keys follow the pack. The insurance specs stay out of a library run, and the library spec stays out of the default run. The config passes the variable through. The default run stays on insurance.
- [x] 7.2 Write `e2e/library_flow.spec.ts`. The spec signs in as the lead librarian. It opens the queue. It opens one loan request. It sees the pack words. Run it with `CRM_DOMAIN=library`.
- [x] 7.3 Run the default e2e suite on insurance. Prove no change.

## 8. Docs and delivery

- [x] 8.1 Update `crm/README.md` with the library sign-in rows and the pack line. Update `CLAUDE.md` with the library pack mention. Add the library terms to `glossary/business.md`.
- [x] 8.2 Commit the units as atomic commits. Push the branch. Open the pull request. Run the adversarial review. Merge.
