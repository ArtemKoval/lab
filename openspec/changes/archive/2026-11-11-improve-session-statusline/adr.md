# ADR Review Manifest

- Status: completed
- Review date: 2026-11-11

## Review Summary

The review walked the supersession graph of `adr/` (0001 through
0016, and 0013 supersedes 0012). No new ADR follows. The effort
display rule is a tool-level render decision, and its trade-offs
live in design.md.

## In-Force ADRs Reviewed

- `adr/0002-claude-code-single-harness.md` - accepted, in force. The
  line renders inside Claude Code sessions, and no second harness
  enters.
- `adr/0004-enforce-ste-in-specs.md` - accepted, in force. The
  delta spec and the change artifacts follow the mechanical STE
  rule set. Quotes and code spans stay exempt.
- `adr/0011-pin-glm-5-3-flash-on-every-role.md` - accepted, in
  force. The coding plan serves glm-5.3-flash on every slot, and
  the mapping targets exactly that serving path.
- `adr/0016-fast-mode-delivery-contract.md` - accepted, in force.
  This delivery runs the normal flow, and no fast run reads it.

## New Durable ADRs Created

None.
