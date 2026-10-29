# Council Notes: proposal.md

## Author Summary

The author draft carried the three grill decisions: transcripts plus a new hook, markdown by default with a flag for gh, and the pipeline mandate. It named two new capabilities and one modified capability, and it kept the cost formula and the field names out as design work.

## Reviewer Challenges

- Three sentences passed the 20 word procedural cap or the 25 word cap, so the mechanical gate would fail.
- The Step 14 sentence read as a change to a log file, not to the skill text.
- The full hardware bullet contradicted the redaction mandate.
- Six research items had no home in the proposal. The items were synthetic model errors, the cache cost formula, unknown prices, GenAI field names, vanity metrics, and the model split.
- The two-package split had no ASIT justification and contradicted the spec_ste_check precedent of one package with cli.py and hook.py.
- The DORA bullet named three proxies and stayed silent about the other two metrics.
- The registry story contradicted the enforce-ste-in-specs precedent that a stdlib tool needs no unit.
- Impact missed the .gitignore entry, the pricing table, the CI coverage floor, and the hook shim with its timeout.
- The template bullet named sections that the template does not have, and it did not name the file.

## Resolutions

- Accepted: all nine required changes. The sentences got splits. Step 14 got a rewrite bullet. The specs bullet got an omission list. The research items got two design-record bullets. The layout is one package with one capability. DORA got a mapping sentence that delegates the table to the design. The registry story is one wiring unit and no dependency unit. Impact names the gitignore entry, the pricing file, the CI floor, and the shim. The template bullet names the file and keeps the five existing sections.
- Rejected: none. Every finding survived a look at the code or the gate rules.
- Deferred: the exact hook event list and the pricing numbers stay design and implementation work.

## Remaining Risks

- The transcript format drifts between Claude Code versions. The parser must skip unknown types and treat fields as optional.
- Pricing data goes stale. Unknown-price handling bounds the damage, and the file carries a source date.
- The hook runs on every tool call. Its leanness budget and timeout need a measurement during apply.
