---
name: Tech debt
about: Skipped gates and tests from a fast-mode prototype run
labels:
  - tech-debt
---

<!-- Open this issue before you merge the fast-mode pull request. The
     issue title starts with `tech-debt:`. Build the Telemetry block
     with the handover-telemetry tool (see the handover-telemetry
     skill) when the run produced observations. Remove secrets before
     you paste any artifact. -->

## Task

<!-- What the prototype was. Give the pull request link, and the
     observations that later work needs. -->

## Telemetry

<!-- Paste the tool output here: handover_telemetry build --out
     report.md. Write None when the run produced no observations. -->

## Debt items

<!-- One line per skipped step, gate, or test lane that applies to
     the task. Each item carries a next action. The unwaited CI run
     is always one item, except when branch protection held the merge
     for the green CI result. Write the CI item alone when nothing
     else applies. -->

## Follow-ups

<!-- Links to the paying pull requests, or write "None". The issue
     closes when the Debt items section shows None. Close the issue
     with the reason when the linked pull request closes without a
     merge. -->
