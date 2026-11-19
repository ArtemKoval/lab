# Proposal: desk-decides-waiting-request

## Why

The desk librarian has no controls on a waiting request. The agent works
the queue through dispatches, and the lead resolves referrals, but Iris,
the desk librarian, cannot work a loan herself, although the pack's manual
gives the desk its own decisions: approve a term of 14 days or fewer,
decline, or refer to the lead librarian. On stage the second librarian is
a spectator.

## What Changes

- Add `POST /api/cases/{case_id}/worker-decision`, for any signed-in
  worker, on a case that waits or is left for a worker. The body names a
  decision of `approve`, `decline`, or `refer`, with a reason, the rule
  sections relied on, and, for an approval, the term in days and the
  pack's benefit line.
- An approval resolves the declared outcome through the pack's resolve
  verb, records the decision with the worker as who decided it, and runs
  the case's effect: the desk issues the loan. A term over the approval
  limit holds the case for the lead librarian's sign-off, the way the
  agent's over-limit approvals hold.
- A decline records the decline. A referral records the referral for the
  lead, whose resolution form already sits on the case page.
- The case page shows a waiting or left-for-worker case the desk's
  decision form to every signed-in worker, with the words from the pack's
  vocabulary.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `crm-engine`: The desk's decision route and its refusals.
- `crm-library-domain`: The loan-desk words for the desk's decision form.

## Impact

- `crm/backend/main.py` and `crm/backend/models.py`: the route, the request
  model, and the refusals.
- `crm/dashboard/src/components/DeskDecisionForm.tsx` (new),
  `crm/dashboard/src/pages/CasePage.tsx`, and `crm/dashboard/src/api.ts`:
  the form and its call.
- Both packs' manifests: the desk's label keys.
- Tests: pytest for the route's paths and gates, vitest for the form, and
  the runbook's desk beat.
