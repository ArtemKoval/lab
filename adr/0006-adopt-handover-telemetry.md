# 0006 - Adopt per-task handover telemetry

- Status: accepted
- Date: 2026-10-29

## Context

The pipeline opens a handover issue after every merge, and the issue carries a summary and next steps but no run data. Claude Code transcripts and a session log hold the models, tokens, timings, tool calls, decisions, and costs of each task, and no tool extracts them. Runs now spend real money across several agents per task. The redaction need is absolute, because an issue is a public record and the logs hold secrets, paths, and identity fields.

## Decision

Every handover issue carries a redacted telemetry block that a stdlib CLI builds from two sources: the session transcripts and a new local hook log. The hook redacts at write time and always exits 0. The CLI redacts again before any output, omits raw text and identity fields by structure, and prints a redaction report. The pipeline skill states the mandate in Step 13 and names the shipped tooling in Step 14. The report marks estimates and gaps honestly: prices carry source dates, unknown prices render as unknown, and proxies without data render as not available. Rejected options: an advisory skill without a pipeline rule, because adoption would depend on the model noticing it. Cost display without a redaction contract, because one leak defeats the whole surface. A logging-only hook without the transcript merge, because the hook never sees tokens or models.

## Consequences

Every future handover issue makes the cost, the model mix, and the friction of the run visible, and the data survives compaction. The hook adds work to every tool call in every session of this repo, so its duration needs a measurement and a timeout. The transcript format is internal to Claude Code, so the parser stays tolerant and the fixtures follow real files. The price table needs a person to update it, and stale rates degrade the cost numbers instead of failing them.
