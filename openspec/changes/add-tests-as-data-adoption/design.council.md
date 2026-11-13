# Council Notes: design.md

## Author Summary

The author drafted the element map with 14 rows and verdicts of
adopt, covered, partial, and skip, three adoption candidates with
future change ids, five rejections, edge cases and risks, and a
no-diagram note. The author raised five concerns: the YAML dependency
home, the thin customer seat, the guard order, the port oracle noise,
and the property-based testing reason.

## Reviewer Challenges

- The parametrize count spoke for the repository but counted only the
  root tests tree. The crm tree holds 36 files with parametrize.
- Three YAML positions contradicted each other across rows.
- ADR 0008 carries the proposed status, and the draft cited it as
  settled.
- Candidate 2 named no input source and inverted the runner
  mechanics.
- Candidate 1 defined no setup or side-effect rows against its own
  element row.
- The open unknowns had no list, against the working rules.
- The no-diagram note deviated from the direct precedent as a
  section.
- The printers row carried a covered reason under a skip verdict.
- The verification section named no pytest STE gate run.

## Resolutions

- Accepted: the recount by the primary agent confirmed 8 root files
  and 36 crm files under the strict pattern, and the row now scopes
  each count to its tree.
- Accepted: one YAML position survives. The first delivery uses CSV
  only, and the plan adds structured YAML after the test dependency
  policy lands.
- Accepted: the row cites the observed floci and apfel setups and
  names ADR 0008 with the proposed status.
- Accepted: candidate 2 now states scripted inputs, deterministic
  stdout surfaces, the compare direction, the deviations ledger
  against the openspec change artifacts, and the determinism probe.
- Accepted: candidate 1 defers setup and side-effect rows to a later
  stage.
- Accepted: the open unknowns list carries four items, each with a
  status and a next probe.
- Accepted: the primary agent folded the no-diagram decision into
  Verification as one sentence.
- Accepted: the plan now orders the candidates, and candidate 3
  states that it follows `add-scenario-tables`.
- Accepted: the printers row now carries the covered verdict.
- Accepted: Verification names the CLI scan and the pytest gate.

## Remaining Risks

- The customer seat stays thin with one reader. The expansion trigger
  caps the cost, but the format returns value only while the operator
  reads tables in reviews.
- The guard read model stays undefined until candidate 3 lands, and
  the guard can block the operator iterations if the read model is
  wrong.
- The port oracle rests on upstream determinism at the pinned
  milestone. The probe guards it, but a flaky upstream surface can
  still force a scope cut.
