# Inventory: the insurance words in the dashboard

The sweep's source list for this change. The sweep found 414
user-visible strings, and this table carries the insurance-flavored
ones. Every row carries the stable key id the manifest's labels map
uses, the words the library pack shows, and the component that shows
it. The full strings are untruncated.

| Key | Today's words | The library words | Where |
| --- | --- | --- | --- |
| queue.col.claimed | Claimed | Replacement price | pages/QueuePage.tsx:80 |
| queue.col.outcome | Award | Loan | pages/QueuePage.tsx:34-36 fallback, rendered at 84 |
| dispatch.col.award | Award | Loan | components/DispatchPanel.tsx:89 |
| case.lead.entry | {customer_name}'s {case_type} entry | {customer_name}'s {case_type} request | pages/CasePage.tsx:56 |
| case.incident | Incident | Requested (dd: the day the borrower wants the copy, then the desk that took the request) | pages/CasePage.tsx:96-99 |
| case.amount_claimed | Amount claimed | Replacement price (real dollars for this pack, so money() stays) | pages/CasePage.tsx:106-107 |
| items.title | Items claimed | Copies requested | pages/CasePage.tsx:120 |
| document.type | Carrier report | pack supplies its own type labels | pages/CasePage.tsx:160 |
| contract.title | Contract | Membership | components/ContractPanels.tsx:15 |
| contract.id | Contract | Card | components/ContractPanels.tsx:19-20 |
| contract.plan | Plan | Tier | components/ContractPanels.tsx:23-24 |
| contract.plan_value | Premium | Standard membership (pack plan labels) | components/ContractPanels.tsx:24 |
| contract.add_ons | Add-ons | none sensible — library data always carries an empty list; the pack row set should hide it | components/ContractPanels.tsx:27-32 |
| contract.purchased | Purchased | Issued | components/ContractPanels.tsx:35-36 |
| contract.sold_through | Sold through | Issued at | components/ContractPanels.tsx:39-40 |
| contract.trip | Trip | Card (dd: "{home branch}, {valid from} to {valid to}"); the whole dd composition moves to the pack row presentation | components/ContractPanels.tsx:43-47 |
| contract.trip_cost | Trip cost |  | components/ContractPanels.tsx:50-51 |
| contract.travelers | Travelers | Members | components/ContractPanels.tsx:54-55 |
| history.filed | {case_type label}, filed {date} | {case_type label}, requested {date} | components/ContractPanels.tsx:80-83 |
| history.paid | {outcome label}, paid {money(amount_paid)} | none sensible — the pack row should drop or reword the paid clause (see notes) | components/ContractPanels.tsx:85-88 |
| hold.gateway_refused | The Gateway refused the payment of {money(award)}, so it waits for a worker's sign-off. | The Gateway refused the loan term of {days} days, so it waits for the lead librarian's sign-off. — the amount is DAYS for this pack, so money() is wrong here (see notes) | components/DecisionPanel.tsx:67-70 |
| hold.over_limit | The payment of {money(award)} is over the approval limit and waits for a worker's sign-off. | The loan term of {days} days is over the approval limit and waits for the lead librarian's sign-off. — money() formats days (see notes) | components/DecisionPanel.tsx:74-79 |
| decision.award_amount | {money(payload.award)} (award amount span, class "award mono") | NO label swap possible — the library award is the loan term in days (14, 21, 0); it needs a pack-supplied unit/formatter, not a word (see notes) | components/DecisionDetails.tsx:16-18 |
| decision.calculation_caption | How the award was worked out | How the loan term was worked out | components/DecisionDetails.tsx:51 |
| decision.award_label | Award | Loan term (the amount beside it is money-formatted days — see notes) | components/DecisionDetails.tsx:61-66 |
| decision.manual_version | Cases manual version {manual_version} | Loan rules version {version} (the library source is "The Northgate loan rules, version 2026.2") | components/DecisionDetails.tsx:31-33 |
| not_allowed.text | Only a worker who can sign off awards over {money(approval_limit)} can {action}. {worker.name} can't. | Only a worker who can sign off loan terms over {limit} days can {action}. {worker.name} can't. — money() renders the 14-day limit as "$14.00" (see notes) | components/NotAllowed.tsx:12-20 |
| steps.sent_back_note | Worker's note | Librarian's note | components/StepList.tsx:122 |
| decision.approve | Approved | Issued (words already fit the loan desk per the pack's approve/decline/refer; presentation should come from PackView.resolutions) | format.ts:200 (decisionLabels) |
| case.type | Trip delay | pack supplies its own type nouns (Checkout, Renewal) | format.ts:118 (label fallback) |
| addons.adventure_sports | Adventure Sports | none — the pack should supply add-on names; the library data has none | format.ts:206 |
| addons.pre_existing_waiver | Pre-Existing Condition Waiver | none — pack-supplied | format.ts:207 |
| addons.electronics_plus | Electronics Plus | none — pack-supplied | format.ts:208 |
| contract.add_on_fallback | New add on | none — pack-supplied | format.ts:212 (addOnName fallback) |
| measure.straight_through | Straight-through | Without sign-off (share of requests decided at the desk with no lead-librarian sign-off) | measures.ts:16 |
| case.worker_col | Worker | Librarian | pages/EvaluationPage.tsx:118 |
| case.same_grounds_col | Same grounds | Same rule | pages/EvaluationPage.tsx:122 |
| scoreboard.lead | How the case agent scores against our workers' decisions. | How the case agent scores against the librarians' decisions. | pages/ScoreboardPage.tsx:31 |
| settings.lead | The approval limit and the rules for improving the case agent. | The loan term sign-off limit and the rules for improving the case agent. | pages/SettingsPage.tsx:57 |
| settings.group_approval_lead | Awards over the limit wait for a senior worker's sign-off. A new limit applies to later decisions only. | Loan terms over the limit wait for the lead librarian's sign-off. A new limit applies to later decisions only. | settingsFields.ts:48 |
| improvement.rounds_empty | No rounds yet. Starting a round has the improver read the latest results and propose a change to the case agent for a worker to approve. | No rounds yet. Starting a round has the improver read the latest results and propose a change to the case agent for a librarian to approve. | components/Rounds.tsx:35 |
| card.kind.customers | Customers and contracts | Borrowers and memberships | copilot.ts:23 (CARD_KINDS.customers) |
| copilot.suggest.wording | What does the contract wording say about baggage delays? | What do the loan rules say about overdue titles? (also suggested: "...about renewals?") | copilot.ts:85 (SUGGESTED_QUESTIONS) |
| outcome.paid | Signed off and paid | Signed off and issued | copilot.ts:117 (PAID) |
| outcome.may_have_paid | The Copilot stopped while signing off, so its page says whether it was paid. | The Copilot stopped while signing off, so its page says whether the loan was issued. | copilot.ts:122-123 (MAY_HAVE_PAID) |
| copilot.greeting.lead | Ask me about the queue, a entry or the contract wording, or have me do the work. I work as you, so I can see and do what you can. | Ask me about the queue, a request or the loan rules, or have me do the work. I work as you, so I can see and do what you can. | components/CopilotGreeting.tsx:20-21 |
| confirm.title.waiting | Sign off this award? | Sign off this loan? | components/ConfirmationCard.tsx:54 |
| confirm.sign_off_pay | Sign off and pay | Sign off and issue | components/ConfirmationCard.tsx:85 |
| worker.role | Senior Claims Handler | Library Lead (the library pack ships this already) | domains/insurance/data/workers.json:pin: crm/e2e/pages.spec.ts:38; vitest fixture dashboard/src/testing.tsx:29 says Senior Cases Worker |
| error.over_approval_limit | An award over {dollars(limit)} needs a worker's sign-off | none — the limit is days but dollars() formats it; the pack must supply the whole sentence, e.g. "A loan term over 14 days needs the lead librarian's sign-off" (see notes) | backend/main.py:196 (raised at 635, 638) |
| error.contract_not_found | Contract {contract_id} not found | Membership {membership_id} not found | backend/main.py:190 |

## The award's unit call sites

Every place an award value or the approval limit reaches the screen
through `money()` or a dollars unit, verified against the source. The
pack's award format governs each. The queue's and the dispatch's
outcome cells are not on this list: the pack's own `summarize` composes
their strings already, and the library pack's line says
`14-day loan issued`.

- `measures.ts:15` — the Cost of mistakes column, `money(m.cost_of_mistakes)`
- `Chips.tsx:71` — DecisionAward, `money(award)`, used on the evaluation page for the worker's award and the agent's award
- `DecisionDetails.tsx:17` — the decision's award span, `money(decision.payload.award)`
- `DecisionDetails.tsx:57` — the calculation rows, `money(line.amount)`, whose amounts are days on the library pack
- `DecisionDetails.tsx:64` — the calculation's footer cell, `money(award)`
- `DecisionPanel.tsx:62` — the pay line's award, `money(decision.payload?.award ?? 0)`
- `NotAllowed.tsx:16` — the not-allowed message's limit, `money(settings.current.approval_limit)`
- `settingsFields.ts:174` — the settings input's unit, `dollars` with a `$` prefix
- `EvaluationPage.tsx:165` — the case table's mistake cost, `money(entry.mistake_cost)`

Sites that stay money on every pack: the case's replacement price and
item prices (CasePage), the insurance history's amount paid, the round
spending limits, and the model prices on the models page. The packs'
own `summarize` lines already speak each pack's unit.
