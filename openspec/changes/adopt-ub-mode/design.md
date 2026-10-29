# Design

## Context

Facts come from the review round on 2026-10-28 and from a preflight on this machine. The author round gave 13 revisions, and the primary agent accepted 11. The reviewer round gave 7 required changes, and the primary agent accepted all.

- The four upstream repos at the pinned commits are real. The skill repo carries no license file. The three tool repos carry 0BSD licenses and declare `tree-sitter>=0.24` and `tree-sitter-language-pack>=0.7` (wheels of about 2.5 MB) on Python 3.11 or newer. Each `pyproject.toml` declares a `dev` extra with `pytest>=8`.
- Preflight on this machine: crapper suite 144 passed and 2 failed, dryer 80 passed, mutator 76 passed. The two crapper failures need `/bin/zsh`, which the `uml` launcher uses as its shebang. GitHub ubuntu-24.04 runners ship zsh. Suite cost: 6.3 s, 0.6 s, and 53 s.
- `mutator` requires `crapper` as a sibling checkout (`../crapper`). The `tools/` layout gives it that sibling.
- `crapper --changed` reads `git status --porcelain`. A CI checkout has a clean working tree, so `--changed` selects nothing there. `--threshold N` exits 2 when the worst CRAP score exceeds N, so a score of exactly 10 passes with `--threshold 10`.
- `tests.yml` runs one root pytest command with coverage over `plan_exec` and `spec_ste_check` at 100 percent, plus ruff on two tools. Its `paths-ignore` keeps `fde/**` and `llm_ops/**` out. `tests/claude_infra/test_ci_workflow.py` pins today that the workflow names no mutation tool, so this change flips that pin on purpose.
- The registry unit shape is fixed: `id`, `kind`, `purpose`, `check` (word list), `install`, `requires`. The project-setup skill reads the registry at run time, so the three units need no skill edit.
- The root `.gitignore` already carries `.venv/` at any depth. The gate runs add `.metrics/` and `target/` at the analyzed root.
- `openspec/config.yaml` exempts vendored upstream files from the ASD-STE100 prose rules. The skill body stays upstream prose. The local section and all new repo prose follow STE.
- The existing per-tool gate configs (`ruff`, `mutmut` in `tools/zai_routing_audit`, `fde`, `llm_ops/eval`) stay untouched in this change.

## Goals / Non-Goals

Goals:

- Three deterministic default gates for new Python changes: CRAP at 10 or less, similarity at or below 0.8, and mutation with no survivors.
- CI that gates the changed repository Python and runs the three vendored suites on every qualifying pull request.
- An honest adoption record: provenance frontmatter, vendored README pins, contract-test pins, and ADR 0005 with the license note.
- A pipeline that carries the adopted discipline where the repo can see it.

Non-Goals:

- No adoption of `uml-viewer`. The skill names it, and the local section records the exclusion.
- No migration of the existing `ruff` or `mutmut` configs. A follow-up change owns it.
- No whole-tree gate in CI. The gate stays diff-scoped in this change. A ratchet is a follow-up once the baseline is known.
- No hook enforcement of the discipline. The pipeline text informs, as ADR 0003 decided for the charter.
- No change to `build.yml` or the fde packaging.

## Decisions

**D1 - Vendor the full upstream trees at pinned commits.** Each of `tools/crapper`, `tools/dryer`, and `tools/mutator` receives the upstream working tree without `.git`. The tree carries the source, the launcher, `pyproject.toml`, `LICENSE`, its `tests/`, and its `.gitignore`. The `uml` launcher of crapper ships for suite fidelity. Each vendored README gains an adoption note with the upstream URL and the pinned commit. Alternative rejected: install from upstream at setup time. A clone build would need the network, and the mutator sibling requirement would drift.

**D2 - The CI gate derives explicit paths from the pull request diff.** The gate step fetches the base, lists the changed gated paths with `git diff`, and passes them as arguments. CI never uses `--changed`. Alternative rejected: `--changed` in CI. It reads the working tree, which is clean there, so it would gate nothing.

**D3 - Thresholds follow the skill, stated as the flags enforce them.** The crapper gate runs `--threshold 10`. A score of 10 or less passes. The dryer gate runs `--threshold 0.8`. The apply step verified the rules against the vendored code. Dryer reports pairs at a score at or above the threshold, and upstream dryer always exits 0 on findings. The owned copy gains one flag, `--fail-above`. It exits 2 on a reported pair. Owned tests sit beside the upstream suite. The upstream defaults (30 and 0.82) stay available to local runs.

**D4 - The mutator CI step carries an explicit budget.** It mutates only the changed gated paths, caps workers, and carries a step timeout. The first CI run records the real cost. A follow-up tunes the budget or scopes the test command if the cost is too high. Alternative rejected: whole-tree mutation on every pull request. Its runtime is unbounded.

**D5 - The mutation pin in the workflow contract test flips on purpose.** `test_ci_workflow.py` asserts today that the workflow names no mutation tool. The test update states the new policy in its docstring. The pin stays false only for the old policy.

**D6 - The vendored suites run from their vendored location.** CI calls each suite with its unit venv interpreter. Alternative rejected: relocation under `tests/`. The root pytest collects `tests/` only, and the move would break the upstream layout that keeps pin bumps clean.

**D7 - The e2e smoke follows the house pattern.** `tests/quality_gates/` hosts it, `UB_TOOLS_E2E=1` gates it, and it skips without the variable or a missing venv. It asserts exit 0 on a conforming fixture, exit 2 above each threshold, and exit 3 for a surviving mutant. The boundary scenario runs crapper with `--threshold 1` on a fixture whose worst score is exactly 1. The case proves that only a score above the threshold fails. `pytest.ini` names the variable in the marker docstring.

**D8 - Provenance lives in four places.** The skill frontmatter (with `license: none - unlicensed upstream`), the three vendored README notes, the contract tests, and ADR 0005. The ADR records the accepted risk of the unlicensed skill text and the replacement plan if the risk ever matters.

**D9 - CI is the green gate for the two zsh-dependent tests.** A host without zsh sees two known failures in the crapper suite. If a runner ever lacks zsh, the step installs it or deselects the two tests with a written reason.

**D10 - The repo-code gate scope follows the user's answer, with one review-driven carve-out.** The gate whitelist is the four owned tools and `tests/`. The crapper gate covers changed product and test paths. The coverage run measures the test paths too, so a changed test file scores its own coverage instead of 0 percent. The dryer and mutator gates cover changed product paths only. The review found eight pre-existing structural clones at or above 0.8 in one test file. A dryer run over changed test files would fail CI on shape the change did not create. The mutator test command is the root pytest suite through the shared venv. Mutating test code against the suite that runs it gives noisy verdicts, so the mutation scope stays on product code. CI runs each launcher directly, and the launcher selects its unit venv. The apply run found one mechanism fix the gate needs. The test conftests resolved their repo root through symlinks, so the mutator worker overlay imported the original file, and every mutant survived. The four conftests now use `Path.absolute()`, and the overlay imports the mutated copy.

Builder-check settles folded into this design: all three vendored `pyproject.toml` files declare a `dev` extra (`pytest>=8`), seen in the preflight. The skill provenance uses the house `metadata.ported` shape with `from`, `commit`, and `license`. The e2e asserts exit 3 on a surviving mutant. Upstream URLs: `github.com/unclebob/{crapper,dryer,mutator}`.

## Wiring

The wiring uses a lightweight C4-inspired container view in ASCII. The superpowers design used the same format. Containers are runnable units. Components live inside them.

```
 user / agent session
   |
   | invokes /ub-mode or follows the pipeline
   v
+---------------------------------------------+
| Claude Code harness                         |
|  .claude/skills/ub-mode   (adopted skill)   |
|  .claude/skills/feature-pipeline            |
|    cross-cutting rules: three-phase frame,  |
|    five adopted rules, default gates        |
+------------------+--------------------------+
                   | names as default gates
                   v
+------------------------------------------------------------+
| tools/ (vendored, 0BSD, pinned)                            |
|  +-----------+   reads names from   +-----------+          |
|  | crapper   |<--------------------/| mutator   |          |
|  | CRAP<=10  |   sibling ../crapper | kills all |          |
|  +-----------+                      +-----------+          |
|  +-----------+                                             |
|  | dryer     |  similarity <= 0.8                          |
|  +-----------+                                             |
+---------+--------------------------+-----------------------+
         | registers units           | runs launchers on fixtures
         v                           v
+------------------+      +--------------------------+
| registry.json    |      | tests/quality_gates/     |
| project-setup    |      | e2e smoke, UB_TOOLS_E2E  |
+------------------+      +--------------------------+
         ^                           ^
         | builds venvs, gates PRs   |
+--------+---------------------------+--------+
| .github/workflows/tests.yml                 |
|  vendored suites; diff-derived gate paths;  |
|  mutator budget (workers cap + timeout)     |
+---------------------------------------------+
```

## Open Questions

- The dryer boundary and exit codes are verified against the vendored code during apply, before archive.
- The zsh presence on the CI runner image is confirmed on the first workflow run. D9 holds the fallback.
- The first mutator CI run measures the real budget. D4 holds the tuning path.
