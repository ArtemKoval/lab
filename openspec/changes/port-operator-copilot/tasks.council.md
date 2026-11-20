# Council Notes: tasks.md

## Author Summary

The tasks build the pack in nine steps, prove it through the validator,
the smoke run, the suites, the quality gates, and the opt-in e2e lane, sync
the three docs surfaces, and close with the review, merge, archive, and
handover sequence.

## Reviewer Challenges

- Tasks named two instruction files, and the engine import needs four.
- The taught line shape missed `description` and `quantity`.
- No task extended `crm/playwright.config.ts`, which the e2e lane needs.
- The staged-set line missed the change folder, the ADR, and the
  regenerated eval manifest.
- The plan fields the scenario numbers rely on sat unpinned.
- The curated fleet carried no proof task for the routing decisiveness.

## Resolutions

- Accepted: task 1.7 names the four instruction files and the whole line
  shape, and task 1.9 covers all four in the served-tools test.
- Accepted: task 1.10 adds the playwright config branch.
- Accepted: task 4.1 names the full staged set.
- Accepted: task 1.5 pins `base_excess` and `per_repair_cap` per tier, and
  task 1.9 adds the fleet-match test.

## Remaining Risks

- The e2e lane stays opt-in because no gate variable exists in CI, so the
  merge proof for it is the local run with the stack up.
