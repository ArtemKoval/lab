# Council Notes: design.md

## Author Summary

Ten decisions: adopt mechanics not plugin (D1); docs-confirmed hook envelope and settings shape (D2); charter carries pointers, not step prose, with drift-pin strings under test (D3); plan_exec as testable Python under the house nested layout sharing the registered venv (D4); brief reads both task shapes with dotted ids (D5); append-only ledger as git-ignored per-run scratch with a fixed convention (D6); adapted prose with pinned provenance for the three skills (D7); pipeline rules in the pipeline skill only, stale hooks claims removed (D8); CI via paths-ignore with the coverage floor in CI and mutation local (D9); two council files plus the ADR style record (D10).

## Reviewer Challenges

- The author draft dropped the `hookEventName` envelope fix and the mutation-mirror rsync excludes between versions; both restored as required.
- The draft deferred the hooks-field confirmation to implementation; the reviewer required it before the proposal freeze (Step 0.6), and the docs agent plus the hooks reference settled it during this round.
- The draft under-pinned the ledger: missing and identity-less ledgers had to exit 2, the plan path must resolve to absolute before compare, and the Ruling line format needed pinning.
- The draft missed the two stale "no hooks yet" statements its own deliverable makes false.
- The draft's mutation mirror implied a root `pyproject.toml` that does not exist; the tool's own pyproject travels inside the copied tool directory.
- The charter drift test needed named strings, not a promise to invent them later.

## Resolutions

- Accepted: all eight required changes from the reviewer round are in the final design (D2 envelope, D3 strings, D5 ledger cases, D8 stale statements, D9 mirror layout, task 2.3 git identity, D2 field confirmation moved before the freeze).
- Accepted suggestions: seven mechanics enumerated once; ruff `target-version = "py312"`; shared-venv note in the README; ledger directory convention stated; `$0` fallback; paths-ignore safety note tied to the undercover self-skip.
- Rejected: five blanket council files (the mandated skills own those review records); `bash <script>` invocation (PATH lookup).

## Remaining Risks

- The ledger convention relies on each run following it; no mechanism enforces the scratch location beyond the default.
- The CI job is new wiring; its first real run may surface environment gaps the contract test cannot see.
- The three ports adapt upstream prose; a future upstream revision needs a manual re-diff against the pinned commit.
