# Council Notes: design.md

## Author Summary

The design ports the intent-driven template into this Claude Code-only harness: pinned intent-driven schema, eleven skills, four agents, seeded ADRs, and a two-merge-plus-archive discipline, with spec-as-source installed but disabled.

## Reviewer Challenges

Three independent lenses (port fidelity, workflow fit, reality and gates) reviewed the design. Findings, all confirmed:

- The `openspec-verify-change` port as named would be clobbered: the name is a CLI-owned skill directory, and the upstream file carries `generatedBy`. The claimed safety reason (no generated field) was false.
- The agent frontmatter mapping lost two semantics: upstream agents carry no `name:` field (Claude Code silently skips them), and upstream `bash: deny` inverts under Claude Code's allowlist default (all tools when omitted).
- The two-merge flow left the archive commit with no review path; a direct push to main would contradict CLAUDE.md.
- The verbatim git-discipline port contradicts the pipeline's autonomous commit and merge steps.
- The glossary seed used a root file the skill never reads.
- Inventory drift: one-vs-two seed ADRs across artifacts, eight-vs-six generated skills, four-vs-five ADR templates, a `tasks: []` line that hides the commented seed, and unpinned working directory for schema commands.

## Resolutions

- Accepted: port renamed to `verify-change`; stale `generatedBy` dropped; provenance test named as the clobber detector (D3, D6).
- Accepted: explicit frontmatter mapping with required `name:` and read-only `tools:` allowlists for the adversarial pair (D4).
- Accepted: three reviewed squash-merge PRs per change; no direct push to main (D7).
- Accepted: git-discipline gate lines become pipeline checkpoints; the user's task approval is the explicit ask (D3).
- Accepted: glossary seeds at `glossary/business.md` and `glossary/technical.md` (D9).
- Accepted: all inventory corrections and the repo-root cwd rule (D2, D5, D8, D10).

## Remaining Risks

- A future profile change that re-enables `verify` regenerates a CLI skill under the old name; the port keeps its own name, so the risk is a duplicate, not a loss.
- The schema command format is experimental upstream; a CLI update may need a one-change migration.
