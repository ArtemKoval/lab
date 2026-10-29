# Proposal: add-handover-telemetry

## Why

Handover issues give a summary and next steps, but no cost, model, timing, or failure data. Claude Code writes these numbers to disk, and no tool extracts them. Runs now span several paid agents in one task. Their cost and model mix stay invisible.

## What Changes

- Add `handover-telemetry`, a stdlib CLI in `tools/handover_telemetry`.
- The CLI reads Claude Code transcripts and the cc-logging log.
- The CLI writes a redacted report as markdown or JSON.
- The report lists every tool call with its model, tokens, and duration.
- The report splits the numbers per agent: the primary agent and each subagent.
- The report counts each usage entry once and gives cost per model and per run.
- The cost model applies cache-tier price multipliers. A model with no known price gets an unknown mark.
- The report maps DORA metrics to per-task proxies where a proxy exists. The design records the mapping.
- The report lists decision points with the agent, the arguments, and the tools.
- The report gives the hardware and software specs of the host.
- The specs omit serial numbers, hardware addresses, the hostname, and home directory paths.
- The report gives cache hit rate, compaction pressure, permission friction, and error counts.
- It also gives correlation ids, a run fingerprint, git linkage, and the cost split per agent.
- The report omits raw prompt and response text, identity fields, and transcript attachments.
- The report omits activity-only metrics.
- The report redacts secrets, keys, passwords, location data, and PII before any output.
- Markdown is the default output. A flag opens the GitHub issue through gh.
- The design records the cost formula and the OpenTelemetry GenAI field names. It also records the exclusion of synthetic model errors from cost totals.
- Add a session hook that records tool calls, session boundaries, and permission events.
- The hook registers the PreToolUse, PostToolUse, PermissionRequest, SessionStart, SessionEnd, and Stop events.
- The hook appends to one local uncommitted log.
- The hook redacts secrets at write time and always exits 0.
- The hook stays lean. The settings entry sets a timeout.
- Wire the hook in `.claude/settings.json`.
- Add a Step 13 rule to the `feature-pipeline` skill. The rule tells the agent to add the telemetry block to every handover issue.
- Rewrite the `Log` sub-step in Step 14 of the `feature-pipeline` skill. The sub-step names the shipped tooling. The sub-step drops the target-design language.
- Add a Telemetry section to `.github/ISSUE_TEMPLATE/handover.md`. The section holds the tool output blocks. The template keeps the Task, Logs, Metrics, Observations, and Follow-ups sections.
- Add tests under `tests/handover_telemetry/`.

## Capabilities

### New Capabilities

- `handover-telemetry`: A stdlib CLI and a session hook in one package. The CLI reads transcripts and the hook log, and writes a redacted report. The hook records tool calls, boundaries, and permission events.

### Modified Capabilities

- `intent-driven-harness`: The harness wires the hook in project settings. The pipeline skill tells the agent to add the telemetry block in Step 13. Step 14 names the shipped tooling. The template gains the Telemetry section. The coverage floor in CI extends to the new package.

## Impact

- Specs: new spec at `openspec/specs/handover-telemetry/spec.md` for the reporter and the hook. Delta for `openspec/specs/intent-driven-harness/spec.md` for the wiring, the Step 13 rule, the Step 14 rewrite, the template section, and the CI floor.
- Code: `tools/handover_telemetry/` is one package with `cli.py` and `hook.py`, plus the parser, redaction, machine, cost, and render modules. A hook shim at `.claude/hooks/cc-logging.sh` calls the module. A new skill sits at `.claude/skills/handover-telemetry/SKILL.md`.
- Edits: `.claude/settings.json` through the update-config skill, `.github/ISSUE_TEMPLATE/handover.md`, the `feature-pipeline` skill, `CLAUDE.md`, and `.gitignore` for the `.cc_logging/` log directory.
- Setup: one new project-setup unit for the hook wiring. Its doctor examines the shim, the settings entry, and the interpreter. A clean clone needs no dependency unit. The package uses the Python standard library only.
- Data: a versioned pricing table ships in the package. Each rate carries a source date. A person updates the file when prices change.
- Tests: `tests/handover_telemetry/` in the shared repo venv. Tests fake the gh call. A live gh test is opt-in through a gate variable.
- Systems: transcript files and system files are read-only input. The default path makes no network call. The flag path runs gh.
- Risks: the transcript format is internal to Claude Code. The parser skips unknown entry types and treats fields as optional. A Claude Code update can move or reshape the files.
