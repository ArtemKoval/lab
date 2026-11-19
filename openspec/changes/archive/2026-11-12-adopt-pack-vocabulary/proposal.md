# Proposal: adopt-pack-vocabulary

## Why

The dashboard speaks insurance on every pack. On the library pack, the case
page shows a "Contract" with a plan, add-ons, a trip with a destination and
travelers, and case fields named "Incident" and "Amount claimed". The words
make no sense for a loan desk, and a demo audience sees the mismatch. The
cause is structural: the core dashboard hardcodes the insurance words and
reads the insurance fields of the contract record, while the packs carry no
say in what the product shows. The engine's award is a plain number, and the
library pack's award is a loan term in days, so the interface prints
"$14.00" for a 14-day term in several places. A label swap alone cannot fix
that, because the unit travels with the number.

## What Changes

- Extend the pack manifest with a vocabulary section: a `labels` map from
  stable key ids to the pack's words, a `contract` presentation with a title
  and labeled rows over the contract record's fields, an `award_format` of
  `money` or `days`, and `messages` with the pack's words for
  the refusal family that names the limit: the over-limit refusal, the
  senior-worker refusal, the copilot's cant-sign-off refusal, and the
  contract-not-found refusal.
- Serve the vocabulary section on `GET /api/pack`, beside the declarations
  the endpoint already carries.
- Render the contract panel from the pack's rows, over the record's fields,
  with formats `text`, `date`, `money`, `days`, and `list`. The core
  dashboard reads no insurance field of its own.
- Render every domain word through the pack's labels, with the current
  English words as the fallback when a key is absent. The sweep covers the
  queue, the case page, the decisions and their held reasons, the
  calculation, the history panel, the scoreboard and evaluation pages, the
  settings, the improvement and recipe pages, and the copilot cards and
  their suggested questions. The sign-in page speaks before any pack is
  known, so its lead moves to pack-neutral core words.
- Format the award and the approval limit through the pack's award format.
  On the library pack the award reads "14 days", the settings input loses
  its dollars sign, and the refusal family names days, not dollars.
- Give the insurance pack the words it shows today, so its pages and tests
  stay as they are.
- Give the library pack the loan-desk words: Membership, Card, Tier, Borrower,
  Title, Copies requested, Received at, Replacement price, Issued, Sign off
  and issue.
- Update the library e2e spec and the vitest tests that pin changed words.
  The insurance e2e specs stay untouched.

## Capabilities

### New Capabilities

- `crm-pack-vocabulary`: The pack's words in the product. The manifest's
  vocabulary section, its pass-through on the pack endpoint, the pack's
  award format at every award display, the pack's refusal messages, and the
  generic contract and label rendering in the dashboard.

### Modified Capabilities

- `crm-domain-pack`: The manifest MAY carry the vocabulary section. The
  loader passes it through and refuses a pack whose vocabulary names an
  unknown award format.
- `crm-library-domain`: The library pack carries the loan-desk vocabulary:
  its labels, its contract rows, its award format of days, and its refusal
  messages.

## Impact

- `crm/backend/main.py`: `PackView` carries the vocabulary section.
- `crm/domains/loader.py`: the loader exposes the manifest's vocabulary
  section and validates the award format.
- `crm/domains/library/manifest.json` and
  `crm/domains/insurance/manifest.json`: the vocabulary sections.
- `crm/dashboard/src/`: a pack context with a label lookup, the generic
  contract panel, the award format at every award display, and the label
  swap across the pages that `crm/docs/vocabulary_inventory.md` lists. No component reads
  `contract.trip` or `contract.travelers` any more.
- Tests: vitest for the label lookup, the fallback, the contract rows, and
  the award formats. Pytest for the pack endpoint's vocabulary section and
  the loader's validation. The library e2e spec's pinned words move to the
  loan-desk words. The insurance pack's words do not change, so the
  insurance e2e specs need no edit.
- The copilot's suggested questions and the backend's refusal messages are
  part of the sweep. The copilot's answers themselves are model output and
  stay outside this change.
