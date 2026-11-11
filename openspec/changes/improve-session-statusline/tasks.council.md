# Council Notes: tasks.md

## Author Summary

The tasks break the work into a test-first render section, a
verification section with the suite, the gates, and the validation, a
docs section, and a review and merge section.

## Reviewer Challenges

- Should-fix: no task covered the degraded separator test, the
  mixed-case level test, or the exact-line assertion.
- Taste: steps 2.3 and 4.3 packed several imperatives into one step.

## Resolutions

- Accepted: tasks 1.2 and 1.3 now cover the mixed-case level, the
  degraded separator, and the separator. Task 1.7 pins the exact
  standard line at 91 characters.
- Accepted: the multi-imperative steps stay, because the STE checker
  bounds each sentence and the run executes the steps in order.

## Remaining Risks

- None recorded.
