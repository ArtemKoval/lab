# Proposal: add-sec-scan

## Why

The repo carries model keys, tokens, and credentials across `crm/.env`, the
skills, and the git history, and a past lesson (the memory note on fixture
secrets) shows a leaked key is a real hazard. Nothing scans for one, and a
leaked key today has to be revoked by hand.

## What Changes

- Add `tools/sec_scan/`: a stdlib CLI that scans the working tree (and
  optionally `git log -p` history) for known secret shapes — OpenRouter keys,
  AWS access keys, GitHub tokens, Slack tokens, private-key blocks, and
  high-entropy assignments to credential-looking names — and reports each
  finding with its file, line, provider, and the revoke path.
- `--revoke` gates every actual revocation. With an OpenRouter provisioning
  key in the environment, found OpenRouter keys are disabled through the
  provisioning API (recoverable — disable, not delete). For every other
  provider the tool prints the exact revoke command and stops short.
- Add `.claude/skills/sec-scan/SKILL.md` for the scan-and-revoke workflow.
- Register the tool in `tools/project_setup/registry.json`.

## Capabilities

### New Capabilities

- `sec-scan`: The scanner, the report, and the gated revocation.

### Modified Capabilities

## Impact

- New `tools/sec_scan/` (stdlib only) and its tests under `tests/sec_scan/`
  built from synthetic, same-shape fixture secrets assembled at test time so
  no literal matches GitHub push protection.
- New skill and one registry line. No changes to existing tools.
