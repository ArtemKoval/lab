# Proposal: adopt-ub-mode

## Why

The delivery pipeline states its quality gates as examples (`ruff C901`, `mutmut`, `xenon`). No gate tool in the repo measures complexity and coverage together, and none finds duplicate code. The `ub-mode` skill from `unclebob` carries a reduced engineering discipline and names three deterministic gate tools. The user asked to adopt the skill, the tools, and the important parts of the discipline into the pipeline.

## What Changes

- Vendor three upstream tools as owned code under `tools/`. Each gets its 0BSD license file, its launcher, and its own test suite in the upstream layout:
  - `tools/crapper` at upstream commit `6fd92c4c9bcc56efb64a2f8743d5a2993bcfd42d`. CRAP scores: `CRAP = CC² × (1 − coverage)³ + CC`.
  - `tools/dryer` at upstream commit `66ff6d21a42c04afcad89c78a80066176d1294b0`. Structural duplicate detection with Jaccard similarity.
  - `tools/mutator` at upstream commit `a5a0cb803b66e0cdb8bf471b3b08af701d424a41`. Mutation testing. It reads function names from the sibling `../crapper`, which the `tools/` layout gives it.
  - Each vendored README gains an adoption note with the upstream URL and the pinned commit. The `uml` launcher of crapper ships with the tree for suite fidelity. The `uml-viewer` tool stays out. The skill's local section records that exclusion.
- Adopt the `ub-mode` skill at upstream commit `57a8bdd28e45ed41900ace0bafa2ff76dd9ed70f` as `.claude/skills/ub-mode/SKILL.md`. The upstream body stays unchanged, plus one local section. The frontmatter gains provenance. The upstream repository has no license file, and the ADR records that gap and the accepted risk.
- Extend the feature-pipeline skill:
  - One new subsection under the cross-cutting rules carries the three-phase frame: First Make it Work, Then Make it Right, Practice. The subsection adds the rules the pipeline lacks. They cover: one decision in one place, the data shape before the logic, redesign from first principles, attack the premise, and subtract before you add.
  - Step 3 gains the upstream test rule as an extension of its present wording. A test that still passes when every function returns nothing is not a behavior test. The step gains the rule to throw such a test out.
  - Step 10 gains the commit message rule: each commit says why, what changed, and how you proved it.
  - The Quality gates section names the three vendored tools as the default gates for new Python changes. The crapper gate holds the worst CRAP at 10 or less: `crapper --threshold 10` exits 2 when the worst score exceeds 10. The dryer gate holds similarity at or below 0.8 with `--threshold 0.8`. The mutation gate names `mutator` next to `mutmut`. The apply step verifies the dryer boundary and the exit codes against the vendored code before the spec states them.
- Register one project-setup unit per tool in `tools/project_setup/registry.json`. Each unit has `kind: dependency-file`. The install command builds the tool venv and installs the tool editable with its dev extras. The check command runs through the unit venv interpreter. The upstream launchers also create their own `.venv` on first use.
- Extend CI (`tests.yml`):
  - CI builds the three tool venvs and runs each vendored suite from its vendored location with the unit venv interpreter.
  - CI gates repository Python on every pull request that runs `tests.yml`. The gate step derives the changed Python paths from the pull request diff. The checkout fetches the base branch first. The step passes the paths to the tools as explicit arguments. The `--changed` flag reads the working tree, which is clean in CI, so CI never uses it. The crapper and dryer gates cover the changed product and test paths, with the LCOV form of the workflow coverage run as their coverage input. The mutator gate covers the changed product paths only, and runs the root pytest suite as its test command.
  - The gate scope is the repository-owned Python: `tools/plan_exec`, `tools/spec_ste_check`, `tools/project_setup`, `tools/devcontainer_init`, and `tests/`, minus the vendored tool trees and the deliberate-violation fixtures. `fde/` and `llm_ops/` stay out through the `paths-ignore` of the workflow.
  - The mutator gate runs only the mutants of the changed product paths. The step caps the workers and carries an explicit timeout as its runtime budget. The first CI run records the actual cost, and a follow-up tunes the budget if it is too high.
  - The gate venvs carry `pytest` and `coverage` from the start, so no gate run installs tooling on demand.
  - The two crapper tests that need `/bin/zsh` are the known local failures. CI is the green gate. Runners ship zsh.
  - `tests/claude_infra/test_ci_workflow.py` pins today that `tests.yml` names no mutation tool. This change flips that pin on purpose and states the new policy in its docstring.
- Add `.metrics/` and `target/` to the root `.gitignore`. The present `.venv/` pattern already covers the tool venvs.
- Pin the adoption in `tests/claude_infra/`: skill provenance, vendored layout, license files, README pins, registry units, and the pipeline integration.
- Add an opt-in e2e test at `tests/quality_gates/` behind `UB_TOOLS_E2E=1`. It runs the three launchers against a small fixture tree. It asserts exit 0 on a conforming fixture, exit 2 above each threshold, and exit 3 for a surviving mutant. It skips when the venvs are absent. `pytest.ini` gains `UB_TOOLS_E2E` in the marker docstring.
- Record the decision in `adr/0005-adopt-ub-mode-and-quality-tools.md`.
- Update `CLAUDE.md` (Projects and skills entries) and the root README (tool and skill entries). The vendored upstream READMEs document the tools.

## Capabilities

### New Capabilities

- `quality-gates`: The three vendored gate tools as this repository uses them. Invocation and thresholds, the pipeline gate-section contract, the registry units, the CI gating of changed repository Python, and the e2e smoke.
- `ub-mode-discipline`: The `ub-mode` skill and the discipline parts that land in the delivery pipeline. Provenance, the local gates section, the trigger, the pipeline subsection, and the Step 3 and Step 10 edits.

### Modified Capabilities

None. The CI and feature-pipeline edits are additive, and every SHALL in the `intent-driven-harness` spec stays true.

## Impact

- New Python venvs under `tools/{crapper,dryer,mutator}/.venv` with `tree-sitter` and `tree-sitter-language-pack` (small wheels). Python 3.11 or newer.
- CI gains three venv builds, three vendored suites (6 s, 1 s, and 53 s measured), and three gate runs. The mutation gate adds minutes to a pull request that touches gated Python.
- The gate runs and the e2e smoke write `.metrics/` and `target/` scratch under the repo root. Both stay untracked.
- The existing per-tool gate configs (`ruff` and `mutmut` in `tools/zai_routing_audit`, `fde`, and `llm_ops/eval`) stay as they are. Migration to the new tools is a follow-up.
- Surfaces touched: `tools/`, `.claude/skills/feature-pipeline`, `.claude/skills/ub-mode` (new), `tests/claude_infra/` (including `test_ci_workflow.py`), `tests/quality_gates/` (new), `pytest.ini`, `.github/workflows/tests.yml`, `.gitignore`, `tools/project_setup/registry.json`, `CLAUDE.md`, `README.md`, `adr/`.
