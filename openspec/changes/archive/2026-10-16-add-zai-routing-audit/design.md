# Design

## Context

The audit reproduces a 2026-10-15 investigation. See proposal.md for the motivation. Measured facts that shape this design:

- The z.ai console endpoints `api.z.ai/api/monitor/usage/model-usage` and `api.z.ai/api/monitor/usage/quota/limit` are undocumented. Working clients parse two envelope variants (`data.limits` and top-level `limits`).
- Some `/api/anthropic/v1/messages` responses carry raw control characters inside strings. A strict JSON parser fails on them.
- The coding plan key sits in `~/.claude/settings.json` under `env.ANTHROPIC_AUTH_TOKEN`. The same key works on the console endpoints of the same host.
- The repo has no root pytest config and no CI. Python units carry their own venv inside the project directory (the `fde-python-dev` registry unit is the pattern).

## Goals / Non-Goals

**Goals:**

- Reproduce every audit step as one CLI command with machine output.
- Keep the run-time core on the standard library only.
- Hermetic tests by default; live checks behind a gate.
- Redact the token at one choke point.
- Meet the house gates: 100 percent branch coverage on the new package, cyclomatic complexity of 10 or less per function, mutation score of 95 percent or higher.

**Non-Goals:**

- No fix or rewrite of the z.ai panel, no wrapper app, no proxy.
- No keyring integration; the tool reads the key from settings or an env var.
- No scheduled or automatic runs.

## Decisions

1. **Stdlib-only core.** `urllib.request` instead of `httpx` or `requests`. The tool must run on a bare interpreter during an incident. Alternative rejected: `httpx` is already a devcontainer dependency of `llm_ops/eval`, but that install path does not exist on the host.
2. **Injected transport and clock.** The core takes a transport object with `post_json` and `get_json`, and a monotonic clock callable. Tests pass fakes; live runs pass real implementations. No network mocks, no patching.
3. **Tolerant JSON parse.** Parse with `json.loads(text)`. On `ValueError`, parse again with `json.loads(text, strict=False)`. This is the measured behavior of the real endpoint.
4. **Package layout and venv.** `tools/zai_routing_audit/zai_routing_audit/` holds `core.py`, `cli.py`, `mcp_server.py`. The venv lives in `tools/zai_routing_audit/.venv` and mirrors the `fde-python-dev` registry pattern. The CLI runs as `cd tools/zai_routing_audit && .venv/bin/python -m zai_routing_audit`.
5. **Tests at the repo root.** `tests/zai_routing_audit/` mirrors the source area. A root `pytest.ini` sets `testpaths = tests` so a root run stays scoped and hermetic. Live tests carry `@pytest.mark.e2e` and check `ZAI_ROUTING_AUDIT_E2E`.
6. **Redaction at one point.** A single `redact()` helper returns the first four characters plus an ellipsis. Every output path, text and JSON, passes through it. Tests assert the full token never appears.
7. **Burn behind a flag.** Without `--spend-credits` the command prints its plan and exits 0. The gate is a plain argument check, so the transport never sees a burn request by default.
8. **Schema drift exits 2 with an excerpt.** When a console response matches no known shape, the command prints a short body excerpt (token redacted) and exits 2. Silent guesses are worse than a clean failure.
9. **Gates in the tool venv.** `pytest-cov --cov-branch --fail-under=100` over the package, `ruff check` with `C901` at max-complexity 10, `mutmut` against an out-of-tree copy of the package per the pipeline rule. `mcp_server.py` gets an import test only, because FastMCP adds the `mcp` dependency at run time for the wrapper alone.
10. **Thin MCP wrapper.** `mcp_server.py` maps each subcommand to one tool function and holds no logic. `.mcp.json` launches it through the tool venv interpreter; `.claude/settings.json` gains the server allow entry.

## Risks / Trade-offs

- [Undocumented endpoints change shape] → envelope fallbacks plus a clean exit 2 with a redacted excerpt; README marks the endpoints as reverse-engineered on 2026-10-15.
- [Token leak through logs or JSON] → single `redact()` choke point with a test that scans every command output.
- [Surprise quota spend] → bounded `max_tokens` defaults, documented costs per command, `burn` gated by the explicit flag.
- [Mutation run cost] → mutate an out-of-tree copy of one small package only; exclude the MCP wrapper from mutation with a per-file reason.
- [Console counters lag real time] → the burn command re-reads pools twice with a short sleep and reports raw deltas; the README warns about ingestion delay.

## Migration Plan

New directory plus config lines. Rollback removes the directory and reverts the four config files. No data migration.

## Open Questions

None.
