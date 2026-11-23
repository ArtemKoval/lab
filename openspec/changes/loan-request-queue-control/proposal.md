## Why

The library desk cannot add a loan request at run time. The queue only
holds the cases the seed carries, so every real request needs a seed-file
edit plus a reseed, and the reseed drops the decisions the desk already
made. The desk needs a control on the queue page that puts a new request
in the queue, with a matching backend route that writes `crm.db` directly.
The request is ArtemKoval/lab#242, ported from the private child repo.

## What Changes

- A backend route creates a case at run time: `POST /api/cases` takes the
  customer, the contract, and the request text, validates that the person
  and the membership exist, generates the next free case id from the
  pack's id series, and writes the case with status `waiting` straight to
  the database. No seed rebuild and no decision loss.
- Two backend reads feed the control's pickers: a customer list (id and
  name) and a contract list filtered by customer.
- The queue page carries an "Add a loan request" control that posts the
  form and refreshes the queue, with the pack's own words.
- The dashboard keeps working for every other pack: the control reads its
  words from the pack vocabulary, so a non-library pack simply shows its
  own terms or none.

## Capabilities

### New Capabilities

- None. The route and the control extend two existing capabilities.

### Modified Capabilities

- `crm-engine`: the API gains the run-time case creation route and the two
  picker reads.
- `crm-library-domain`: the queue page gains the loan-request control and
  its words.

## Impact

- `crm/backend/main.py` — the new route and reads, with the id generation
  helper beside the route.
- `crm/backend/tests/` — route tests: creation, validation failures, and
  the id series.
- `crm/dashboard/src/pages/QueuePage.tsx` and `crm/dashboard/src/api.ts` —
  the control, the form, and the API client calls, with their tests.
- `crm/domains/library/` — the control's words ride the pack
  vocabulary. The seed files stay untouched.
- No schema migration. The case row already exists. The route writes the
  columns the seed writes.
- The pack validator and the smoke run are unaffected.
