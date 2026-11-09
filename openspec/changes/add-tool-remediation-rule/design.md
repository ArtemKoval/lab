# Design: add-tool-remediation-rule

## Plan review

The review kept the report proposal as the plan. ASIT: Unification.
The exit-code contract in Step 2 exists, and the rule extends its
message shape. No new component enters the repository.

Alternatives the review rejected:

- An error taxonomy with tags. rea carries 27 tags because it serves
  about 160 tools. The lab tools are small, and no caller branches on
  an error tag today.
- A retrofit change for all existing tools. The report scopes the rule
  to new and touched tools, and a mechanical retrofit adds review load
  with no failure to repair.
- A gate tool that examines failure messages for a remediation line.
  The rule governs tool authors, and the suite guard on the skill text
  holds the rule in place. A message linter would judge prose, and no
  owned gate examines tool output prose today.

## The rule text

The rule lands in Step 2 after the CLI contract bullet:

- Every operational failure (exit 2) names one next action in its
  message. A `--json` failure carries a `remediation` field beside the
  exit code. New and touched tools adopt this rule.

## Edge cases

- A tool without a `--json` flag keeps the message rule only. The
  `remediation` field sentence is conditional on the flag.
- A failure whose next action is trivial keeps the rule. The message
  names the action in one line, and the line costs little.
- The rule does not constrain success output. Exit 0 keeps its shape.

## Verification

The guard test in `tests/claude_infra/test_pipeline_rules.py` asserts
the three rule sentences in the collapsed skill text, one assertion
per sentence. A removal fails the suite.
