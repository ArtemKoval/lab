# Proposal: add-library-domain

## Why

The library assignment (issue
[ArtemKoval/library_crm#1](https://github.com/ArtemKoval/library_crm/issues/1))
asks for a minimal library management system: librarians work loan requests
against membership rules, and each borrower holds at most three concurrent
loans of 14 days. The crm engine already runs the queue, the decisions, the
sign-off, the runs, and the scoreboard, and it reads every domain word from
a pack. A pack for the library gives the full agent-facing product without
one engine edit.

## What Changes

- Add the `library` domain pack at `crm/domains/library/` with the manifest,
  the rules, the protocol, the policy documents, the context files, the seed
  data, the instructions, and the evals.
- Map the engine nouns to the library nouns: case = loan request, customer =
  borrower, contract = membership, worker = librarian, plan = membership
  tier, award = loan term in days, sign-off = lead librarian approval of a
  loan term over 14 days.
- Encode the assignment business rules: one copy per loan and checkout only
  when a copy is free, the 14-day term, the three concurrent loan cap, and
  the role split between the desk librarian and the lead librarian.
- Make the e2e suite pack aware, and add the library flow spec that signs in
  a library librarian and walks the loan desk flow.
- Update `crm/README.md`, `CLAUDE.md`, and the sign-in table for the library
  pack.

## Capabilities

### New Capabilities

- `crm-library-domain`: The library pack and its loan desk flow: the
  manifest and its declarations, the rules and the protocol, the policy
  documents, the seed data, the instructions, the evals, the validator and
  smoke gates, and the e2e flow.

### Modified Capabilities

- None. The pack contract in `crm-domain-pack` holds as written.

## Impact

- New pack at `crm/domains/library/` with pack-local tests, in the shape of
  the helpdesk pack. No engine module changes: `crm/backend/`, `crm/agent/`,
  `crm/context/`, `crm/domains/loader.py`, `crm/validate.py`,
  `crm/smoke.py` stay untouched.
- Small pass-through edits in `crm/e2e/workers.ts`, `crm/e2e/sign_in.setup.ts`,
  and `crm/playwright.config.ts`, so `CRM_DOMAIN=library` runs the library
  spec, and the default run stays on insurance.
- Docs: `crm/README.md` sign-in rows, the `CLAUDE.md` project line, and the
  library terms in `glossary/business.md`.
- The borrower self-service portal, account CRUD, inventory CRUD, and the
  borrower usernames and passwords stay out of this change. HARNESS.md
  records the cut and the next steps.
