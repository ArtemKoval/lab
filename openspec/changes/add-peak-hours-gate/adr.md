# ADR Review Manifest

- Status: completed
- Review date: 2026-11-03

## Review Summary

One durable decision. The change turns the peak-window rule into a deterministic
harness gate instead of a prompt rule. The record lands as `adr/0012` at archive.

## In-Force ADRs Reviewed

- `adr/0004-enforce-ste-in-specs.md` - accepted, in force. The spec text of this
  change follows the mechanical rule set, and the checker passes it.
- `adr/0005-adopt-ub-mode-and-quality-tools.md` - accepted, in force. The new Python
  passes the same three gates, crapper, dryer, and mutator, on changed paths.
- `adr/0001-add-intent-driven-harness.md` - accepted, in force. The change adds one
  hook to the existing wiring instead of a second workflow.
- `adr/0010-adopt-spec-governed-agent-gates.md` - accepted, in force. This change
  stays outside the harness registry, so the ordinary gates govern it.
- `adr/0011-pin-glm-5-3-flash-on-every-role.md` - accepted, in force. The gate makes
  no model call, so the pins do not touch it.

## New Durable ADRs Created

### 0012 - Enforce the peak-window rule with a hook gate

- Status: proposed
- Date: 2026-11-03

#### Context

The lab routes Claude Code through z.ai GLM. z.ai charges peak-window rates Monday
to Friday, 14:00 to 18:00 Singapore Standard Time. A line in CLAUDE.md is a wish,
and nothing in the harness stopped a dispatch in the window. The alternatives: keep
the prompt rule only (drift stays invisible and nothing blocks), or switch settings
on a schedule (a cron flips configuration twice a day, every session inherits it,
and the flip point wedges runs that cross it).

#### Decision

Enforce the rule with a deterministic PreToolUse hook. The window is Monday to
Friday, 14:00 to 18:00 SGT, with a fixed UTC+8 offset, the start inclusive, and the
end exclusive. The gate denies every model-backed start in the window with exit
code 2 and names the window and the override. `ZAI_PEAK_HOURS_OVERRIDE=1` in the
hook process environment is the emergency path. Internal errors fail open, so a
gate fault never wedges a session. Rejected: the prompt-only rule (no enforcement),
the scheduled settings switch (brittle and global), and a whole-session prompt block
(it stops planning and chat, which the rule allows).

#### Consequences

Every new model-backed call in the window stops with the deny message. Work that
crosses the window boundary stops at its next dispatch. The override is one
variable at session launch. A wrong host clock shifts the window. The window
policy changes only through a superseding ADR.
