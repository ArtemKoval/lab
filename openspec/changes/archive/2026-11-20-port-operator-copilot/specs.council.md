# Council Notes: specs/crm-garage-domain/spec.md

## Author Summary

The delta pins the garage pack on the library capability's shape: the
manifest, the loadability, the request line shape, the authorization
arithmetic, the sign-off question, the five protocol verbs, the seed data
and the queue fill, the policy documents, the four instruction files, the
eval records and coverage, the e2e lane, and the desk vocabulary.

## Reviewer Challenges

- The pack named two instruction files, but the engine reads `recipe` and
  `improver` at import time, and a pack without them raises on every
  backend import.
- The engine renders the `money` unit with the dollar prefix, so the
  pounds-on-render claims were unsatisfiable without an engine edit.
- The engine `Line` model requires `description` and `quantity`, so the
  taught line shape failed model validation as written.
- The fleet sign-off scenario pinned no fleet excess or cap, and the
  arithmetic named no excess field and no zero floor.
- The desk form posts the `days` field capped at 90, so the amount rides
  the case items, and the desk words had to pin the amount label instead.
- The strict validator flagged the arithmetic and protocol requirement
  texts past 500 characters after the folds.

## Resolutions

- Accepted: the spec pins the four instruction files, and the pack test
  covers all four.
- Accepted: the render claims state the pack's own words with no engine
  money prefix, and the divergence record carries the dollar prefix fact.
- Accepted: the line shape requirement pins `description` and `quantity`,
  and the arithmetic requirement splits from it.
- Accepted: the scenarios pin `base_excess` and `per_repair_cap` per tier,
  the arithmetic floors at zero, and the excess field name is pinned.
- Accepted: the desk words pin the amount label, and the award comes from
  the case items through the rules.
- Accepted: the line shape requirement split dropped both texts under the
  limit, and the change validates strict again.

## Remaining Risks

- The eval award values and the exact tier numbers settle at generation
  time, with the scenario numbers as the pins.
