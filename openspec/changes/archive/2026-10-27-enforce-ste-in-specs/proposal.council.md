# Council Notes: proposal.md

## Author Summary

The author drafted a proposal with one new capability, `spec-ste-enforcement`, and no modified capabilities. The draft carried the fixed decisions: gate scope, mechanical rule set, pytest gate plus write-time hook, fail-open degradation. It froze a violation census of 16 and a file count of 10, assumed no `.coveragerc` edit, and named `python -m spec_ste_check` without a module-resolution story.

## Reviewer Challenges

- BLOCKER: the spec file count is 11, not 10. The census missed the `plan-exec` spec and the updated `intent-driven-harness` spec.
- BLOCKER: the census of 4 `provide` uses is wrong. The repo holds 7 real uses plus verb uses of `check`. Numbers frozen before the checker exists drift.
- BLOCKER: without a `.coveragerc` omit line for the new `__main__.py`, the 100 percent branch coverage floor fails the suite.
- BLOCKER: `python -m spec_ste_check` cannot import the package from the project root. Nothing installs the lab tools. The fail-open rule would then allow every write.
- BLOCKER: `intent-driven-harness` owns the settings hooks surface and the CI coverage requirement, so the change modifies that capability. Precedent: the 2026-10-26 archived change listed it as modified for the same reason.
- IMPROVEMENT: name the procedural-or-descriptive classification, the code exemption, the `check`-as-verb heuristic home, and the conftest path depth. Add a lint gate for the new tool. Note that the gate covers this change's own documents (bootstrap hazard). Say that the hook script, not Claude Code, filters paths.
- TASTE: the Why section held 3 sentences against a template of 1 to 2. The word "unit" collides with the registry units.

## Resolutions

- Accepted: all five blockers. The final proposal drops frozen counts. It adds `.coveragerc` and the lint step. It carries the `PYTHONPATH` plus interpreter-fallback story. It lists `intent-driven-harness` as modified with the two requirement-level changes. I verified every blocker against the repo before I accepted it.
- Accepted: the improvements. The rule bullet names the exemption and hands the sentence model to the design. The rewrite bullet covers the change documents.
- Accepted: the taste notes. The Why now holds 2 sentences, and "unit" became "part".
- Rejected: none.

## Remaining Risks

- The sentence model for headings, bullets, tables, and fenced code is a design decision. The proposal asserts the rule set is mechanical without it.
- The true violation census stays unknown until the checker runs. The rewrite pass is census-driven, so the implementation tasks must allow for more than the 12-plus-4 the first scan found.
- The `check`-as-verb heuristic needs a false-positive review against the corpus. The design records it.
