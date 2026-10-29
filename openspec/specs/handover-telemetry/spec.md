# handover-telemetry Specification

## Purpose
TBD - created by archiving change add-handover-telemetry. Update Purpose after archive.

## Requirements

### Requirement: The CLI names the run sources
The CLI SHALL discover the newest session transcript of the current project under the Claude Code projects root. The CLI SHALL accept `--project-dir`, `--transcript`, and `--session` to name other sources.

#### Scenario: The default source is the newest transcript
- **WHEN** the build command runs with no session flags in a project whose directory holds transcripts
- **THEN** the command uses the newest transcript and exits 0

### Requirement: The parser stays tolerant and counts once
The parser SHALL skip unknown entry types and SHALL treat missing fields as absent. The parser SHALL count each API usage entry once. The parser SHALL exclude entries that carry the synthetic error marker from token and cost totals. The parser SHALL include the subagent transcript files of the session.

#### Scenario: An unknown entry type does not stop the build
- **WHEN** a transcript carries an entry type the parser does not know
- **THEN** the parser skips the entry, and the build exits 0

#### Scenario: One API turn counts once
- **WHEN** one API turn appears as several entries with one message id
- **THEN** the report counts its usage once

#### Scenario: A synthetic error stays out of the totals
- **WHEN** an assistant entry carries the synthetic error marker with zeroed usage
- **THEN** the entry stays out of the token sums, the cost totals, and the model list

#### Scenario: Subagent runs split per agent
- **WHEN** the session holds subagent transcript files
- **THEN** the report carries their numbers as separate agents next to the primary agent

### Requirement: The CLI merges the hook log
The CLI SHALL read the cc-logging log of the session when the log exists, and SHALL pair its records with the transcript tool calls. A hook duration SHALL replace a derived duration for the same call. A missing log SHALL degrade to transcript-only numbers.

#### Scenario: A hook duration replaces the derived duration
- **WHEN** the hook log carries a duration for a call that also appears in the transcript
- **THEN** the report shows the hook duration for that call

#### Scenario: A missing log degrades cleanly
- **WHEN** the session has no hook log
- **THEN** the report uses transcript durations only, and the build exits 0

### Requirement: The report carries the funnel, the tokens, the models, and the cost
For every tool call the report SHALL list the tool name, the agent, the start time, and the duration. The report SHALL give token sums per model with the cache splits, and the served and the requested model names. The report SHALL compute cost from a versioned price table with cache-tier multipliers, and SHALL mark a model with no known price as unknown. The report SHALL give the cache hit rate and the cost split per agent.

#### Scenario: Both model names appear
- **WHEN** a turn records a requested model and a different served model
- **THEN** the report shows both names for that turn

#### Scenario: An unknown price renders as unknown
- **WHEN** the served model has no rate in the price table
- **THEN** the cost for that model renders as unknown, and the run total names the gap

#### Scenario: The cache split appears
- **WHEN** a turn records cache read and cache creation tokens
- **THEN** the report shows the three token kinds and the cache hit rate

### Requirement: The report carries the per-task pipeline proxies
The report SHALL give the lead time from the first prompt to the merge commit. The report SHALL give the rework rate from the review rounds. The report SHALL give stability signals from failed gates and fixes. The report SHALL render a proxy with no source data as not available. The DORA metrics with no per-task proxy SHALL render as not applicable.

#### Scenario: The lead time comes from git
- **WHEN** the repository carries the merge commit of the task branch
- **THEN** the report gives the span from the first prompt to the merge time

#### Scenario: A proxy without data renders as not available
- **WHEN** the session has no merge commit in the repository
- **THEN** the lead time renders as not available, and the build exits 0

### Requirement: The report carries the decision points
The report SHALL list the calls on a designated decision-tool list with the agent, the tool, and redacted truncated arguments. The design SHALL name the decision-tool list.

#### Scenario: A question call lands in the decision list
- **WHEN** the transcript carries a question tool call with arguments
- **THEN** the report lists the call with the agent, the tool, and the redacted arguments

### Requirement: The report carries the machine specs and the run fingerprint
The report SHALL collect an allowlist of host fields: kernel, distribution, architecture, cpu model, cpu count, memory, disk, runtime versions, and container detection. The specs SHALL omit serial numbers, hardware addresses, the hostname, and home directory paths. The report SHALL give the agent version, the entrypoint, and the session id as the run fingerprint.

#### Scenario: No identity field survives
- **WHEN** the report renders the machine specs of a host with a hostname and a home directory
- **THEN** the report carries no hostname and no home directory path

### Requirement: The CLI redacts every output
The CLI SHALL scrub every output string with the redaction patterns before it writes the output. The CLI SHALL give a redaction report with counts per category. The report SHALL omit raw prompt and response text, identity fields, and transcript attachments. The report SHALL omit activity-only metrics.

#### Scenario: A planted secret does not survive
- **WHEN** a transcript field carries a token that matches a redaction pattern
- **THEN** the output carries a redaction mark instead of the token, and the redaction report counts it

#### Scenario: Raw text stays out
- **WHEN** the transcript carries prompt text and response text
- **THEN** the report carries no raw prompt text and no raw response text

### Requirement: The CLI lists sessions and opens issues only with a flag
The CLI SHALL give a `sessions` subcommand that lists the sessions of a project directory with start time, end time, and model names. The CLI SHALL open the GitHub issue through gh only with `--create`. Without the flag the CLI SHALL NOT run a network command. The CLI SHALL exit 0 on success and 2 on operational failure.

#### Scenario: The session list renders
- **WHEN** the sessions command runs against a project directory with transcripts
- **THEN** the command prints one line per session with the start time and the model names

#### Scenario: No flag means no gh call
- **WHEN** the build command runs without `--create`
- **THEN** the command runs no gh process

#### Scenario: A failure exits 2
- **WHEN** the build command runs against a missing transcript path
- **THEN** the command exits 2 and names the problem

### Requirement: The hook records the session
The hook SHALL append one JSON line per event to the log file of the session under the `.cc_logging/` directory. The hook SHALL register the PreToolUse, PostToolUse, PermissionRequest, SessionStart, SessionEnd, and Stop events. The hook SHALL redact secrets at write time, SHALL record its own duration, and SHALL always exit 0.

#### Scenario: An event appends one line
- **WHEN** the hook receives a tool event with a session id
- **THEN** the log file of the session gains one JSON line with the event name and the time

#### Scenario: A secret in the payload stays out
- **WHEN** an event payload carries a string that matches a redaction pattern
- **THEN** the log line carries a redaction mark instead of the string

#### Scenario: A hook failure does not stop the session
- **WHEN** the hook raises an error on an event
- **THEN** the hook exits 0, and the session continues

#### Scenario: A missing interpreter degrades
- **WHEN** the hook shim runs with no python interpreter
- **THEN** the shim exits 0 with no output
