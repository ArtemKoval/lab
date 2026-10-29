# ADR Review Manifest

- Status: completed
- Review date: 2026-10-28

## Review Summary

ADR review completed for this change. The review examined the in-force records for conflicts with the adoption decision and found none. This change extends the harness inside the discipline ADR 0001 established. It stays on the single harness surface ADR 0002 fixed. It follows the adoption pattern ADR 0003 set for vendored mechanics. It keeps the STE rule of ADR 0004 through the vendored-file exemption in `openspec/config.yaml`. The pipeline edits are additive, so no in-force SHALL changes.

## In-Force ADRs Reviewed

- adr/0001-add-intent-driven-harness.md - this change follows the two-merge discipline and the artifact set it established. No supersession needed.
- adr/0002-claude-code-single-harness.md - the skill and the tools target the Claude Code harness only. No supersession needed.
- adr/0003-adopt-superpowers-execution-mechanics.md - this change reuses its vendored-owned-code pattern and leaves its Step 14 Analyse designation untouched. No supersession needed.
- adr/0004-enforce-ste-in-specs.md - all new spec and ADR text passes `tools/spec_ste_check`. The skill body exemption follows the config rule. No supersession needed.

## New Durable ADRs Created

- adr/0005-adopt-ub-mode-and-quality-tools.md - the adoption of the ub-mode discipline, the three vendored gate tools as default gates, and the CI wiring, with the unlicensed-skill risk recorded.
