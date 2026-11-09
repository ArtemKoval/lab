---
name: dead-export-scan
description: Scan the owned tools for dead code with vulture, and read the findings. Use this skill when the user asks to scan for dead exports or unused code, when a dead-code finding needs the reading rules, or when the feature-pipeline gates miss a trivial dead export. The scan is opt-in and read-only.
---

# Dead-export scan

The scanner at `tools/dead_export_scan/` runs vulture over Python
files and reports unused code. The scan reads the tree and never
edits. The scan is opt-in: no pipeline step runs it, and a later
change promotes it to a gate when the first runs name real residue.

## Run the scan

Run through the shared repository venv, which carries the pinned
vulture:

```bash
tools/zai_routing_audit/.venv/bin/python tools/dead_export_scan/dead_export_scan.py
```

The default scan walks `tools/` and skips the vendored and test
trees. Scope the scan with `--paths`:

```bash
tools/zai_routing_audit/.venv/bin/python tools/dead_export_scan/dead_export_scan.py --paths tools/dead_export_scan
```

Raise vulture's confidence threshold with `--min-confidence` when the
run names style noise. The default is 60.

## Read the results

- Exit 0 means a clean scan. Exit 2 means findings or an operational
  failure.
- Each finding carries the file, the line, the name, and the type
  (function, class, import, variable, or attribute).
- A finding is a claim, not a verdict. Examine the callers before you
  remove code, because a name that dynamic code reaches by string
  looks dead to vulture.
- `--json` carries `ok`, the findings, and the errors, for machine
  readers.

## Failure routes

- `vulture missing` means the shared venv lacks the pinned vulture.
  Install it with
  `tools/zai_routing_audit/.venv/bin/python -m pip install -r tools/dead_export_scan/requirements.txt`.
- `path missing` means a `--paths` entry does not exist. Fix the
  path and run again.
