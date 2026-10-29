# handover_telemetry

A stdlib package for per-task handover telemetry. The hook module
records session events to a local redacted log. The CLI reads that log
and the Claude Code session transcripts, and renders a redacted
telemetry report as markdown or JSON. The `handover-telemetry` skill
gives the commands. The spec at `openspec/specs/handover-telemetry/`
owns the behavior.

## Why

A handover issue needs the cost, the model mix, the timings, the
decisions, and the friction of a run. The numbers sit in the session
transcripts and the hook log, and no tool extracted them. This package
is that one extraction and redaction authority.

## Commands

The shared repository venv interpreter runs the package. The unit
`zai-routing-audit-python-deps` in `tools/project_setup/registry.json`
owns that venv.

```bash
VENV=tools/zai_routing_audit/.venv/bin/python
PYTHONPATH=tools/handover_telemetry $VENV -m handover_telemetry build --out /tmp/handover-report.md
PYTHONPATH=tools/handover_telemetry $VENV -m handover_telemetry build --json
PYTHONPATH=tools/handover_telemetry $VENV -m handover_telemetry build --session <id> --out /tmp/r.md
PYTHONPATH=tools/handover_telemetry $VENV -m handover_telemetry sessions
PYTHONPATH=tools/handover_telemetry $VENV -m handover_telemetry build --create   # network; gh auth needed
```

Exit 0 on success and 2 on operational failure. The default path makes
no network call. Flags: `--project-dir`, `--transcript`, `--session`,
`--prices`, `--out`, `--json`, `--create`, `--repo`.

## The hook

`.claude/hooks/cc-logging.sh` runs on the PreToolUse, PostToolUse,
PermissionRequest, SessionStart, SessionEnd, and Stop events of this
repository. It appends one redacted JSON line per event to
`.cc_logging/<session-id>.jsonl`, records its own duration, and always
exits 0. The directory stays out of version control through
`.gitignore`. The doctor at
`tools/handover_telemetry_setup/handover_telemetry_setup.py`
examines the wiring, and the `handover-telemetry-hook` registry unit
installs it on a clean clone.

## Redaction

Three layers guard every output. The callers only hand allowlisted
fields to the engine. The engine scrubs token shapes, keys, JWTs, PEM
blocks, credential pairs, emails, IP addresses, credentials in URLs,
home paths, and timezone names, and catches high-entropy secrets with
a pure-hex exemption that keeps commit ids. The report ends with the
redaction counts. Raw prompt and response text never leaves the
parser. A hostname never appears in any output.

## Prices

`handover_telemetry/pricing.json` maps a model id to rates in USD per
million tokens, with a source date per entry and an `alias_of` form
for variants. A missing cache rate falls back to the Anthropic
multipliers of 0.1, 1.25, and 2.0 on the input rate. A model with no
entry renders as unknown. Update the file by hand when prices change,
and keep the source and the date in the entry.

## Tests and gates

```bash
tools/zai_routing_audit/.venv/bin/python -m pytest tests/handover_telemetry
tools/zai_routing_audit/.venv/bin/python -m pytest tests/handover_telemetry -q \
  --cov handover_telemetry --cov-branch --cov-fail-under=100 --cov-config .coveragerc
tools/crapper/crapper --threshold 10 --use-existing-coverage tools/handover_telemetry
tools/dryer/dryer --threshold 0.8 --fail-above tools/handover_telemetry
```

The live checks are opt-in: `HANDOVER_TELEMETRY_E2E=1` runs the real
transcript scan, and `HANDOVER_TELEMETRY_E2E=1` plus
`HANDOVER_TELEMETRY_E2E_REPO=<owner/repo>` adds one gh issue round
trip that closes its issue.

### Mutation run

Run mutmut on an out-of-tree copy, never inside the repository. The
doctor and shim contract tests stay in the repository suite, so the
copy drops `tests/test_setup_doctor.py` and `tests/test_hook_shim.py`:

```bash
rm -rf /tmp/ht_mut && mkdir -p /tmp/ht_mut/tests
rsync -a --exclude __pycache__ tools/handover_telemetry/handover_telemetry/ /tmp/ht_mut/handover_telemetry/
cp tools/handover_telemetry/pyproject.toml tools/handover_telemetry/ruff.toml /tmp/ht_mut/
cp -r tests/handover_telemetry/. /tmp/ht_mut/tests/
rm /tmp/ht_mut/tests/test_setup_doctor.py /tmp/ht_mut/tests/test_hook_shim.py
cd /tmp/ht_mut
$VENV -m pytest tests/            # the unmutated copy passes first
$VENV -m mutmut run
$VENV -m mutmut results
```

The copy's `pyproject.toml` points at `tests/handover_telemetry/`. Edit
the copy's pyproject.toml test paths to `tests/` before the run.
Target: 95 percent or higher. `__main__.py` carries a
`do_not_mutate_patterns` exclusion: the two-line shim holds no logic.

## Limits

The transcript format is internal to Claude Code and drifts between
versions. The parser skips unknown entry types and treats missing
fields as absent. Session listing reads every transcript in the
project directory, so a large directory costs one parse per file. On a
host with concurrent merges, the lead time uses the newest merge commit
after the first prompt. That merge can belong to another task.
