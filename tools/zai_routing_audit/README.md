# zai_routing_audit

A stdlib Python CLI that audits the z.ai GLM model routing behind Claude Code. It answers four questions with commands instead of one-off shell scripts:

1. Which model name does Claude Code send?
2. Which model name does the z.ai endpoint echo back?
3. Which model name does the usage report record?
4. What does the credit engine charge for each name?

The method comes from a manual investigation on 2026-10-15. See the `zai-routing-audit` skill for the results of that run.

## Install

A clean clone installs the unit through the `project-setup` skill. Manual install:

```bash
python3 -m venv tools/zai_routing_audit/.venv
tools/zai_routing_audit/.venv/bin/python -m pip install -r tools/zai_routing_audit/requirements-dev.txt
```

## Commands

Run from `tools/zai_routing_audit/`. Add `--json` for machine output. Exit code 0 means success; 2 means operational failure. The token never prints.

```bash
cd tools/zai_routing_audit
AUDIT=".venv/bin/python -m zai_routing_audit"

$AUDIT config
$AUDIT transcripts --directory ~/.claude/projects/-Users-art-Documents-git-lab
$AUDIT echo glm-5.3-flash glm-5.3
$AUDIT usage --start "2026-10-15 00:00:00" --end "2026-10-15 23:59:59"
$AUDIT throughput glm-5.3-flash glm-5.3
$AUDIT burn glm-5.3-flash glm-5.3 --spend-credits
```

`config` reads `~/.claude/settings.json` by default. `--settings PATH` points at another file. The network commands (`echo`, `usage`, `throughput`, `burn`) accept `--base-url URL` to override the endpoint.

`burn` without `--spend-credits` prints its plan and sends nothing. With the flag it sends one padded request per name, about 48k input tokens each, and reports the credit pool delta per name.

## Costs

| Command | Spends |
|---|---|
| config, transcripts | Nothing |
| usage | Console reads only |
| echo | About 35 tokens per name |
| throughput | About 1k output tokens per name |
| burn | Tens of credits per name |

## Console endpoints

`usage` and `burn` read undocumented console endpoints, reverse engineered on 2026-10-15:

- `GET <origin>/api/monitor/usage/model-usage?startTime=...&endTime=...` - per-model token rows. Local time, URL-encoded.
- `GET <origin>/api/monitor/usage/quota/limit` - credit pools.

The origin comes from the model API base URL. The tool accepts both known envelope shapes and exits 2 with a redacted body excerpt on any other shape. The endpoints can change without notice.

## Results from the 2026-10-15 run

- The endpoint echoes every requested name unchanged.
- The usage report merged a flash-only day under the `GLM-5.3` row.
- Identical 48,021-token burns cost 13 credits as flash and 17 as `glm-5.3`.
- Both names generated at the same speed.

## Tests and quality gates

```bash
tools/zai_routing_audit/.venv/bin/python -m pytest
tools/zai_routing_audit/.venv/bin/python -m pytest --cov zai_routing_audit --cov-branch --cov-fail-under=100 --cov-config .coveragerc
tools/zai_routing_audit/.venv/bin/ruff check tools/zai_routing_audit
```

Live checks need `ZAI_ROUTING_AUDIT_E2E=1` and `-m e2e`.

### Mutation run

Run mutmut on an out-of-tree copy, never inside the repository:

```bash
rm -rf /tmp/zai_mut && mkdir -p /tmp/zai_mut
rsync -a --exclude .venv --exclude __pycache__ tools/zai_routing_audit/ /tmp/zai_mut/zai_audit/
mkdir -p /tmp/zai_mut/zai_audit/tests
cp -r tests/zai_routing_audit/. /tmp/zai_mut/zai_audit/tests/
cd /tmp/zai_mut/zai_audit
/full/path/to/lab/tools/zai_routing_audit/.venv/bin/python -m mutmut run
/full/path/to/lab/tools/zai_routing_audit/.venv/bin/python -m mutmut results
```

The `[tool.mutmut]` section expects the mirrored layout above. The final run kills 1152 of 1197 mutants, a score of 96.2 percent. The 45 survivors sit in equivalence classes that behave identically by construction:

| Class | Where | Why the mutant behaves the same |
|---|---|---|
| argparse keyword forms | `build_parser` (23 mutants) | argparse derives `dest` from the option string and uses None as the default, so the removed `default=None` and `dest=` forms build the same parser |
| codec alias | `encode` and `decode` calls | `UTF-8` and `utf-8` name the same codec |
| method inference | `Request` calls | urllib infers POST from the data argument and GET otherwise |
| locale reads | `open()` calls | the runner locale is UTF-8, so the default and the alias read identically |
| redact normalization | `env.get` defaults | redact maps a missing and an empty token to the same output |
| falsy strict | `json.loads(strict=None)` | the decoder treats None as false, which is the same tolerant parse |
| no-op replace | `sanitize` or-form | replacing an absent or an empty token changes nothing |
| hidden microseconds | `day_bounds` | the timestamps print no microseconds |
| guarded isinstance | `parse_model_usage` | the data value is always a dict at that point |
| internal only | `_resolve` facts call | the facts dictionary only feeds the base URL there |

## Known limits

- The console counters lag real time by a short period. `burn` sleeps two seconds before each re-read.
- Transcript scanning reads the Claude Code JSONL record shapes of October 2026. A harness change can shift the field paths.
- The tool audits. It changes no setting.
