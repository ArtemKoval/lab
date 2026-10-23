# Council Notes: proposal.md

## Author Summary

Adopt the intent-driven template into the Claude Code harness: schema switch, eleven skills, four agents, ADR folder with two seed records, and the review discipline, with spec-as-source installed but disabled.

## Reviewer Challenges

- The proposal seeded one ADR record while the design, tasks, and spec delta required two.
- The proposal called `acceptance-test-authoring` a sub-skill of `spec-as-source`; upstream ships it as an independent skill, so "leave both disabled" had no config line for the second skill.
- The proposal named `openspec-verify-change`; the CLI owns that skill name.

## Resolutions

- Accepted: two seed records named in the proposal (ADR-0001 and ADR-0002).
- Accepted: eleven independent skill directories; only `spec-as-source` is disabled through commented rules.
- Accepted: the port ships as `verify-change`.

## Remaining Risks

- None carried at proposal level.
