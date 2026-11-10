# session-statusline Specification

## Purpose


The session status line renders one console line for the current
Claude Code session: the model, the thinking effort, the z.ai limit
percentages, the session cache rate, the token totals in millions,
and the time in UTC. The payload is the first source, the transcript
backs the totals, and the console backs absent limits, so the line
survives every data fault.

## Requirements


### Requirement: The status line renders the session summary
The tool SHALL read one JSON payload on standard input and print one
summary line. The line SHALL carry the model, the thinking effort, the
5-hour limit percentage, the weekly limit percentage, the session
cache rate, the input token total in millions, the output token
total in millions, and the time in UTC in `HH:MM` form. The payload
fields are the first source for every field the payload carries.

#### Scenario: A complete payload renders every field
- **GIVEN** the payload carries `model.display_name` `GLM-5.3-Flash`,
  `effort.level` `high`, `rate_limits.five_hour.used_percentage` `9`,
  `rate_limits.seven_day.used_percentage` `83`,
  `prompt_cache.hit_ratio` `0.98`, and transcript usage that sums to
  606225 input and 205336 output tokens
- **WHEN** the tool renders the line
- **THEN** the line carries `GLM-5.3-Flash`, `effort high`,
  `5h 9%`, `wk 83%`, `cache 98%`, `in 0.61M`, `out 0.21M`, and a
  `HH:MM UTC` time

#### Scenario: An absent cache object falls back to the transcript
- **GIVEN** the payload carries no `prompt_cache`, and the transcript
  usage sums carry cache reads over the input side
- **WHEN** the tool renders the line
- **THEN** the cache field carries the transcript-derived rate, and a
  transcript with no usage rows reads `cache n/a`

#### Scenario: An absent effort renders n/a
- **GIVEN** the payload carries no `effort.level`
- **WHEN** the tool renders the line
- **THEN** the effort field reads `n/a`

### Requirement: The transcript backs the session token totals
The tool SHALL sum the per-message usage from the session transcript
at `transcript_path` for the input and output token totals, and SHALL
cache the running sum per session so one refresh never re-reads the
whole file. The tool SHALL key the running cache on `session_id`. A
payload with a new `session_id` SHALL reset the sums. A cached offset
past the transcript size SHALL trigger a full re-read. The tool SHALL
skip a transcript line that does not parse.

#### Scenario: The totals survive a refresh
- **GIVEN** the transcript holds 606225 input and 205336 output
  tokens, and a prior render wrote the running cache after 500000
  input tokens
- **WHEN** the tool renders the line twice
- **THEN** both lines carry `in 0.61M` and `out 0.21M`, and the
  second render reads no transcript bytes before the cached offset

#### Scenario: A new session resets the totals
- **GIVEN** the running cache holds the sums of the prior session, and
  the payload carries a new `session_id`
- **WHEN** the tool renders the line
- **THEN** the totals come from the new transcript only

#### Scenario: A stale offset triggers a full re-read
- **GIVEN** the running cache holds an offset larger than the
  transcript size
- **WHEN** the tool renders the line
- **THEN** the totals come from a full re-read of the file

#### Scenario: A partial line is skipped
- **GIVEN** the transcript carries one line that parses as no JSON
  object between two valid usage rows
- **WHEN** the tool renders the line
- **THEN** the totals carry the two valid rows

#### Scenario: A missing transcript renders n/a totals
- **GIVEN** `transcript_path` names no existing file
- **WHEN** the tool renders the line
- **THEN** the token fields read `n/a`

### Requirement: The console backs the limit percentages
When a window percentage is absent from the payload, the tool SHALL
read that percentage from the two credit pools through the
`usage` command of `zai_routing_audit`. The tool SHALL read the
`CREDIT_LIMIT` rows only. The tool SHALL map the first pool to the
5-hour window and the second pool to the weekly window.

#### Scenario: The payload rate limits win
- **GIVEN** the payload carries `rate_limits.five_hour.used_percentage`
  and `rate_limits.seven_day.used_percentage`
- **WHEN** the tool renders the line
- **THEN** the line carries those two percentages and the tool makes
  no console call

#### Scenario: One absent window reads the console
- **GIVEN** the payload carries `rate_limits.five_hour.used_percentage`
  and no `rate_limits.seven_day`
- **WHEN** the tool renders the line
- **THEN** the line carries the payload percentage for `5h` and a
  console percentage for `wk`

### Requirement: The pool math renders one percentage per pool
The tool SHALL compute one percentage per pool as 100 times consumed
divided by the sum of consumed and remaining. A zero total or a
missing value SHALL render that percentage as `n/a`. A pool count that
is not two SHALL render both percentages as `n/a`.

#### Scenario: A zero-total pool renders n/a
- **GIVEN** the payload carries no window percentages, and the console
  returns two pools, the first with `consumed` 0 and `remaining` 0,
  and the second with non-zero values
- **WHEN** the tool renders the line
- **THEN** the `5h` field reads `n/a` and the `wk` field carries the
  computed percentage

#### Scenario: A pool count that is not two renders n/a
- **GIVEN** the payload carries no window percentages, and the console
  returns three pool rows
- **WHEN** the tool renders the line
- **THEN** both percentage fields read `n/a`

### Requirement: The console read is cached and fails stale
The tool SHALL cache each console percentage for 300 seconds. The tool
SHALL serve the stale cache when a console read fails. The tool SHALL
render `n/a` for a window with no cache and no successful read.

#### Scenario: A fresh cache makes no console call
- **GIVEN** the console cache is younger than 300 seconds, and the
  payload carries no window percentages
- **WHEN** the tool renders the line
- **THEN** the line carries the cached percentages, and the console
  command runs no times

#### Scenario: A failed console read serves the stale cache
- **GIVEN** the payload carries no window percentages, the console
  cache is older than 300 seconds, and the console command fails
- **WHEN** the tool renders the line
- **THEN** the line carries the cached percentages

### Requirement: The tool fails open
The tool SHALL print a line and exit 0 on every data fault, including
an unparsable payload and a missing transcript. The tool SHALL exit 2
with one next action only when the invocation itself is wrong.

#### Scenario: A broken payload renders a degraded line
- **GIVEN** standard input carries text that parses as no JSON object
- **WHEN** the tool runs
- **THEN** the tool prints one line where every field reads `n/a`
  with one fault marker, and exits 0

#### Scenario: A wrong invocation exits 2
- **GIVEN** the command line carries an unknown argument
- **WHEN** the tool runs
- **THEN** the tool exits 2, and the message names one next action
