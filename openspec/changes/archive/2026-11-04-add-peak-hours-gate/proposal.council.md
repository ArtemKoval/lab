# Council Notes: proposal.md

## Author Summary

The author drafted the proposal with the four required sections, the new capability `peak-hours-gate`, and no modified capabilities. The draft carries the settled decisions. They cover the window and its boundary semantics, the block and allow sets, the deny rule, and the fail-open rule.

## Reviewer Challenges

- The draft dropped the required `## Capabilities` parent header that the template and the house form carry.
- The Impact section claimed a root-suite coverage floor that no listed change implements. CI enforces the floor through explicit lists in `tests.yml` and pinned substrings in `tests/claude_infra/test_ci_workflow.py`.
- The capability bullet contradicted What Changes on the deny message and dropped the boundary semantics.
- The clock source stayed unnamed. Hosts run in other zones.
- The shim interpreter sentence left the resolution order open.
- `dspy_gate nightly` drives optimize and certify and so burns GLM spend, but the settled list did not name it.
- A distant pronoun ("It also holds") reached across an intervening sentence, and "Internal errors fail open" had no testable exit code.

## Resolutions

- Accepted: the `## Capabilities` header is back, and the capability bullet now carries the boundary semantics, the full deny rule, and the fail-open exit code.
- Accepted: the Impact section now names the `tests.yml` `--cov` source, the gated root, the `.coveragerc` omit line, the pinned substrings, and the default quality gates.
- Accepted: the clock source sentence (UTC read plus the 8-hour offset), the two-step interpreter order, the repeated noun, and the ADR-at-archive line.
- Accepted with a note: `nightly` joins the blocked dspy_gate paths. The approved scope names "the paths that burn real GLM spend" under the broadest enforcement choice, and nightly is one. The flag goes to the user at proposal approval.
- Rejected: none.

## Remaining Risks

- The `nightly` inclusion goes past the literal approved list. The proposal approval settles it.
- The gate trusts the host clock. A wrong clock moves the window.
- Claude Code snapshots hooks at session start, so the wiring takes effect on the next session after the merge.
