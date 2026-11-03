# Proposal: add-dspy-gate

## Why

OpenSpec holds the intent as WHEN/THEN scenarios. Nothing proves that the code matches those scenarios.
The "DSPy Gate" guide at GitHub issue 77 gives the full plan. This change builds the plan, phases 0 through 4.

## What Changes

- Add a bridge tool at `tools/dspy_gate/`. It compiles OpenSpec change scenarios into datasets, compiled assertions, `eval_manifest.json`, and generated Tier-A conformance tests.
- Mark every bridge artifact with a GENERATED header. Make regeneration deterministic and idempotent. Route each module to a hand-written or an optimized implementation.
- Add the six lifecycle gates as mechanical tests. Gate 0 lints each proposal before its pull request. Gate 1 examines manifest coverage in CI on every pull request. Gate 2 optimizes and certifies on demand through the CLI. Gate 3 runs the conformance suites in the root suite and in CI. Gate 4 freezes the eval suites and baselines at archive. Gate 5 re-certifies after any model pin change.
- Each gate failure routes to one action: re-optimize, fix the harness, change the spec, or repair the environment.
- Add the DSPy harness layer with signatures, modules, tools, and hand modules. One model factory reads the model role pins from a governed `gates.yaml`.
- Pin glm-5.3-flash on every model role. Keep glm-5.3-flash on the vision judge. Keep thinking disabled on all flash roles. These pins differ from the guide values. design.md records the deviation. An ADR records it at archive.
- Add the surface dimension. Surface tags route each scenario to the dspy-eval, e2e-ui, e2e-visual, or agent-e2e runner.
- Add a deterministic fixture preview page on stdlib http.server. Playwright journeys, visual baselines, and the VLM judge bind to it behind `DSPY_GATE_E2E=1`. Visual baselines are governed artifacts that carry change IDs.
- Add the nightly learning loop with the steps collect, triage, expand, optimize, certify, promote, and escalate. The example bank takes writes only through the judge and evicts entries on regression. Five safety rails bound the loop.
- Add the scheduled GitHub workflow default-off. It runs only when the repository variable `DSPY_NIGHTLY_ENABLED` is true and the `ZAI_API_KEY` secret exists. The CLI runs the same loop locally at any time.
- Add ticket triage as the pilot capability with the guide specimen scenarios. Outage keywords route to on-call. Billing disputes route to billing. Escalation before reply is a judged scenario with a rubric.
- Extend the intent-driven harness. The change template gets `gates.yaml` and `rubrics/` artifacts. New hooks deny edits to GENERATED paths and run the bridge verifier after spec edits. The feature-pipeline skill gets the gate steps. The gate-status MCP server registers in `.mcp.json` and `.claude/settings.json`.

## Capabilities

### New Capabilities

- `spec-bridge`: The bridge compiles OpenSpec change scenarios into the eval manifest, datasets, compiled assertions, and generated Tier-A conformance tests. The bridge is the one writer of GENERATED paths. Regeneration is deterministic and idempotent. Routing sends each module to a hand-written or an optimized implementation.

- `spec-gates`: Six gates run as mechanical tests along the lifecycle. Gate 0 is the spec lint. Gate 1 examines bidirectional scenario-to-eval-case coverage. Gate 2 optimizes and certifies the modules. Gate 3 runs the conformance suites: the delta suite against the harness, and the frozen suites against regressions. Gate 4 freezes the eval suites and baselines at archive. Gate 5 detects drift and starts re-certification when a model pin changes. Each gate failure routes to re-optimize, fix the harness, change the spec, or repair the environment. A gate-status MCP tool gives the gate state and the conformance matrix.

- `gate-harness`: The harness layer holds signatures, modules, tools, and hand modules. One model factory reads model role pins from a governed `gates.yaml`. The pins put glm-5.3-flash on every role, keep glm-5.3-flash on the vision judge, and keep thinking disabled on flash roles. Assertion tiers A, B, C, and D set the passing rules. Tier A is hard and deterministic. Tier B is an LM judge with a rubric, an ensemble of 3, and temperature 0. Tier C is trajectory assertions over tool-call order. Tier D is budget assertions with p95 tokens and latency.

- `gate-surface`: Surface tags route scenarios to the dspy-eval, e2e-ui, e2e-visual, and agent-e2e runners. A small deterministic fixture preview page on stdlib http.server is the fixed e2e target. Playwright journeys follow the a11y-first rule. Visual baselines are governed artifacts that carry change IDs. A VLM judge ensemble examines the visual runs. All e2e bindings need the `DSPY_GATE_E2E=1` gate.

- `gate-learning`: The nightly loop runs collect, triage, expand, optimize, certify, promote, and escalate. An example bank takes writes only through the judge and evicts entries on regression. Five safety rails bound the loop: held-out certification, freeze discipline, the intent boundary, budget bounds, and reversibility. The scheduled GitHub workflow is default-off. It runs only when the repository variable `DSPY_NIGHTLY_ENABLED` is true and the `ZAI_API_KEY` secret exists. The CLI runs the same loop locally. The loop drafts OpenSpec changes for recurring spec gaps, and humans decide.

- `ticket-triage`: A hand-written deterministic module triages tickets. The guide specimen scenarios define the behavior. Outage keywords route to on-call. Billing disputes route to billing. Escalation before reply is a judged scenario with a rubric.

### Modified Capabilities

- `intent-driven-harness`: The change template gets `gates.yaml` and `rubrics/` artifacts through a schema and templates update. The settings-key requirements amend: `enabledMcpjsonServers` and `permissions` gain the gate-status server entries, and `outputStyle` stays unchanged. New hook groups deny edits to GENERATED paths and run the bridge verifier after spec edits. The feature-pipeline skill gets the gate steps.

## Impact

- The tool follows the house layout: `tools/dspy_gate/dspy_gate/` with `cli.py` and `__main__.py`, plus `pyproject.toml`, `ruff.toml`, and `README.md`. A setup doctor lands at `tools/dspy_gate_setup/`, and a unit joins `tools/project_setup/registry.json`.
- The CLI core is standard library except the `gates.yaml` reader, which uses PyYAML as a run-time dependency. The shared repository venv gains PyYAML too. dspy stays an optional extra for the live paths. The MCP wrapper uses the `mcp` package with the pin `>=1.2.0,<2`, on the zai-routing-audit pattern. Playwright rides the e2e extra, and the e2e job installs the chromium browser.
- The bridge writes `openspec/eval_manifest.json`, `openspec/changes/*/evals/`, `openspec/specs/**/evals/`, and `tests/dspy_gate/generated/`. These GENERATED artifacts are JSON, JSONL, or Python, never markdown, so the STE scan never reads them. The new hooks protect these paths.
- The new hooks `.claude/hooks/spec-gates-protect.sh` and `.claude/hooks/spec-gates-bridge.sh` join the `hooks` object in `.claude/settings.json`. `enabledMcpjsonServers` and `permissions.allow` gain the gate-status server entries.
- A new workflow `.github/workflows/spec-gates.yml` runs Gate 0 and Gate 1 on pull requests, and holds the env-gated live suites. `tests.yml` gains one lint line, the new coverage sources, and the gated roots. Four pinned substrings in `tests/claude_infra/test_ci_workflow.py` update with it.
- The root suite coverage floor covers `tools/dspy_gate` from the first pull request. The generated conformance tests count toward that floor.
- The feature-pipeline skill gets the gate steps. CLAUDE.md gets the project entry and the spec gate rules.
