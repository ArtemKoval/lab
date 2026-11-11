# negative_instruction_audit

Inventories the prohibitive instructions in the agentic harness text
and classifies each against the guard-test pins. The tool answers one
question: which harness sentences tell the agent what not to do, and
which of them the guard tests pin? The scan is read-only and runs
without a network.

The tool owns the sentence detection and the pin classification. The
operator owns the contract judgment on the unpinned candidates: most
candidates are mechanical contracts or descriptive prose, and only a
thin band converts to positive phrasing.

## Commands

```bash
# Human-readable report
PYTHONPATH=tools/negative_instruction_audit \
  tools/zai_routing_audit/.venv/bin/python -m negative_instruction_audit

# Machine-readable report
PYTHONPATH=tools/negative_instruction_audit \
  tools/zai_routing_audit/.venv/bin/python -m negative_instruction_audit --json

# Another repository root
PYTHONPATH=tools/negative_instruction_audit \
  tools/zai_routing_audit/.venv/bin/python -m negative_instruction_audit \
  --repo-root /path/to/repo
```

## Exit codes

- 0 on a completed scan.
- 2 on an operational failure, with one next action on stderr.

## Limits

- The marker set covers explicit prohibitions (never, do not, should
  not, must not, shall not, cannot, avoid, and sentence-start no).
  Positively-phrased prohibitions such as "Reply in the review
  thread, not as a top-level comment" stay outside the recall.
- Descriptive sentences that contain a marker word ("The scan never
  edits") appear as candidates. The operator filters them.
- Pin classification matches whitespace-collapsed substrings against
  the string literals of the test tree, so a paraphrased pin reads as
  a candidate.
