## Context

A referral lands decided, and the engine has no worker path past it: the
outcome route is the agent's and demands a case in progress, and the
decide route refuses a case that already carries a decision. The pack's
manual says the lead decides a referral in person.

## Goals / Non-Goals

**Goals:**

- One route, the lead's authority only, that issues or declines.
- The smallest engine change: the sign-off skeleton, reused.
- The words from the packs' vocabularies.

**Non-Goals:**

- No new table: a decline updates the case's decision, the way a sign-off
  updates it with who signed.
- No agent-side change: the agent's referral stays on the record as the
  case's steps show it.

## Decisions

- The route mirrors `sign_off_case`: the same authority dependency, the
  same effect runner. A `loan` resolution builds the pack's
  `AwardRequest` from the case's first item with the lead's days as the
  nights, resolves through the pack, records the outcome, and runs the
  effect. A `decline` resolution updates the case's decision to a decline
  with the lead as who decided.
- The refusals: 403 with the pack's senior words for a desk librarian,
  409 naming the referral for anything but a decided referral.
- The dashboard form lives beside the decision on the case page, gated on
  the worker's authority, with the words from the pack's labels.

## Risks / Trade-offs

- A decline rewrites the case's decision, which loses the referral as the
  decision of record. The agent's referral stays visible in the steps, and
  the manual makes the lead's in-person decision the case's final word.
- The loan path needs the case's first item for the request line. Seed
  cases carry one; a case without items resolves to a 422 from the pack.
