# Proposal

## Why

On 2026-10-15 a manual investigation settled a routing question for the z.ai GLM Coding Plan: Claude Code requests `glm-5.3-flash`, but the z.ai usage panel reports the traffic under `GLM-5.3`. The investigation used one-off shell commands, and its results live only in one chat transcript. A repeatable tool preserves the method and reruns the audit whenever the routing question comes back.

## What Changes

- Add `tools/zai_routing_audit/`, a stdlib Python CLI package with these subcommands:
  - `config` - read back the Claude Code routing settings (base URL, model slots) and redact the auth token.
  - `transcripts` - scan Claude Code transcript files for the requested model and the echoed model, and sum token usage per model.
  - `echo` - send one bounded request per model name and compare the model each response echoes.
  - `usage` - read the console per-model usage rows and the credit pools.
  - `throughput` - time one bounded generation per model name and report tokens per second.
  - `burn` - measure the credit cost of one identical request per model name. Runs only with the explicit `--spend-credits` flag.
- Add hermetic unit tests under `tests/zai_routing_audit/`. Live network checks stay behind an env-var gate and an `e2e` marker.
- Add a thin FastMCP wrapper, `.mcp.json` registration, and the matching permission entries.
- Add a Claude skill, a tool README, a CLAUDE.md entry, and a setup registry unit for the Python dependencies.

## Capabilities

### New Capabilities

- `zai-routing-audit`: an audit that shows which GLM model name Claude Code sends, which model the z.ai endpoint echoes, which model the usage report records, and what the credit engine charges for each name.

### Modified Capabilities

- None.

## Impact

- New code: `tools/zai_routing_audit/` (stdlib only at run time), `tests/zai_routing_audit/`.
- New config: `.mcp.json`, permission entries in `.claude/settings.json`, one unit in `tools/project_setup/registry.json`, a `pytest.ini` at the repo root so a root pytest run stays hermetic and scoped.
- Edits: `CLAUDE.md` (projects list), tool README.
- Quota: `echo` and `throughput` spend a few hundred tokens per run. `burn` spends tens of credits and needs the explicit flag.
