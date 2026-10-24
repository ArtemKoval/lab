# ADR Preferences

preferred-style: custom

When `preferred-style` is `unset`, ask the user which ADR style they prefer before drafting an ADR, then update this file with one of:

- `madr-full`
- `madr-minimal`
- `nygard`
- `y-statement`
- `custom`

If the user chooses `custom`, record a short note describing the preferred structure.

House style (custom): one decision per file at `adr/NNNN-kebab-title.md`, format of `adr/0001`: title line `# NNNN - Title`, bullets `- Status: accepted` and `- Date: YYYY-MM-DD`, then `## Context`, `## Decision`, `## Consequences` in short prose. Rejected options stay in the Decision prose. Supersession only through a new record whose context names the old one. The syntax (`Status:` line present, no `Supersedes:` line) is pinned by the harness contract test.
