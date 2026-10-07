# Proposal

## Why

The `llm_ops/eval` project has a devcontainer and no code. DeepEval uses an OpenAI model as its judge by default. This repository runs the Apple on-device model through a local apfel server. The user wants DeepEval to use that server as its judge, with no cloud key.

A direct setup fails for three reasons. I measured each reason on 2026-10-07 with apfel 1.10.0 and DeepEval 4.2.8:

- From a devcontainer, apfel gives HTTP 403 to the Host header `host.docker.internal`.
- apfel ignores `$ref` and `$defs` in a JSON schema. A nested schema gives empty objects, and the DeepEval AnswerRelevancy metric fails.
- The DeepEval `LocalModel` class sends no schema to the server.

## What Changes

- Add a DeepEval judge model that calls the apfel server from a devcontainer.
- Add a script that asks apfel four questions. The script scores the answers with a DeepEval correctness metric. The judge is the same apfel server, and the run sends no telemetry.
- Add unit tests, an opt-in end-to-end test, and the quality gates. The gates are 100% branch coverage, complexity of 10 or less, and a mutation score of 95% or more.
- Add the dev dependencies, a Claude skill, the documentation, and two setup registry units.

This change does not add other metrics, other models, parallel runs, an MCP tool, or CI.

## Capabilities

### New Capabilities
- `llm-ops-eval/apfel-judge`: A DeepEval judge model that uses a local apfel server. Its output matches the schema that the metric asks for.
- `llm-ops-eval/eval-run`: A command that scores the apfel answers to fixed questions. It reports the result and sets an exit code.

### Modified Capabilities

None.

## Impact

- New code in `llm_ops/eval/`: two modules, their tests, and a `pyproject.toml` that holds the gate settings.
- Dependencies: `deepeval`, `openai`, and `python-dotenv`, each with an exact version. Dev tools: `pytest`, `pytest-cov`, `ruff`, `mutmut`, and the HTTP package that the tests import.
- The devcontainer installs the dev dependencies.
- The run must have the apfel server on the macOS host. One run makes 8 model calls and 1 call to list the models. Each call takes about 8 to 40 seconds.
- `tools/project_setup/registry.json` gets two units. `CLAUDE.md` names the project.
