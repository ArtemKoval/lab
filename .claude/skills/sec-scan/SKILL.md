---
name: sec-scan
description: Scan the repository for possibly exposed keys and secrets — in the working tree and optionally the git history — and revoke what it found. Use this skill when the user asks to check the repo for leaked keys or credentials, to run a secrets scan, or to revoke an exposed OpenRouter key.
---

# sec-scan

The tool at `tools/sec_scan/sec_scan.py` scans the working tree (and
optionally `git log -p`) for known provider secret shapes — OpenRouter keys,
AWS access keys, GitHub tokens, Slack tokens, private-key blocks — plus
high-entropy assignments to credential-looking names. Each finding names its
file, line, provider, and the revoke path.

## Scan

From the repository root:

```bash
.venv/bin/python tools/sec_scan/sec_scan.py            # the working tree
.venv/bin/python tools/sec_scan/sec_scan.py --history  # tree + git log -p
.venv/bin/python tools/sec_scan/sec_scan.py --json     # machine output
```

Exit 0 means no findings; exit 2 means findings were reported. Vendored and
dependency directories are skipped.

## Diff scan in CI

The `secret-scan` workflow (`.github/workflows/secret-scan.yml`) runs the
tool in diff mode on every pull request and on dispatch:

```bash
.venv/bin/python tools/sec_scan/sec_scan.py --diff origin/main
```

The mode scans only the lines the diff adds, with the new-file line numbers.
Operator literal secrets travel through the `SECRET_SCAN_LITERALS`
repository secret into the job environment; the tool reads that variable,
splits it on newlines, and reports each literal finding with a SHA-256
prefix, never the value. A git failure fails the scan closed with exit 2.


## Revoke

Without `--revoke` the tool makes no network call: each finding carries its
revoke command for the hand. With `--revoke`, and with
`OPENROUTER_PROVISIONING_KEY` in the environment, found OpenRouter keys are
disabled through the provisioning API — disable, not delete, so it is
recoverable. Every other provider is printed as a manual step:

```bash
OPENROUTER_PROVISIONING_KEY=... .venv/bin/python tools/sec_scan/sec_scan.py \
  --revoke
```

## The fixture lesson

This repository once learned: never write a provider-shaped literal into a
test fixture — GitHub push protection blocks the push. Assemble fixture
secrets at test time from concatenated fragments, as `tests/sec_scan/` does.
