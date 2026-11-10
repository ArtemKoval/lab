# Design: add-session-statusline

## Plan review

The clarifying round asked two questions, and the user answered both:
the limit percentages read the z.ai console when the payload lacks
them, and the wiring lands in the project settings. The review
consulted the prior lessons. A status line command runs frequently,
so it stays stdlib-only, fail-open, and cached. Absolute paths keep
the command working from any working directory. The status line docs
for 2.1.322 name the payload fields this design reads:
`model.display_name`, `effort.level`, `rate_limits`,
`prompt_cache.hit_ratio`, `transcript_path`, and `session_id`. The
docs also name `context_window.current_usage`. It holds the last-call
usage. The design does not read it.

ASIT: `Unification` and `Multiplication`. The tool renders from the
payload the harness already produces, reads limits through the
`zai_routing_audit` console command that exists, and computes the
session token totals with the transcript-sum pattern the
`handover_telemetry` tool established. No new dependency, service, or
protocol enters. One new component enters: the status line tool
itself, because no existing tool renders a line from the status line
payload.

Assumptions recorded:
- The two credit pools report in console display order, so the first
  pool maps to the shorter window. The panel is the only source for
  the window mapping, and the operator reads both percentages anyway.
- Each percentage is consumed divided by the sum of consumed and
  remaining. A zero total or a missing value renders that percentage
  as n/a. A pool count that is not two renders both percentages as
  n/a. The tool reads the `CREDIT_LIMIT` rows only.
- `context_window.current_usage` holds the last-call usage, so the
  session totals come from the transcript sum, matching the numbers
  that `handover_telemetry` reports for this session.

## The render pipeline

```
stdin payload (JSON)
   |
   +-- model.display_name ---------> model
   +-- effort.level ----------------> effort (n/a when absent)
   +-- rate_limits.*.used_percentage > 5h / wk percentages,
   |        per window, payload first
   |        (absent) ---> console read, 300 s cache,
   |                      stale cache wins, else n/a
   +-- prompt_cache.hit_ratio ------> cache rate (percent)
   |        (absent) sums -> cache rate from transcript usage
   +-- transcript_path ------------> transcript sums for in/out totals
   +-- clock ----------------------> HH:MM UTC
```

The tool prints one line and exits 0 on every data fault. The
invocation faults (a wrong argument) exit 2 with one next action. The
settings block carries `refreshInterval: 15`, so the line tracks the
clock and the pools every 15 seconds, and the console cache holds the
network to one console invocation per 300 seconds at most.

The console call carries a 10 second timeout, so one slow call cannot
outlive the 15 second refresh. The tool writes each cache file to a
temporary file and renames it into place. The tool treats a corrupted
or unreadable cache file as no cache. The console cache and the
running-sum cache live under `~/.cache/session_statusline/` by
default as `console.json` and `sums.json`, and the injected arguments
override the paths. The running cache keys on `session_id` and holds
one record with the byte offset, the input sum, the output sum, the
cache-read sum, and the update time. A payload with a new `session_id`
resets the sums and drops the prior record. A cached offset past the
transcript size triggers a full re-read.

The console fallback shells one command:
`tools/zai_routing_audit/.venv/bin/python -m zai_routing_audit usage`,
with the repository root as the working directory and the day-default
window. The fallback parses the `pools` array of the JSON output, and
each pool row carries `type`, `consumed`, and `remaining`.

The transcript sums follow the handover-telemetry rule. Each assistant
turn with a usage object adds `usage.input_tokens` to the input total,
`usage.output_tokens` to the output total, and
`usage.cache_read_input_tokens` to the cache-read total. The cache
rate divides the cache-read total by the input side, the sum of the
input, cache-read, and cache-creation totals.

## Edge cases

- The effort field reads n/a when the payload carries no
  `effort.level`.
- `prompt_cache` absent: the cache rate computes from the transcript
  usage sums with the handover-telemetry definition, cache reads over
  the total input side. No usage renders n/a.
- The tool skips a transcript line that does not parse. A missing or
  unreadable transcript file renders n/a totals, and the line still
  renders. A transcript with no usage rows renders
  `in 0.00M out 0.00M` and a `cache n/a` field.
- The console cache fresh (under 300 seconds): no network call.
- The console call fails with no cache: `5h n/a wk n/a`.
- The payload JSON broken: a degraded line names the fault, exit 0.
- A narrow terminal: the line stays under 100 characters.
- The doctor writes the absolute tool path into the `statusLine`
  command of its checkout. A doctor run on another checkout repairs
  the path.

Formats: the tool rounds each percentage to the nearest whole
percent. The tool renders each token total as millions with two
decimals. The tool truncates the model field to 24 characters. The
time is the render time, and the 15 second interval bounds the drift.

The settings block pins one command template:
`<repo>/tools/zai_routing_audit/.venv/bin/python
<repo>/tools/session_statusline/session_statusline.py`, with the
operator checkout path in place of `<repo>`. The doctor writes and
repairs that string.

## Verification

`tests/session_statusline/` gains unit and contract tests: the render
with a complete payload, each fallback, each n/a case, the cache
behavior with an injected clock, an injected transport for the console
call, and the fail-open cases. Coverage holds 100 percent line and
branch on the module, and the mutation gate runs over it. The smoke
runs the tool with `--json` against this session's real payload and
transcript. The Gate 0 lint, the Gate 1 manifest proof, and the Gate 3
suites pass on the change. The strict validate and the STE gate pass
on the artifacts.
