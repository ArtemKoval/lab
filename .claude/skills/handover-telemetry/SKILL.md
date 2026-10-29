---
name: handover-telemetry
description: Build the redacted telemetry block for a handover issue from Claude Code session logs. Use after a merge when you open a handover issue, when the user asks for run statistics, costs, models, timings, or DORA proxies of a task, or when the feature-pipeline Step 13 rule tells you to add the telemetry block. Gives the commands, the exit codes, and the redaction rules.
---

# handover-telemetry

Build the telemetry block of a handover issue. The tool reads one
Claude Code session transcript plus the local cc-logging hook log, and
renders a redacted report as markdown or JSON. The spec at
`openspec/specs/handover-telemetry/` owns the behavior.

## When

- feature-pipeline Step 13 tells you to add the telemetry block to a
  handover issue. That case is mandatory.
- The user asks for the cost, the models, the timings, or the step
  funnel of a finished task.

## Commands

Run through the shared repository venv interpreter:

```bash
VENV=tools/zai_routing_audit/.venv/bin/python
PYTHONPATH=tools/handover_telemetry $VENV -m handover_telemetry build --out /tmp/handover-report.md
```

Variants:

```bash
# Machine output with OpenTelemetry GenAI field names
PYTHONPATH=tools/handover_telemetry $VENV -m handover_telemetry build --json

# A session other than the newest one
PYTHONPATH=tools/handover_telemetry $VENV -m handover_telemetry build --session <id> --out /tmp/r.md

# List the candidate transcripts of this project
PYTHONPATH=tools/handover_telemetry $VENV -m handover_telemetry sessions

# Open the GitHub issue directly (network; needs gh auth)
PYTHONPATH=tools/handover_telemetry $VENV -m handover_telemetry build --create
```

Exit 0 on success and 2 on operational failure. The default path makes
no network call. `--create` is the only network path.

## How to read the report

- Run: the session id, the agent version, the branch, and the host.
- Funnel: one row per tool call with agent, start, duration, and exit.
- Models and tokens: sums per served model, with the requested models
  and the cache hit rate.
- Cost: an estimate from the packaged price table with its source
  date. A model with no rate renders as unknown. Update
  `tools/handover_telemetry/handover_telemetry/pricing.json` when
  prices change.
- Pipeline proxies: lead time, fail signals, recovery, rework. A
  proxy without data renders as n/a. Deployment frequency has no
  per-task proxy.
- Decisions: the question, plan, agent, and workflow calls with their
  redacted arguments.
- Friction: api errors, failed calls, retries, compactions, and
  permission events.
- Machine: the allowlisted host fields. No hostname, no serials, no
  home paths.
- Redaction: counts per category. Read them before you paste anything.

## Redaction rules

The tool scrubs tokens, keys, credentials, emails, addresses, home
paths, and timezone names, and omits raw prompt and response text.
Read the Redaction section of the report before you paste it into an
issue. If a count looks wrong, examine the source field and drop the
block.

## Setup

A clean clone wires the hook through the `handover-telemetry-hook`
unit in `tools/project_setup/registry.json`. The doctor:

```bash
python3 tools/handover_telemetry_setup/handover_telemetry_setup.py --repo-root .
```

Exit 0 means the shim, the settings groups, and the interpreter are
ready. The hook log of a session sits at `.cc_logging/<session>.jsonl`
and stays out of version control.
