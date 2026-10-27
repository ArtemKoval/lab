---
name: spec-ste-check
description: Run or read the spec STE gate. Use when a spec write gets blocked by the SPEC-STE hook, when a pytest run fails on spec_ste_check, or when the user asks to examine a file for ASD-STE100 violations. Gives the commands, the exit codes, the rules, and the fixes.
---

# spec-ste-check

The repo enforces a mechanical ASD-STE100 rule set on spec text: `openspec/specs/**` and the active directories under `openspec/changes/**`. One CLI owns the rules. The pytest gate and the `PreToolUse` hook call it.

## Rules

Errors: a sentence over its word cap (20 words in an imperative sentence, 25 in any other sentence), a semicolon, a contraction, a progressive tense, and the banned words that CLAUDE.md names (`perform`, `utilize`, `ensure`, `provide`, `check` as a verb). A perfect tense is a warning. Warnings never fail a gate.

Exempt: code spans, fenced code blocks, headings, commands, paths, identifiers, quoted text. A code element is one word. A hyphenated group is one word.

## Commands

Run the checker through the shared repository venv:

```bash
PYTHONPATH=tools/spec_ste_check tools/zai_routing_audit/.venv/bin/python -m spec_ste_check openspec/specs/
PYTHONPATH=tools/spec_ste_check tools/zai_routing_audit/.venv/bin/python -m spec_ste_check --json --repo-root .
```

- With no paths, the tool scans the gate scope and skips `openspec/changes/archive/`.
- Exit 0 means a clean scan. Exit 2 means at least one error, or a file that the tool cannot read.
- `--json` prints one JSON object with the violations, the error count, and the warning count.

## Fix a blocked write

1. Read the `SPEC-STE blocked` line on stderr. It names the file, the line, the rule, and the sentence.
2. Rewrite that sentence: split it at a clause boundary, or replace the banned word (`provide` -> `carry`, `give`, or `report`; `ensure` -> `make sure`; `check` as a verb -> `examine`; `perform` -> `do`; `utilize` -> `use`).
3. Keep every SHALL and MUST obligation exactly. Do not merge or drop clauses.
4. Write again.

## Results

- A human report prints one line per violation: file, line, severity, rule, sentence.
- Warnings carry the severity `warning`. A warning never blocks a write or fails a test.
- A `sentence-length` error needs a split, not a word deletion. Keep the articles, the verbs, and "that".

## Known problems

- The tense and word heuristics use regex patterns. Attested exceptions live in allowlists in `tools/spec_ste_check/spec_ste_check/rules.py`. A false hit gets an allowlist entry, never a loosened pattern.
- A sentence that wraps across two lines evades the caps. House prose keeps one sentence on one line.
