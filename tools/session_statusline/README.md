# session_statusline

Renders the Claude Code status line for the current session: the
model, the thinking effort, the 5-hour and weekly limit percentages,
the session cache rate, the input and output token totals in
millions, and the time in UTC.

Claude Code runs the command from the `statusLine` block in
`.claude/settings.json` and renders its stdout at the bottom of the
console. The tool reads one JSON payload on stdin and prints one
line. The payload is the first source for every field. The session
transcript backs the token totals and the cache rate behind an
incremental per-session cache. The `usage` command of
`tools/zai_routing_audit` backs limit percentages that the payload
does not carry, behind a 300 second cache with a 10 second timeout.

The line fails open: every data fault renders n/a fields and exits 0,
so a broken transcript or a dead console never blanks the line. A
wrong invocation exits 2. The line can blank while the shared venv
interpreter itself is missing or rebuilding; the doctor catches that
state at install time.

## Commands

```bash
# Render one line from a payload file (what Claude Code does on stdin)
cat payload.json | tools/zai_routing_audit/.venv/bin/python \
  tools/session_statusline/session_statusline.py

# Machine-readable fields
cat payload.json | tools/zai_routing_audit/.venv/bin/python \
  tools/session_statusline/session_statusline.py --json

# Examine or repair the wiring for this checkout
python3 tools/session_statusline_setup/session_statusline_setup.py --repo-root .
python3 tools/session_statusline_setup/session_statusline_setup.py --repo-root . --install
```

The caches live under `~/.cache/session_statusline/` as `console.json`
and `sums.json`. Delete the directory to reset them.

## Exit codes

- 0 on a rendered line, including every degraded case.
- 2 on a wrong invocation, with the usage on stderr.

## Limits

- The two pool percentages follow the console display order: the first
  pool renders as `5h`, the second as `wk`. The mapping is an
  assumption about an undocumented endpoint.
- The detector reads the payload, the transcript, and the console. It
  makes no other network call.
