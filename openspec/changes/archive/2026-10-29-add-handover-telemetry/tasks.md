# Tasks: add-handover-telemetry

## 1. Package core

- [x] 1.1 Create `tools/handover_telemetry/` with the package layout of design D1 and the house pyproject, ruff config, and README stub.
- [x] 1.2 Write `redact.py`: the pattern scrub with per-category counts, the omission helpers, and the hostname hash. Plant every secret shape in unit tests.
- [x] 1.3 Write `pricing.json` with source dates for the GLM and Claude rates from the research.
- [x] 1.4 Write the price loader with the multiplier fallback and the unknown mark.

## 2. Transcript and log parsing

- [x] 2.1 Write `transcript.py`: the tolerant entry reader with usage dedup and the synthetic-error exclusion.
- [x] 2.2 Write the sidechain glob and the source discovery with `CLAUDE_CONFIG_DIR` support.
- [x] 2.3 Write `logparse.py`: the hook log reader and the pairing with transcript tool calls on session id and tool use id.
- [x] 2.4 Build committed fixtures that mirror the real transcript shapes from the research, with planted secrets for the redaction tests.

## 3. Metrics and rendering

- [x] 3.1 Write `metrics.py`: funnel extraction, token sums with cache splits, cost math, DORA proxies, decision extraction, friction signals, and the run fingerprint.
- [x] 3.2 Write `machine.py`: the allowlisted host reads with best-effort degradation on Linux and macOS.
- [x] 3.3 Write `render.py`: the markdown sections and the GenAI-named JSON output.

## 4. CLI surface

- [x] 4.1 Write `cli.py`: the `build` and `sessions` subcommands, the flags of design D10, and the exit 0 and 2 contract.
- [x] 4.2 Write the `--create` path with the fake gh executable for tests and the e2e gate behind `HANDOVER_TELEMETRY_E2E=1`.

## 5. Hook

- [x] 5.1 Write `hook.py`: the event field selection, write-time redaction, append-only JSONL output, self timing, and the always exit 0 contract.
- [x] 5.2 Write `.claude/hooks/cc-logging.sh`: the root resolution, the interpreter pick with the `python3` fallback, and the fail-open path.

## 6. Wiring and setup

- [x] 6.1 Wire the six hook groups in `.claude/settings.json` through the update-config skill, and add `.cc_logging/` to `.gitignore`.
- [x] 6.2 Write the setup doctor `tools/handover_telemetry_setup/` and register the hook-wiring unit in `tools/project_setup/registry.json`.
- [x] 6.3 Extend the CI workflow with the coverage floor for the package and the lint step, and name the e2e variable in `pytest.ini`.

## 7. Tests and gates

- [x] 7.1 Write `tests/handover_telemetry/` with one test per spec scenario and the hook subprocess test for the shim.
- [x] 7.2 Run the full hermetic suite with the branch coverage floor at 100 percent for the package.
- [x] 7.3 Run the crapper, dryer, and mutator gates through the shared venv.
- [x] 7.4 Run the mutation gate on an out-of-tree copy of the package, and prove every survivor equivalent.
- [x] 7.5 Run the hook against a live event, measure its duration, and set the settings timeout from the measurement.
- [x] 7.6 Run `openspec validate add-handover-telemetry --type change --strict` before archive.

## 8. Surfaces and docs

- [x] 8.1 Write `.claude/skills/handover-telemetry/SKILL.md` with the commands and the reading guide.
- [x] 8.2 Finish the README of the package, and add the Projects entries to CLAUDE.md.
- [x] 8.3 Add the Step 13 rule and the Step 14 rewrite to the `feature-pipeline` skill.
- [x] 8.4 Add the Telemetry section to `.github/ISSUE_TEMPLATE/handover.md`.
