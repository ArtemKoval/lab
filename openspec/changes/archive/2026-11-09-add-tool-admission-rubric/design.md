# Design: add-tool-admission-rubric

## Plan review

The review kept the report proposal as the plan. ASIT: Unification.
The Step 2 rule list exists, and the rubric extends it. No new
component enters the repository.

Alternatives the review rejected:

- A capability registry for tools. The report defers the rea registry
  to rea scale, and the lab's two MCP servers carry no schema-size
  pain.
- A hook that blocks a tool addition without a stated question. The
  rule governs the pipeline author, and the guard test holds the
  text.
- Six mandatory shape names in CLAUDE.md. The shapes belong beside the
  tool contract in the pipeline step, and CLAUDE.md stays the source
  for conventions, not for tool design.

## The rule text

The rule lands in Step 2 after the remediation rule:

- A new tool names the question it answers, and picks one of six
  shapes: inspect, search-list, trace, compare, workflow,
  observe-capture. A primitive comes before a composed workflow, and
  each interpretation a tool produces gets one owner.

## Edge cases

- A tool that spans two shapes names its primary shape and says why
  the second exists. The rubric asks for the choice, not for a
  perfect fit.
- A one-off script that no one reads again stays out of version
  control under the existing working rule, and the rubric does not
  apply to it.
- The rule does not constrain the remediation rule or the exit-code
  contract. The bullets keep their own subjects.

## Verification

`tests/claude_infra/test_pipeline_rules.py` gains one guard test with
one assertion per rule sentence, on the collapsed skill text. A
removal fails the suite.
