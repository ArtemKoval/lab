## Context

The desk librarian works loans at the desk, and the engine gives her
nothing: the decision route is the agent's, with the agent's key, and it
demands a case the agent started. The manual gives the desk three
decisions, and the over-limit approval holds for the lead exactly as the
agent's over-limit approvals hold.

## Goals / Non-Goals

**Goals:**

- One route for the desk's three decisions, on a waiting or
  left-for-worker case.
- The over-limit approval holds for the lead's sign-off, unchanged from
  the agent's flow.
- The words from the packs' vocabularies, on a form every signed-in
  worker sees on a waiting case.

**Non-Goals:**

- No change to the agent's routes or the dispatch flow.
- No new table: the decision rides the decisions table, the effect rides
  the effect runner.

## Decisions

- The route mirrors the sign-off skeleton and reuses the resolution
  route's outcome build: the pack's resolve verb over the case's first
  item, with the desk's days as the nights.
- The desk's over-limit approval holds, and the lead's sign-off runs the
  effect, exactly as the agent's held approvals do.
- The decided_by carries the desk librarian's name, so the record reads
  who decided at the desk.
- The rule sections ride the body, prefilled on the form with the pack's
  default wording label.

## Risks / Trade-offs

- The desk and a dispatch can race for the same case. The route refuses a
  case in progress, and the dispatch panel's own state rules refuse a
  case the desk decided, so the last writer wins a clean 409 either way.
