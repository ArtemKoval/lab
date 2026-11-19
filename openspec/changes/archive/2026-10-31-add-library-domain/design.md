# Design: add-library-domain

## The domain extraction

The free-form product brief of issue #1 names these entities and rules.

| Engine noun | Library noun | Notes |
| --- | --- | --- |
| company | Northgate Public Library | The library and its global numbers. |
| worker | Librarian | The lead signs off over-limit terms. The desk librarian does not. |
| customer | Borrower | A member of the library. |
| contract | Membership | The library card, with its tier and its live loan count. |
| plan | Membership tier | `standard` and `research`, with the term and cap fields. |
| case | Loan request | A checkout, a renewal, or a bulk request at the desk. |
| award | Loan term in days | One number per approval. |
| decision | approve, decline, refer | approve issues the loan. decline refuses it. refer sends it to the lead. |
| sign-off | Lead approval | A term over 14 days waits for the lead. |
| worker sign-in | Librarian desk account | The brief's seed librarian signs in as a pack worker with the dev password. |

The tier fields, pinned for the rules arithmetic: both tiers carry
`base_loan_days` at 14. The standard tier carries `max_loan_days` at 14. The
research tier carries `max_loan_days` at 28, so a research renewal above 14
days exercises the sign-off gate.

The business rules of the brief, and where each one lives:

| Rule from the brief | Where it lives |
| --- | --- |
| A title holds N copies, and a checkout needs one free copy | The wording section 3, the case items, and the evals. |
| The term is 14 days | The plan field `base_loan_days` in the rules arithmetic. |
| At most 3 concurrent loans, per borrower on both tiers | The wording section 5, the membership field `active_loans`, and the evals. |
| Authentication on every endpoint except login, and role-based access | The engine auth, unchanged. The lead signs off, and the desk does not. |
| A returned copy goes back on the shelf | The wording section 6 states the desk action, and the engine holds no copy table. |

The engine record models require insurance-shaped fields on every seed
record. The pack fills them with library meanings:

| Engine field | Library meaning in the pack |
| --- | --- |
| `trip` on a membership | The card's home branch: destination is the branch name, and the dates are the card term. |
| `travelers` on a membership | The members the card covers. |
| `amount_claimed` on a case | The replacement price of the requested title. |
| `amount` on an item | The list price of the title. |
| `previous_cases` on a borrower | Earlier loan requests, with the outcome and any fine paid. |
| `documents` on a case | The desk papers of the request, usually empty. |

## The C4 view

The pack plugs into the engine at the two declared seams, and nothing else.

```text
┌──────────────────────────── C4 context: the loan desk ────────────────────────────┐
│                                                                                   │
│  Desk librarian ──► Dashboard (SPA) ──► crm backend (FastAPI queue) ──► SQLite    │
│                              │                        │                           │
│                              │                        ▼                           │
│                              │              agent harness (LangGraph)             │
│                              │                        │                           │
│                              ▼                        ▼                           │
│                    auth service (workers)      pack: domains/library              │
│                                                               │                   │
│                     policy/wording, manual ◄─────────────────┤                   │
│                     context/ (glossary, plans, catalog) ◄─────┤                   │
│                     data/ (seed) + evals/ ◄───────────────────┘                   │
│                                                                                   │
└───────────────────────────────────────────────────────────────────────────────────┘
```

C4 component view of the pack: `rules.py` and `protocol.py` are the two code
seams the loader imports. The manifest declares the outcomes and the effects.
The engine calls `resolve` for an approved case, `gate` for the sign-off
question, `execute` for the loan record, `summarize` for the worker line, and
`metric` for the scoreboard.

## Alternatives, and why the pack wins

- **A standalone library app.** A new FastAPI app, a new SPA, new auth, and
  new tests rebuild what the engine carries. The assignment grades the setup
  around the agents, and the engine is that setup. Rejected.
- **Loan rows as engine cases, with a copy table in the engine.** The copy
  table needs engine routes, engine tables, and a superseding decision for
  new engine nouns. The brief says the copy state enters the case at intake.
  Rejected for this change, and recorded as a cut with a next step.
- **The pack.** The engine contract carries one numeric outcome, one gate,
  one effect, and one metric. The loan term fills each one. No engine edit.
  Chosen.

## The arithmetic boundary

The rules module stays pure and small. One approved request carries one
line of kind `item`, and its `nights` field holds the requested days, with
zero hours. The arithmetic caps the term at the tier's `max_loan_days` and
shows each step. The sign-off gate compares the term with the approval limit
of 14 days. Decline and refer conduct, like the copy rule and the three loan
cap, lives in the wording, and the eval set pins the expected decision per
case. The bulk request is a decline case in the seed, so no approval carries
more than one line. This is the house pattern of the insurance and helpdesk
packs.

## Risks

- **The three loan cap is advisory in the runtime.** The engine does not
  count a member's open loans, so the cap holds at the desk and in the
  evals, not in a database constraint. The design doc of the assignment says
  one sentence is enough, and HARNESS.md carries it.
- **The sign-off refusal speaks in dollars.** The engine formats the
  approval limit as money in its refusal text, and the library limit counts
  days. The pack accepts the wording, and HARNESS.md records the cut. A
  superseding decision with new engine wording can change it later.
- **The e2e suite pins pack words.** The insurance specs break under
  `CRM_DOMAIN=library`, so a library run excludes them and runs the library
  spec with pack-keyed workers and storage, and the default run stays on
  insurance.
- **The bulk case exercises lines, not copies.** A bulk request of five
  copies is a decline case when the copies are out, so the arithmetic never
  faces a multi-line award.
