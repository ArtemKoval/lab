# Design: add-handover-telemetry

## Context

Claude Code writes one JSONL transcript per session under `~/.claude/projects/<slug>/`, with subagent transcripts under `<session-id>/subagents/`. The entries carry models, token usage, tool calls, timestamps, compaction markers, and a session cost summary. The format is internal and drifts between versions. The pipeline opens a handover issue after every merge, and the template carries no telemetry. The user chose both data sources: the transcripts and a new logging hook. The in-force ADRs bind the shape. ADR 0002 fixes the single Claude Code harness. ADR 0004 fixes the mechanical STE gate. ADR 0005 fixes the vendored quality gates for new Python. No ADR needs supersession.

## Goals / Non-Goals

**Goals:**

- One stdlib package that turns a session into a redacted telemetry report.
- A hook that records tool calls, boundaries, and permission events at write time.
- Cost, DORA proxies, decisions, machine specs, and friction signals in every report.
- No secret, key, password, identity field, or home path in any output.

**Non-Goals:**

- No raw prompt or response text in any output.
- No OpenTelemetry exporter, dashboard, or cross-task aggregation store.
- No rewrite of the transcript format, and no write access to transcripts.
- No price fetching from the network at run time.

## Decisions

**D1 - One package carries the hook and the CLI.** `tools/handover_telemetry/` holds `hook.py`, `cli.py`, and the shared modules `transcript.py`, `logparse.py`, `redact.py`, `machine.py`, `metrics.py`, `render.py`, and `pricing.json`. The hook is the writer of the log, and the CLI is the reader, so one module owns the log schema. Alternative rejected: two packages. Writer and reader would drift on the log format. A third module would carry the shared code, and the hook would need a second import path.

**D2 - The transcript is the primary record, and the hook log is the supplement.** The build pairs hook records with transcript tool calls on the session id and the tool use id. A hook duration replaces a derived duration for the same call. A missing log degrades to transcript-only numbers. Alternative rejected: hook-only data. The hook never sees tokens, models, or compaction, and it has no history before its first session.

**D3 - The parser stays shallow and tolerant.** It skips unknown entry types, treats missing fields as absent, and reads only stable shallow fields. It deduplicates usage on the message id and the request id, because one API turn writes several entries. It excludes entries with the synthetic error model from token and cost totals. It globs `subagents/` for sidechain files and reports them as separate agents. Alternative rejected: strict schema validation. The format changes between Claude Code versions, and a strict parser fails on every update.

**D4 - Redaction runs in three layers.** Layer one omits by structure: the outputs carry allowlisted fields only, no raw text, and no identity fields. Layer two scrubs every emitted string with the redaction patterns. The patterns cover token shapes, keys, JWTs, PEM blocks, and high-entropy strings. They also cover emails, IP addresses, credentials in URLs, home paths, usernames, and timezone names. The machine allowlist omits the hostname, and no hostname field exists in any output. Layer three adds a redaction report with counts per category. The hook uses the same module at write time, so the log holds no secrets either. Alternative rejected: one scrub at render time only. The log file would hold secrets before any render.

**D5 - The cost model uses a versioned price table with source dates.** `pricing.json` maps a model id to rates per million tokens for input, output, cache read, and the two cache write tiers. A missing rate falls back to the Anthropic multipliers of 0.1, 1.25, and 2.0 on the input rate. Thinking tokens sit inside output tokens, so the formula never adds them twice. A model with no entry renders as unknown, and the run total names the gap. A person updates the file when prices change. The apply run fills the table with the researched rates. The z.ai GLM rates carry their docs source and date. The Claude rates come from the claude-api reference at apply time. Alternatives rejected: network pricing at run time, because the default path stays offline, and no cost section, because the user asked for dollars.

**D6 - The DORA mapping is a fixed table with honest gaps.** Lead time maps to the span from the first prompt to the merge commit, found through local git. Change fail rate maps to the count of failed gates, failed tests, and fix commits. Recovery time maps to the span from the first red gate to the next green gate. Rework rate maps to the share of commits that follow the first review event, through gh when available. Deployment frequency has no per-task proxy and renders as not applicable. Any proxy without source data renders as not available.

**D7 - Decision points come from a designated tool list.** The list names `AskUserQuestion`, `ExitPlanMode`, `Agent`, `Skill`, `Workflow`, and `EnterPlanMode`. The report lists each call with the agent, the tool, and redacted truncated arguments. The module holds the list in one place for extension. Alternative rejected: heuristics over all tool calls. Every call would land in the list, and the signal would drown.

**D8 - Machine specs come from an allowlist with best-effort reads.** The fields are kernel, architecture, distribution, cpu model and count, memory, and disk size at the repo. The list adds the python and git versions, container detection, and the gpu name when a query tool answers. No other tool version joins the list. Each read degrades to an absent field. macOS hosts use their own read commands behind the same field names. The fingerprint adds the agent version, the entrypoint, and the session id.

**D9 - The hook is a shim plus a lean module.** The shim at `.claude/hooks/cc-logging.sh` resolves the repo root like the spec STE gate. It picks the shared venv interpreter with a system `python3` fallback, and pipes the event JSON to `handover_telemetry.hook`. The event names come from the pipeline event list, and the update-config skill re-validates the names at wiring time. The module selects a small field set, redacts strings, and appends one JSON line to `.cc_logging/<session-id>.jsonl` with an append-only write. It records its own duration, and it always exits 0. A missing interpreter or log directory exits 0 with no output. The settings entries carry a timeout.

**D10 - The CLI surface follows the house contract.** Subcommands `build` and `sessions`. Flags `--project-dir`, `--transcript`, `--session`, `--prices`, `--out`, `--json`, `--create`, and `--repo`. Exit 0 on success and 2 on operational failure. `--create` prepares the body and runs `gh issue create`. Tests fake the gh executable on `PATH`, and one live test sits behind the `HANDOVER_TELEMETRY_E2E=1` gate.

**D11 - Wiring and setup follow the house seams.** The hook groups land in `.claude/settings.json` through the update-config skill. The registry gains one unit for the hook wiring, and its doctor examines the shim, the settings groups, and the interpreter. `.gitignore` names `.cc_logging/`. CI adds the package to the 100 percent coverage floor and gains a lint step. The crapper, dryer, and mutator gates run on the package through the shared venv.

**D12 - The JSON output uses the OpenTelemetry GenAI field names.** Fields such as `gen_ai.request.model`, `gen_ai.response.model`, and `gen_ai.usage.input_tokens` keep the JSON joinable with standard observability tooling. The markdown report uses human labels.

## Wiring

The wiring uses a lightweight C4-inspired container view in ASCII. Containers are runnable units. Components live inside them.

```
 user / agent session (Claude Code)
   |  events: PreToolUse, PostToolUse, PermissionRequest,
   |          SessionStart, SessionEnd, Stop
   v
 [.claude/hooks/cc-logging.sh]  -->  [handover_telemetry.hook]  -->  (.cc_logging/<session>.jsonl)  redacted, uncommitted
                                          ^ shared: redact.py, log schema
 [Claude Code transcripts]                                    |
   ~/.claude/projects/<slug>/<session>.jsonl                  |
   ~/.claude/projects/<slug>/<session>/subagents/*.jsonl      |
   |                                                          |
   v                                                          |
 [handover_telemetry.cli build]  <--- merges both sources ----+
   |  reads: pricing.json, /proc + uname, git
   +--> handover-report markdown | --json | --create -> gh issue
```

## Risks / Trade-offs

- [The transcript format drifts between Claude Code versions] -> The parser skips unknown types, and the fixtures come from real files. One e2e gate runs against the live directory on demand.
- [Prices go stale] -> Each rate carries a source date, unknown models render as unknown, and a person updates the file.
- [The hook adds work to every tool call] -> The module stays stdlib and small. The apply run measured 62 to 79 ms per event on the build host, and the settings entries carry a 10 second timeout.
- [A redaction pattern misses a new secret shape] -> The omission layer bounds what reaches an output. The report counts every scrub, and tests plant known secret shapes.
- [Transcripts move between config roots] -> The discovery honors `CLAUDE_CONFIG_DIR` and both known roots.

## Migration Plan

No data migration exists. The hook activates on the next session start after the settings merge. Rollback removes the hook groups through the update-config skill. The CLI works without the hook log on every past transcript.

## Open Questions

- The gpu field needs a host with a query tool for its first real value. Absent stays a valid state.
- Workflow subagents sit one directory deeper than plain subagents. The glob covers both. The first real workflow run confirms the layout.
