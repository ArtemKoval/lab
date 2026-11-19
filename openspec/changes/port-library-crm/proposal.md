## Why

The private repository `ArtemKoval/library_crm` holds the finished library
assignment: a fourth domain pack for the crm engine, the engine features the
pack needs, a narrated-video tool, and the assignment records. The fork
diverged from this repository at `05c3ddd` on 2026-10-31 and carries 68
commits. The work exists in one place only, outside the mainline lab. This
change ports the artifacts into `ArtemKoval/lab`, so the lab carries the
library pack and every child-side improvement in one history.

## What Changes

- Port the `library` domain pack at `crm/domains/library/`: the manifest, the
  rules, the protocol, the policy documents, the seed data, the pack tests,
  and the pack evals. The pack maps the engine nouns to the library nouns and
  encodes the assignment rules: one copy per loan, the 14-day term, the
  three-loan cap, and the desk and lead librarian roles.
- Port the engine features the child added on top of the fork base: the desk
  librarian decides a waiting request on its case page, and the lead resolves
  a referred request through `POST /api/cases/{case_id}/resolution`. The
  resolution is idempotent through an issued state: a request that already
  carries a resolution refuses a second one.
- Port the pack-vocabulary feature: the manifest carries a vocabulary section
  with labels, contract rows, award format, and refusal messages. The backend
  serves it on `GET /api/pack`, and the dashboard renders every domain word
  and the award unit from the pack, with the core dashboard carrying no
  insurance word of its own.
- Port `tools/slidecast` with its test suite at `tests/slidecast/`: one
  narrated video from one JSON deck, through edge-tts and ffmpeg. Port the
  four assignment videos, their decks, and `build_all.sh` at `docs/videos/`.
- Port the assignment records: `HARNESS.md`, `SCALE.md`, `docs/wiki/`,
  `crm/docs/` with its screenshots, runbook, and vocabulary inventory, and
  the five child archive change folders into `openspec/changes/archive/` as
  provenance.
- Port the harness additions: the `library-uow` slash command, the `crm-app`
  and `crm-local-aws` skill updates, and the library rows in the root
  `README.md` and `CLAUDE.md`.
- The two child ADRs landed already on this branch as
  `adr/0018-library-assignment-history-discipline.md` and
  `adr/0019-pack-vocabulary-and-award-units.md`, because the lab owns
  numbers 0010 through 0017. Each keeps the child content verbatim and
  carries one ported-from provenance line.
- Add the child's demo `db` service to the base compose with a loopback
  bind, add `crm/deploy/compose.demo.yaml` as the override that publishes it
  on the public address, and point `demo_up.sh` at both compose files.
- Merge method: a three-way merge with the fork base `05c3ddd`. The raw
  merge touches 232 files and conflicts in 7 files with 10 hunks. The
  applied merge excludes `openspec/specs/`, so 6 conflicts resolve by union
  or design in the implementation, and the spec deltas of this change
  deliver the spec content at archive time. The merge is dry-run verified
  in a scratch clone.

Out of scope, recorded here so the cut is explicit:

- The child's stale in-flight change `openspec/changes/add-sec-scan`. The lab
  already shipped `tools/sec_scan` and the `secret-scan` workflow.
- The child's stray scratch under `tests/slidecast/`: the `W` and `W3`
  mutator output directories and the two concat text files. The `.gitignore`
  entries `W/` and `W3/` port, because the mutation workflow recreates them.
- The child's `.claude/tests/` directory. It holds one stray duplicate of a
  slidecast test. The lab keeps its tests under `tests/`.
- The child repository itself stays on GitHub untouched as the assignment
  archive.

## Capabilities

### New Capabilities

- `crm-library-domain`: The library pack and its loan desk flow: the manifest
  and its declarations, the rules and the protocol, the policy documents, the
  seed data, the instructions, the evals, the validator and smoke gates, the
  desk decision and the lead resolution flows, and the e2e flow.
- `crm-pack-vocabulary`: The pack vocabulary contract: the manifest vocabulary
  section, the `GET /api/pack` payload, the dashboard rendering rules, the
  award formats `money` and `days`, and the refusal message family.
- `slidecast-scenes`: The slidecast tool: one narrated video from one JSON
  deck, the scene model, the render pipeline, and the CLI contract. The name
  follows the child repository's capability name.

### Modified Capabilities

- `crm-engine`: Add the desk decision requirement for a waiting request and
  the lead resolution requirement family for a referred request, from the
  child's live spec.
- `crm-domain-pack`: Add the vocabulary section requirement to the pack
  manifest contract, from the child's live spec.

## Impact

- `crm/`: backend, agent, context, dashboard, e2e, deploy, and the new pack.
  The engine carries no new domain word. The vocabulary feature removes the
  insurance words from the core dashboard. `crm/deploy/compose.yaml` keeps
  the Langfuse services and gains the loopback-bound demo `db` service and
  the override file beside it.
- `tools/slidecast/` and `tests/slidecast/` are new. The tests run in the
  root suite with the standard library only. The two new test conftests
  touch a gate-protected path pattern, so the implementation pull request
  body carries the `gate-integrity: acknowledged` line.
- Docs and records: `README.md`, `CLAUDE.md`, `HARNESS.md`, `SCALE.md`,
  `docs/wiki/`, `docs/videos/`, `crm/docs/`, `glossary/business.md`,
  `adr/0018`, `adr/0019`.
- Harness: `.claude/commands/library-uow.md`, the `crm-app` and
  `crm-local-aws` skills, `.coveragerc`, `.gitignore`.
- No governed capability is touched: the dspy-gate registry declares only
  `ticket-triage`, so the ordinary gates rule for this change.
- Dependency surface: edge-tts and ffmpeg are runtime needs of the slidecast
  render path only. The tests stub them, so the root suite stays hermetic.
