# Proposal: resolve-referred-request

## Why

When the agent refers a request, the case lands decided with a Referred
chip and nothing else. On LN-5006, the special-collection checkout, the
lead librarian has nothing to click and nothing to fill in, although the
pack's own manual says the lead decides the referral in person. The demo
audience sees a dead end.

## What Changes

- Add `POST /api/cases/{case_id}/resolution`, for a worker who can sign off
  over the limit (the lead). The body names a resolution of `loan` or
  `decline`. `loan` carries the term in days: the engine resolves the
  declared outcome through the pack's resolve verb, records it, runs the
  case's effect, and the case stays decided with the outcome shown.
  `decline` carries a reason: the lead's decline replaces the referral as
  the case's decision, with the lead recorded as who decided.
- The route refuses a case whose status is not decided, whose decision is
  not a referral, and refuses a worker who cannot sign off over the limit.
- The case page shows the lead the two actions on a referred case, with the
  words from the pack's vocabulary: Issue the loan, with the term in days,
  and Decline the request, with a reason.
- The insurance pack carries its own words for the same actions.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `crm-engine`: The lead's resolution route and its refusals.
- `crm-library-domain`: The loan-desk words for the two actions and the
  resolution line the case shows afterwards.

## Impact

- `crm/backend/main.py` and `crm/backend/models.py`: the route, the request
  model, and the refusals.
- `crm/dashboard/src/components/DecisionPanel.tsx` (or a sibling component)
  and `crm/dashboard/src/api.ts`: the form and its call.
- Both packs' manifests: the new label keys.
- Tests: pytest for the route's paths, vitest for the form's gating, and a
  library e2e walk of the referral resolution.
