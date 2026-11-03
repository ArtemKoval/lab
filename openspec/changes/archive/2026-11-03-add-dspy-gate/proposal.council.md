# Council Notes: proposal.md

## Author Summary

The author draft named the six new capabilities and the one modified capability, listed the twelve change bullets, and held the file near one page. The draft carried the user decisions: full scope, flash pins, fixture preview surface, default-off nightly run, and the gate-status MCP server.

## Reviewer Challenges

- Blocker: nine sentences used the banned word form `check(s)`. The STE rules file bans it without a determiner, and the write hook would block the artifact.
- Major: the Impact named `fastmcp` as the MCP dependency. The house pattern uses the `mcp` package with the pin `>=1.2.0,<2`.
- Major: three requirements in the intent-driven-harness spec pin `outputStyle`, `enabledMcpjsonServers`, and `permissions` as unchanged. The MCP registration changes two of those keys, so the delta must amend them.
- Major: the draft gave no trigger and no runner per gate. The proposal needed the run site for each of the six gates.
- Major: GENERATED eval artifacts under `openspec/**` could collide with the STE scan if the bridge emitted markdown there.
- Minor: the lint wording was wrong, and the draft missed the e2e variable name.
- Minor: the Impact missed the PyYAML dependency, the browser install site, the house tool layout, and the pinned CI substrings.
- Minor: two sentences in Why each joined two topics.

## Resolutions

- Accepted: all `check(s)` forms reworded to tests, assertions, or the bridge verifier. Verified against `tools/spec_ste_check/spec_ste_check/rules.py`.
- Accepted: the Impact now names the `mcp` package with the pin `>=1.2.0,<2`.
- Accepted: the Modified Capabilities entry now states the settings-key amendment, and the intent-driven-harness delta carries the MODIFIED requirement blocks.
- Accepted: the What Changes bullet now gives the run site for each gate.
- Accepted: the Impact now states the GENERATED artifacts are JSON, JSONL, or Python, never markdown.
- Accepted: six minor items went into the final text. They cover the lint wording, the four pinned CI substrings, the PyYAML dependency, and the browser install site.
- Accepted: the final text also names `DSPY_GATE_E2E=1` and follows the house tool layout.
- Rejected: none. Every challenge survived verification against the repository.
- Deferred: the full trigger table and the archive freeze mechanics move to design.md, per the template split of why and how.

## Remaining Risks

- The archive flow must run the freeze step so the frozen eval suites survive the spec sync. design.md owns this decision.
- The nightly workflow job condition must test the variable and the secret together. design.md owns the exact condition.
- The coverage floor covers the whole tool from the first pull request. The tasks must sequence tests with code to keep the floor green.
