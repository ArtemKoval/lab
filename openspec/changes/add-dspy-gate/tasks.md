# Tasks: add-dspy-gate

## 1. The bridge core (phase 0)

- [x] 1.1 Write `tools/dspy_gate/dspy_gate/scenarioparse.py`: heading and tag parse, WHEN/THEN extraction, stable slugs, source hashes. TDD through `tests/dspy_gate/`.
- [x] 1.2 Write `compile.py`: THEN clauses to Tier A, B, and C assertion objects, with the refusal contract for an unparseable THEN.
- [x] 1.3 Write `gatepolicy.py`: the `gates.yaml` reader with bounds and pins, and the PyYAML dependency.
- [x] 1.4 Write `lint.py`: the Gate 0 rules, the rubric existence rule, and the bounds rule, exit 0 and 2.
- [x] 1.5 Write `manifest.py` and `datasets.py`: the manifest writer and verifier (Gate 1, both directions), the per-scenario JSONL emitters, GENERATED headers.
- [x] 1.6 Write `codegen.py`: the generated Tier-A pytest module with the GENERATED header, stable test IDs.
- [x] 1.7 Write `cli.py` and `__main__.py`: the subcommands `lint`, `regen`, `verify`, and `check-manifest`, with `--json` and the exit contract.

## 2. The pilot capability and the generated suite

- [x] 2.1 Write `harness/triage.py`: the hand module with the four specimen behaviors, no model call.
- [x] 2.2 Run the bridge on this change: emit `openspec/eval_manifest.json`, the delta evals, and `tests/dspy_gate/generated/`, then commit the artifacts.
- [x] 2.3 Wire the generated Tier-A conformance module into the root suite and make it green with no network.

## 3. The gate runner (phase 1)

- [x] 3.1 Write `checks.py`: the Tier A, C, and D runners with the budget ceilings and self-describing failures.
- [x] 3.2 Write `evals.py`: the Gate 3 delta and frozen suite runner with the failure routes printed per scenario.
- [x] 3.3 Write `matrix.py`: the conformance matrix report for the pull request.
- [x] 3.4 Write `judge.py`: the Tier-B ensemble and the visual judge behind lazy dspy imports, stub-tested at the root.

## 4. The model factory and the optimizer (phase 2)

- [x] 4.1 Write the effective `tools/dspy_gate/gates.yaml` with the flash-everywhere role policy and the bounds.
- [x] 4.2 Write `lm.py`: the one model factory with lazy dspy imports and the `ZAI_API_KEY` gate.
- [x] 4.3 Write `optimize.py`: the Gate 2 runner with the holdout split, certification, and the artifact write contract, stub-tested at the root.

## 5. The surface (phase 3)

- [x] 5.1 Write `harness/preview.py` and the fixture page: deterministic content on a fixed port.
- [x] 5.2 Write the Playwright journey for the a11y-first rule, env-gated behind `DSPY_GATE_E2E=1`, with the browser install documented.
- [x] 5.3 Write `freeze.py`: the Gate 4 archive freeze for evals, baselines, and thresholds.
- [x] 5.4 Add the baseline governance rule to the verifier: no visual scenario without a baseline, no baseline without a scenario.

## 6. The learning loop (phase 4)

- [x] 6.1 Write `bank.py`: the JSONL store, the judge-gated write, the eviction on regression, and the similarity retrieval.
- [x] 6.2 Write `nightly.py`: the seven steps in order, idempotent, with the run report and the draft area for spec gaps.
- [x] 6.3 Prove the five safety rails with tests: holdout isolation, freeze discipline, the intent boundary, budget bounds, and reversibility.

## 7. Harness surfaces and wiring

- [x] 7.1 Write `.claude/hooks/spec-gates-protect.sh` and `.claude/hooks/spec-gates-bridge.sh`, and wire both in `.claude/settings.json` through the update-config skill. Time the hooks.
- [ ] 7.2 Update the intent-driven schema: the `gates.yaml` and `rubrics/` artifacts with templates and instruction text.
- [ ] 7.3 Update the `feature-pipeline` skill: the six gate steps, the regeneration rule, and the matrix rule, per the spec delta.
- [ ] 7.4 Write `.claude/skills/dspy-gate/SKILL.md` with the commands and the exit codes.
- [x] 7.5 Write `mcp_server.py`, register the server in `.mcp.json`, and add the settings keys and permissions per the spec delta.
- [ ] 7.6 Write `.github/workflows/spec-gates.yml` with the Gate 0 and Gate 1 jobs and the env-gated live suites. Extend `tests.yml`: the coverage sources, the gated roots, the lint line. Update the four pinned CI contract tests.
- [ ] 7.7 Write `.github/workflows/dspy-nightly.yml` with cron and dispatch triggers, the `DSPY_NIGHTLY_ENABLED` condition, and the key refusal step.
- [ ] 7.8 Write `tools/dspy_gate_setup/dspy_gate_setup.py` on the doctor contract, register the unit, and pass the completeness test.
- [ ] 7.9 Write `tools/dspy_gate/README.md`, the CLAUDE.md project entry, and the working-rules notes.

## 8. Delivery

- [ ] 8.1 Run the root suite, ruff, and the three gates on the changed paths. Hold the coverage floor at 100 percent for the new tool.
- [ ] 8.2 Run the adversarial review on the whole diff and fix the confirmed findings.
- [ ] 8.3 Open the pull request with the matrix, and merge after the review passes.
- [ ] 8.4 Archive with the freeze step and the two ADR records, and open the handover issue with the telemetry block.
