# Council Notes: proposal.md

## Author Summary

The proposal adopts the `ub-mode` skill with provenance. It vendors the three companion gate tools under `tools/` at pinned commits. It folds the important discipline parts into the feature-pipeline skill. It wires CI to run the vendored suites and to gate the changed repository Python. It registers three setup units and pins everything in contract tests. ADR 0005 records the decision.

## Reviewer Challenges

- Author round, 13 revisions. The themes:
  - The crapper boundary rule (`--threshold 10` passes exactly 10).
  - Missing pass and fail signals per gate.
  - The CI trigger scope versus `paths-ignore`.
  - Suite locations, the `uml-viewer` exclusion note, and the registry unit shape.
  - README provenance pins and the Step 3 delta wording.
  - A README bullet gap and redundant `.gitignore` claims.
- Reviewer round, 7 required changes. The themes:
  - The CI gate is a no-op as written (`--changed` reads a clean tree).
  - The gate scope and exclusions are undefined.
  - `test_ci_workflow.py` pins the absence of mutation and flips by necessity.
  - The "CRAP below 10" wording contradicts the flag semantics.
  - The mutator CI budget is unstated.
  - The zsh-dependent failures need a policy.
  - The pipeline gates-section edit has no capability owner.

## Resolutions

- Accepted: explicit diff-derived paths for the CI gate. Scope and exclusions named. The contract-test flip planned in surfaces and tasks. Boundary wording stated as the flag enforces it (10 or less). Mutator budget with a worker cap and timeout. The CI-is-the-green-gate zsh policy. The gates-section edit assigned to `quality-gates`. Provenance in vendored READMEs. Registry unit house shape. The Step 3 delta stated as an extension. Pass and fail signals per gate. The `uml-viewer` exclusion recorded. The `.gitignore` work reduced to `.metrics/` and `target/`.
- Rejected: relocation of the vendored suites under `tests/` (breaks the upstream layout and enters root-suite collection through `testpaths = tests`). CI runs the gates with `--changed` (no-op on a clean tree).
- Deferred: migration of the existing `ruff` and `mutmut` configs to a follow-up change. The whole-tree gate ratchet waits for the measured baseline.

## Remaining Risks

- The dryer exit-code boundary is verified against the vendored code during apply (task 3.1), before the pipeline wording lands.
- The real mutation budget in CI is unknown until the first run. The design holds the worker cap, the timeout, and the tuning path.
- The unlicensed skill text ships with attribution. ADR 0005 records the risk and the replacement plan.

## Builder Check

A fresh builder read only the artifacts and raised 11 questions. One went to the user, who chose the gate scope. The crapper and dryer gates cover changed product and test paths with the workflow coverage run as LCOV input. The mutator gate covers changed product paths only, with the root pytest suite as its test command. The answer is recorded as design decision D10 and in the CI requirement and tasks 5.2 to 5.4. The 10 minor questions carry settles in the design notes and the tasks. The settles cover:

- Upstream URLs and launcher invocation under unit venv interpreters.
- The ADR 0005 commit task and the exit 3 e2e assertion.
- The verified `dev` extras and the STE treatment of the adopted rule names.
- The `pytest.ini` house pattern, the `metadata.ported` field names, and the fixture exclusion list.
