---
name: zai-routing-audit
description: Audit the z.ai GLM model routing behind Claude Code. Use when the z.ai panel shows a different model than the config requests, when quota numbers look wrong, or when a GLM model name behaves oddly. Gives the commands, the exit codes, the costs, and the console endpoints.
---

# zai-routing-audit

Run the audit commands from `tools/zai_routing_audit/` with the tool venv:

```bash
cd tools/zai_routing_audit
.venv/bin/python -m zai_routing_audit --help
```

The global `--json` flag sits before the subcommand. The tool reads the token and the base URL from `~/.claude/settings.json` by default. It never prints the token. Exit code 0 means success; exit code 2 means an operational failure.

## Commands

| Command | What it shows | Network cost |
|---|---|---|
| `config` | Base URL, model slots, redacted token | None |
| `transcripts --directory DIR` | Requested and echoed models, usage sums | None |
| `echo NAME...` | The model name each response echoes | About 35 tokens per name |
| `usage` | Per-model usage rows and credit pools | Console reads only |
| `throughput NAME...` | Tokens per second per name | About 1k output tokens per name |
| `burn NAME...` | Credit pool delta per name | About 48k input tokens per name |

`burn` sends nothing without `--spend-credits`. With the flag it spends tens of credits. Use it only when the user agrees.

## Typical session

1. Run `config`. Confirm the base URL and the model slots.
2. Run `transcripts --directory ~/.claude/projects/-Users-art-Documents-git-lab`. Compare the requested and the echoed names.
3. Run `echo glm-5.3-flash glm-5.3 --json`. A mismatch exits 2.
4. Run `usage --json`. The rows name the models the report records. The pools show consumed and remaining credits.
5. Run `throughput` and `burn` only when the row question needs weight or price evidence.

Note: in step 3 and 4 the `--json` flag goes before the subcommand, for example `.venv/bin/python -m zai_routing_audit --json echo glm-5.3-flash glm-5.3`.

## Console endpoints

The `usage` and `burn` commands read undocumented console endpoints. They come from reverse engineering on 2026-10-15:

- `GET /api/monitor/usage/model-usage?startTime=...&endTime=...`
- `GET /api/monitor/usage/quota/limit`

The tool accepts both known envelope shapes and exits 2 with a redacted body excerpt on any other shape. Treat schema errors as a sign that z.ai changed the panel API.

## Known facts from 2026-10-15

- The endpoint echoes every requested name unchanged. It does not rewrite `glm-5.3-flash`.
- The usage report merged a flash-only day under the `GLM-5.3` row.
- The credit engine charged identical 48,021-token burns as 13 credits (flash) and 17 credits (`glm-5.3`).
- Both names generated at the same speed, 57.7 against 54.8 tokens per second.

## Tests and gates

The test suite runs from the repository root:

```bash
tools/zai_routing_audit/.venv/bin/python -m pytest
```

The suite is hermetic. Live checks need `ZAI_ROUTING_AUDIT_E2E=1` and `-m e2e`.
