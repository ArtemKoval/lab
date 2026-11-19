## Context

The lab carries the crm engine with three domain packs: insurance, helpdesk,
and opsdemo. The pack seam is `crm/domains/loader.py` plus the manifest
contract. The private child repository `ArtemKoval/library_crm` forked this
lab at `05c3ddd` on 2026-10-31 and built the library assignment on the same
engine: a fourth pack, two engine features, a dashboard vocabulary feature,
a video tool, and the assignment records. The child seed is byte-identical
to the fork base, so a three-way merge with base `05c3ddd` is exact. The
dry run in a scratch clone merged 232 files. The raw merge conflicts in
7 files with 10 hunks. The applied merge excludes `openspec/specs/`, which
leaves 6 conflicts for hand resolution and delivers the spec content
through the change deltas at archive time.

The in-force ADR set constrains the design: ADR 0004 enforces STE in specs,
ADR 0005 adopts the quality tools, ADR 0007 fixes the pack seam, ADR 0013
supersedes 0012, and ADR 0017 adopts the local Langfuse tracing. The child
predates the lab's dspy-gate registry, so none of the ported capabilities is
governed, and the ordinary gates rule.

The ported pieces attach at these points:

```
lab repository
  crm engine
    backend + agent + context + auth      engine core (lab, with Langfuse)
      <<PORT>> desk decision, lead resolution with the issued state
    pack seam: crm/domains/loader.py + manifest contract (ADR 0007)
      insurance | helpdesk | opsdemo | <<PORT>> library
      manifest gains the vocabulary section <<PORT>>
    GET /api/pack
      serves declarations + <<PORT>> vocabulary payload
    dashboard (React)
      <<PORT>> renders labels, contract rows, award unit days or money
    deploy
      compose.yaml: emulator + langfuse profile (lab)
        <<PORT>> demo db service, loopback-bound, from the child
      <<PORT>> compose.demo.yaml override publishes the db publicly
      <<PORT>> demo_up.sh + demo_down.sh, the override file included
    e2e (playwright): default insurance | <<PORT>> library flow spec
  tools/slidecast <<PORT>>   tests/slidecast <<PORT>>
  docs/wiki + docs/videos <<PORT>>   HARNESS.md + SCALE.md <<PORT>>
  openspec deltas: crm-library-domain, crm-pack-vocabulary,
                   slidecast-scenes <<PORT>>  (live specs land at archive)
  adr/0018 + adr/0019 <<PORT>>   .claude/commands/library-uow.md <<PORT>>
```

## Goals / Non-Goals

**Goals:**

- The lab history carries every child-side artifact, with the merge surface
  explicit and reviewed.
- The ported engine code integrates with the lab's evolved engine, proven by
  the complete suite, the dashboard gates, and the e2e flow of the library
  pack.
- The lab's harness, compose defaults, and Langfuse profile stay dominant.
- Every ported spec scenario holds after the merge.

**Non-Goals:**

- No new engine capability beyond the child's work. This change ports, it
  does not design new behavior.
- No promotion of the ported capabilities into the dspy-gate governed
  registry.
- No change to the child repository on GitHub.
- No borrower self-service portal, account CRUD, or inventory CRUD. The
  child cut the same scope, and `HARNESS.md` records the cut.

## Decisions

- **Three-way merge with base `05c3ddd`, not hand-copying.** The seed is
  byte-identical to the fork base, so the merge applies the child's exact
  diff. A hand-copy would lose the 71 child-modified files that lab never
  touched. Alternative rejected: a history-preserving merge commit. The lab
  squashes pull requests, so the child commits would flatten anyway.
- **The applied merge excludes `openspec/specs/`.** The change deltas carry
  the spec content byte-faithful, and the archive flow applies them to the
  live specs, as the openspec discipline intends. Applying the live spec
  files in the implementation too would make the archive a silent no-op or
  a duplicate apply. The raw merge conflict in the `crm-engine` live spec
  therefore never reaches the implementation. 6 conflicts resolve by hand.
  Alternative rejected: land the live specs twice, once per mechanism.
- **Six conflict resolutions by union, compose by design.** `CLAUDE.md`,
  `.coveragerc`, `.gitignore`, `crm/README.md`, and the `crm-local-aws`
  skill take both sides, with the lab lines first and exact duplicate lines
  deduplicated. The compose resolution builds on facts: the fork base
  carried only the emulator, the lab added the Langfuse profile, and the
  child added the demo `db` service. The merged base `compose.yaml` keeps
  the Langfuse services and gains the `db` service bound to
  `127.0.0.1:5433`. The new `compose.demo.yaml` override replaces the
  binding with the public `5433:5432`, and `demo_up.sh` passes both files.
  A compose test pins the contract: the base binds the loopback, and the
  override publishes. Alternative rejected: the child's compose publishes
  the demo Postgres on all interfaces at all times, which gives the lab an
  unsafe default.
- **Ported ADRs landed on the proposal branch as 0018 and 0019.** The lab
  owns 0010 through 0017. Each ported ADR keeps the child content verbatim
  and carries one ported-from line. The status line of 0019 is normalized
  to the lab house syntax. Alternative rejected: keep the child numbers,
  because the files would collide.
- **Spec text ports verbatim, without surface tags.** The child specs carry
  36 requirements and 62 scenarios in the shared convention, and the three
  new-capability deltas carry the child Purpose sections verbatim, which
  the archive flow copies into the live specs. The capabilities stay
  outside the governed registry, so the surface-tag retrofit waits for a
  promoting change. Two deliberate divergences sit beside the verbatim
  rule: one duplicate scenario heading in the crm-engine delta is renamed,
  because the lab's id-uniqueness lint refuses the child's copy-paste
  pair, and the crm README's demo paragraph names the `--emulator` flag
  the ported script actually takes, because the child text names a flag
  that does not exist. Alternative rejected: retag 62 scenarios now, which
  churns ported text with no governed consumer.
- **The child's five archived change folders copy into the lab archive as
  provenance.** They are inert to the openspec tooling and carry the design
  rationale of the child work.
- **Skip list.** The stale child change `add-sec-scan` (the lab shipped
  `tools/sec_scan`), the child's `.claude/tests/` stray, and the mutator
  scratch `W`, `W3`, and the two concat files under `tests/slidecast/`. The
  `.gitignore` entries `W/` and `W3/` port, because the mutation workflow
  recreates them out of tree.
- **No new registry unit.** The slidecast tests import the package with the
  standard library only and run in the root suite, like the notebook tests.
  The port script at `tools/port_library_crm/` is change-owned code with
  its own unit tests, and it needs no registry unit either.
- **Gate scope: the mutator over every ported Python module.** The operator
  chose the mutator over the whole ported Python surface, beside crapper,
  dryer, and the complexity gate over the same surface. The measured
  surface is 5059 production Python lines, with 4435 test lines beside
  them. The mutator run executes out of tree in a copy that mirrors the
  repository layout, because the slidecast conftest switches its import
  root on `MUTANT_UNDER_TEST`. The dashboard TypeScript carries the vitest,
  tsc, eslint, and prettier gates, as every existing dashboard file does.
  The lab holds no JavaScript mutation tool, so this change introduces
  none.

## Risks / Trade-offs

- [The child code integrates with an engine that moved since the fork] ->
  the complete crm suite, the dashboard gates, and the library e2e flow run
  on the merged tree before the pull request. The six-file conflict set
  bounds the overlap with the Langfuse work.
- [The mutation gate over 5059 production lines takes hours] -> the run
  executes out of tree in the background while the review steps run, per
  module.
- [The ported demo scripts bind 0.0.0.0 and expect public ports] -> the
  exposure lives behind `compose.demo.yaml` and `demo_up.sh` alone, and
  `demo_down.sh` closes it. The base compose binds the demo database to the
  loopback, and a compose test pins that contract.
- [The merged diff touches one gate-protected pattern] -> the inventory
  against the protected set names two hits,
  `tests/slidecast/conftest.py` and `tests/port_library_crm/conftest.py`,
  both new files that add tests and weaken no gate. The pull request body
  carries the `gate-integrity: acknowledged` line at creation, and the
  operator merge acknowledges it.
- [4.9 MB of video binaries enter the repository] -> the size grows once,
  with the screenshots precedent. The decks and `build_all.sh` allow a
  rebuild, so the binaries can regenerate.
- [Ported prose drifts from STE] -> the mechanical STE gate re-examines
  every ported `openspec/` file, and the port commit review covers the root
  records.

## Migration Plan

The feature branch `feat/port-library-crm` carries the proposal artifacts
and the two ported ADRs. The proposal pull request merges first. The
implementation branch, cut from the merged main, carries the applied merge
in grouped commits: the crm pack and engine merge, the tool and its tests,
and the docs and records. The suite, the dashboard gates, and the quality
gates run on the branch. One implementation pull request squashes into
`main`. The archive pull request applies the deltas to the live specs and
follows. Rollback: revert the implementation commit. The child repository
stays untouched, so the source of every artifact survives a revert.

## Open Questions

- The desk and resolution fixtures may need adjustments in the lab's
  evolved `crm/conftest.py`. The suite run resolves this. The task list
  carries the verification.
- The saturation pass scope may need a baseline for the slidecast modules.
  The implementation examines `tools/saturation_pass/` scope rules and
  initializes the baseline through the `saturation-run` skill when the tool
  falls in scope.
