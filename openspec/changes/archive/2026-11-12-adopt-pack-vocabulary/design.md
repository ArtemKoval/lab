## Context

The sweep behind `crm/docs/vocabulary_inventory.md` walked the
dashboard's user-visible strings. It found 52 that speak insurance. The worst offender is the contract panel: it reads the
insurance fields of the contract record (`plan`, `add_ons`,
`trip.destination`, `trip.trip_cost`, `travelers`), so the library
membership renders as a travel policy. Two deeper facts shape the design.
First, the engine's award is a plain number, and the library award is a loan
term in days, so the interface prints "$14.00" for a 14-day term in about
ten places, and two backend refusals interpolate `dollars(limit)` for a
limit that is days. Second, the pack endpoint `GET /api/pack` already
serves the pack's declarations to the dashboard, so the pass-through path
exists.

The material questions were settled with the user before this proposal.
Dispatches on the demo run live through the real agent. The Copilot gets
made to work with a model key and a Postgres in the demo stack. The
vocabulary sweep reaches every page.

## Goals / Non-Goals

**Goals:**

- One place per pack where its words live: the manifest's vocabulary
  section.
- A generic contract panel and one label lookup in the dashboard, with the
  current English words as fallback.
- The award in the pack's unit at every award display, in the dashboard and
  in the two backend refusals.
- The insurance pack keeps today's words, so its e2e specs stay untouched.

**Non-Goals:**

- No change to the engine's models: the award stays a number, the contract
  record keeps its fields.
- No change to model output, the copilot's answers, or the agent's words.
- No translation machinery beyond the flat labels map: one locale, one map.

## Decisions

- **The manifest carries the vocabulary.** `vocabulary` with `labels`,
  `contract` (`title` plus `rows` of `label`, `field`, `format`),
  `award_format`, and `messages`. The loader passes it through and refuses
  an unknown format, so a typo fails at load with a named key. The pack
  endpoint serves it beside the declarations.
- **The dashboard renders rows and keys, not fields.** One pack context
  feeds a `label(key)` lookup and the contract rows. `ContractPanel` reads
  the rows over the record and never touches `trip` or `travelers`. The
  fallback for an absent key is the current English word, so the sweep can
  move page by page.
- **The award format is a pack fact.** A small formatter takes the pack's
  `award_format`: `money` keeps today's rendering, `days` renders
  `14 days`, with no plural logic. The formatter exists in TypeScript and
  in Python, with parity tests over both packs. The verified call sites in
  `crm/docs/vocabulary_inventory.md` call it: the measures' cost of mistakes, the decision
  award chip and its calculation rows and footer, the decision panel's pay
  line, the not-allowed message, the evaluation page's mistake cost, and
  the settings input's unit. The queue's and the dispatch's outcome cells
  stay as they are, because the pack's own `summarize` composes their
  strings already, and the library line says `14-day loan issued`.
- **The insurance pack declares today's words.** Its labels map carries the
  strings the pages show now, its contract rows carry the plan, add-ons,
  purchase, sold-through, trip, and travelers rows, and its award format is
  `money`. Its pages and e2e specs stay as they are.
- **The library pack declares the loan desk.** Membership, Card, Tier,
  Borrower, Title, Copies requested, Received at, Replacement price, Issued,
  Sign off and issue, and the copilot's suggested questions about overdue
  titles and loan rules. Its membership rows map the loan desk onto the
  record's fields: the card number over `contract_id`, the tier over
  `plan`, the members over `travelers`, the valid-from and valid-to dates
  over the trip dates, the home branch over the trip destination, the
  issued-at desk over `sold_through`, the member-since date over
  `purchased_on`, and the loans held over `active_loans`.
- **A pack with no rows keeps today's panel.** Helpdesk and opsdemo declare
  no vocabulary tonight. Their contract panel keeps the core's current
  rendering, which the fallback rule states, and their words move in a
  follow-up. A vitest test pins today's insurance panel output, so the
  promise is checkable.
- **The refusal family is four templates.** The over-limit refusal in the
  backend, the contract-not-found refusal, the senior-worker refusal, and
  the copilot's cant-sign-off refusal all interpolate the limit through
  `money()` today. Each pack's `messages` carries all four, and the
  copilot's graph reads the pack's words through the loader. The insurance
  pack's templates carry today's strings, which three e2e specs pin, so
  those specs stay green.
- **The sign-in lead is pack-neutral core words.** The sign-in page speaks
  before any worker signs in, so `/api/pack` cannot serve it. Its lead
  becomes a sentence with no domain noun.
- **Held reasons are dashboard templates.** The two held reasons compose in
  `DecisionPanel` from codes and the award, so the labels map and the award
  formatter own their words. The agent's own free text stays as it is.
- **Small print, decided once.** The `days` format always writes `days`
  with no plural logic. An unknown label key or row field is dead data, not
  an error, because the fallback and the empty-row rule already answer it.
  The formatter exists twice, in TypeScript and in Python, with parity
  tests over both packs' formats.

## Risks / Trade-offs

- The sweep touches many components the night before a demo. The fallback
  keeps every page rendering when a key is missing, and the insurance e2e
  run plus the library e2e run prove both packs end to end.
- The money-formatting call sites for the award are easy to miss. The
  inventory file names them, and a vitest pass asserts the days rendering
  at
  each.
- A pack without a vocabulary section must behave as today. The loader's
  acceptance path and the endpoint's absent field carry tests.
