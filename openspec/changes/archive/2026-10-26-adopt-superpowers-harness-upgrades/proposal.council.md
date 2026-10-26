# Council Notes: proposal.md

## Author Summary

One change adopts seven mechanics from obra/superpowers (MIT, commit 2ce8aa15): a SessionStart charter hook; a stdlib plan-execution CLI (brief, package, ledger); three ported skills; five new pipeline rules; ADR 0003 with the Step 14 reference designation; and a CI job for the root suite. Two capabilities: new `plan-exec`, modified `intent-driven-harness`. Three-merge delivery under the standing discipline.

## Reviewer Challenges

- Hook envelope: the draft omitted `hookEventName` inside `hookSpecificOutput`; the docs read only the nested form, and an extra top-level field injects the charter twice.
- Settings shape: `timeout` sits inside the hook entry, not on the matcher group; the draft was loose on placement and on the key-preservation count (three allow entries, not two).
- Path robustness: `#!/usr/bin/env bash` and a cwd fallback both break under a broken PATH; the reviewer required `#!/bin/bash`, a `$0`-derived fallback, and the exec bit.
- Grouping: plan_exec under `intent-driven-harness` broke the repo's one-capability-per-tool convention; the reviewer required a new `plan-exec` capability.
- CI filter: a narrow allowlist under-triggers for a suite that reads most of the repo; `paths-ignore` for `fde/**` and `llm_ops/**` is the sound shape.
- Bash gates: coverage and mutation cannot measure the hook script; the plan had to say so with reasons instead of promising impossible numbers.
- Scope: five blanket council files duplicate records the other mandated skills already own.

## Resolutions

- Accepted: exact envelope pinned in spec and test; exact settings shape pinned; `#!/bin/bash` plus `$0` fallback plus mode 100755; `plan-exec` as its own capability; `paths-ignore` CI filter; per-deliverable gate mapping; two council files with the rationale recorded in design D10.
- Rejected: invoking the script through `bash <script>` (a PATH lookup); a cwd fallback for the charter path; `requirements-dev.txt` for plan_exec (the registered shared venv is the one source of gate truth).
- Deferred: gate-tool version bounds for the shared requirements file (recorded follow-up); hook live-fire and runtime measurement (implementation tasks 1.5).

## Remaining Risks

- The charter adds about 60 lines to every session; bounded and tested.
- CI installs unpinned gate tools that can drift from local versions.
- `async: false` and the `shell` key follow the current docs reference; a harness update that changes hook fields needs a one-change migration.
