# ADR Review Manifest

- Status: completed
- Review date: 2026-10-30

## Review Summary

No new durable decision. The tool is a plain house-pattern CLI, and the
non-destructive-by-default rule with an explicit destructive flag is already
the pipeline's own Step 2 rule.

## In-Force ADRs Reviewed

- `adr/0007-crm-engine-with-domain-packs.md` - accepted, in force. The scanner
  treats `crm/.env` and pack files as ordinary repo files, with no pack-awareness
  needed.
- `adr/0008-local-emulator-first-aws-targets.md` - accepted, in force. The
  dummy AWS credentials the emulator invites (`test`/`test`) are recognized as
  emulator dummies and reported as such, not as leaks.

## New Durable ADRs Created
