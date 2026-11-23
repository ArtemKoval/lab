## Context

Issue #242 asks for a dashboard control plus a POST endpoint that adds a
loan request to the crm library queue at run time, with no reseed and no
decision loss. The engine is pack-agnostic, so the route lands in the
engine and the words land in the pack.

## Goals / Non-Goals

**Goals:**

- The desk adds a request from the queue page, and it lands in `crm.db`
  with status `waiting`.
- The person and the membership validate server-side.
- The id series continues past the seed without collisions.
- The pack words drive the control, and other packs stay clean.

**Non-Goals:**

- Creating new customers or contracts at run time. The control picks
  existing ones. A runtime person-creation flow is a follow-up if the
  desk needs it.
- Seed-file edits for new requests.
- Any change to the decision or payment routes.

## Decisions

### D1: One generic route, pack-agnostic

The route is `POST /api/cases` in the engine, not a library route. The
engine carries no domain noun. The control's words ride the pack
vocabulary. A future pack gets the same route free. **derived**

### D2: The id series derives from the database

The scan runs over the cases without evaluation copies (the same filter
the queue read applies), reads the alphabetic prefix and the trailing
number of the highest id, and takes the next number. The seed ids run
`LN-5001..5008`, so a real seed continues at `LN-5009`. A database with
no cases falls back to `C-1`, so the route works for any pack.
**derived**

### D3: The pickers read the amended customer search

The backend already serves `GET /api/customers` as a Copilot-facing
search with a required name query behind the signed-in-worker guard. The
change amends that route: the name query turns optional, absent means
every customer, and the guard widens to the same worker and agent guard
the queue reads use. No new colliding route. The Copilot's named search
keeps working through the same path. The contracts-by-customer read is
new. **derived**

### D3b: The dashboard composes the pack-shaped payload, the route stays generic

The route writes the record the request carries and validates only the
customer and the contract. The pack-shaped defaults (the `checkout`
case type, the branch location words, the item category) are composed in
the dashboard's control from the pack vocabulary, so the engine carries
no domain noun and the record always satisfies the `Case` model. The
payload contract:

- required: `customer_id`, `contract_id`, `summary` (the desk's title,
  non-empty), `story` (non-empty), `items` with exactly one item
  (`description` = the title, `category` = the pack's item category word,
  `amount` = the replacement price)
- server-filled: `case_id` (the series), `submitted_on` (today when
  omitted), `status` = `waiting`, `documents` = `[]`, `amount_claimed` =
  the item amount
- refused: 404 on unknown customer or contract, 422 on an empty summary,
  story, or item list

`GET /api/customers` returns id and name only (no addresses or dates).
`GET /api/customers/{id}/contracts` filters by customer. Both sit behind
the worker and agent guard like every read. **derived**

### D4: The control renders from the pack vocabulary

The control reads its words from the pack vocabulary, so the library
words stay in the pack and a non-library pack shows no loan control. The
vocabulary already drives the dashboard's pack words. **observed**

## Risks / Trade-offs

- The route writes to the live database. A validation miss would write a
  broken row. The mitigation: the route validates the customer and the
  contract before any write, refuses empty required fields with a 422,
  and the tests pin the 404 and 422 paths.
- The id series scan adds one read per creation. The queue is small, and
  the scan runs on an indexed column.
- The id series derives from the max id, so a hand-inserted id above the
  series moves the series up. That is the data being the authority, not a
  defect.

## Migration Plan

No migration: the route writes the columns the seed writes. The feature
lands in one PR. A rollback is a revert.

## Diagram

The creation path, component view:

```text
+------------------+   POST /api/cases     +------------------------+
| QueuePage        |---------------------->| main.py create_case    |
| (add control)    |   customer, contract, |   - validate customer  |
|                  |   title, story, price |   - validate contract  |
+------------------+                       |   - next id from series|
                                           |   - write waiting row  |
                                           +-----------+------------+
                                                       |
         GET /api/customers                GET /api/customers/{id}/contracts
+------------------+                       +------------------------+
| pickers          |<----------------------| main.py reads          |
+------------------+                       +------------------------+
```

## Open Questions

- None. The issue carries the design notes, and the id policy plus the
  picker reads are the only decisions the code left open.
