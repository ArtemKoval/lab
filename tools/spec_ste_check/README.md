# spec_ste_check

A stdlib CLI that scans spec text and reports mechanical ASD-STE100
violations. It is the one rule authority for the gate: the pytest gate
and the `PreToolUse` hook call the same rules, so the repo holds one
standard, not two.

The rules examine prose only: code, commands, paths, identifiers, and
quoted text stay exempt. Errors: a sentence over its word cap (20 words
in procedural text, 25 in descriptive text), a semicolon, a contraction,
a progressive tense, and the banned words that CLAUDE.md names
(`perform`, `utilize`, `ensure`, `provide`, `check` as a verb). A perfect
tense is a warning. Warnings never fail the gate.

## Commands

The suite and CI run the tool through the shared repository venv:

```bash
PYTHONPATH=tools/spec_ste_check tools/zai_routing_audit/.venv/bin/python -m spec_ste_check docs/notes.md
PYTHONPATH=tools/spec_ste_check tools/zai_routing_audit/.venv/bin/python -m spec_ste_check openspec/
PYTHONPATH=tools/spec_ste_check tools/zai_routing_audit/.venv/bin/python -m spec_ste_check --json openspec/specs/
```

- With paths, the tool scans trees for `*.md` files and reads named files as given.
- With no paths, the tool scans the gate scope: `openspec/specs/**` and
  the active directories under `openspec/changes/**`. It always skips
  `openspec/changes/archive/`.
- `--repo-root` names the repository root for the default scope. The
  default is the working directory.
- `--json` prints one JSON object with the violations, the error count,
  and the warning count.
- Exit 0 means a clean scan. Exit 2 means at least one error, or a file
  that the tool cannot read.

## The gate and the hook

- The pytest gate `tests/spec_ste_check/test_ste_gate.py` runs the tool
  over the gate scope and fails the suite on an error.
- The hook `.claude/hooks/spec-ste-gate.sh` runs before `Write` and
  `Edit` on a spec path. An error blocks the write. If the checker
  cannot run, the hook allows the write and prints a note on stderr.

## Development

Run the tests with the shared venv:

```bash
tools/zai_routing_audit/.venv/bin/python -m pytest tests/spec_ste_check
tools/zai_routing_audit/.venv/bin/ruff check tools/spec_ste_check
```

### Mutation run

Run mutmut on an out-of-tree copy, never inside the repository:

```bash
rm -rf /tmp/ssc_mut && mkdir -p /tmp/ssc_mut/ssc/tests
rsync -a --exclude .venv --exclude __pycache__ --exclude .ruff_cache \
  tools/spec_ste_check/ /tmp/ssc_mut/ssc/
cp -r tests/spec_ste_check/. /tmp/ssc_mut/ssc/tests/
cd /tmp/ssc_mut/ssc
/full/path/to/lab/tools/zai_routing_audit/.venv/bin/python -m mutmut run
/full/path/to/lab/tools/zai_routing_audit/.venv/bin/python -m mutmut results
```

The unmutated copy passes first (`PYTHONPATH=/tmp/ssc_mut/ssc $VENV -m
pytest tests/`). Each survivor is a missing assertion: add a test until
it dies, or exclude it with a written reason. Target: 95 percent or
higher. `__main__.py` carries a `do_not_mutate_patterns` exclusion: the
two-line shim holds no logic, the same reason the coverage omit lists
it.

### Equivalent-mutant classes (written reasons)

The final run settles at a handful of survivors, each in a measured
equivalence class:

- `prose_sentences` `in_fence = None` and `in_span = None`: both values
  are falsy like the original, and the code only reads their truth.
- `word_count` unit join with padding: the padding adds no whitespace,
  and the count reads whitespace-separated tokens only.
- `is_imperative` strip-set widening with `X`: the first word is
  lowercased before the strip, so an `X` can never sit at either end.
- `_check_word_hits` fallback word `XXXX`: the value sits outside the
  determiner set and outside the noun allowlist, like the original.
- `check_tenses` index `[-1]` to `[1]`: the match always holds exactly
  two words, so both indexes read the participle.
- `cli.scan` encoding aliases: `UTF-8` is a registered alias of
  `utf-8`, and the locale encoding prefers UTF-8 on every platform the
  gate runs on.
- `hook.evaluate` dot-dot prefix check: the check is redundant, because
  every path outside the root fails the earlier first-segment test.
- `hook._post_edit_text` join branch for absolute targets:
  `os.path.join` returns an absolute second argument unchanged.
