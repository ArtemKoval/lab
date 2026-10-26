---
name: writing-skills
description: Use when creating a new skill, editing an existing skill, running a baseline or a pressure scenario for a skill, choosing a guidance form for a failure, writing a rationalization table, running a micro-test of wording, or verifying a skill before release.
metadata:
  ported:
    from: obra/superpowers
    commit: 2ce8aa15d05bd57213e6f746f953aafb7ded7a8b
    license: MIT
---

# Writing Skills

## Overview

Create a skill when a technique was not obvious, when you will reference
it again, and when the pattern reaches past one project. Do not create
one for a one-off solution, for a practice that other documents already
cover, or for a mechanical constraint that a regex or a validation rule
enforces.

You write a skill with test-driven development. The product is a document that records a process, not code.

The cycle:

1. Run a pressure scenario without the skill.
2. Record the baseline behavior and the exact rationalizations.
3. Write the minimum skill that answers those recorded rationalizations.
4. Run the scenario again with the skill.
5. Close each new loophole with an explicit counter.
6. Re-run the scenario until no new rationalization appears.

Core principle: if you did not watch an agent fail without the skill, you do not know whether the skill teaches the correct behavior.

Required background: read the test-driven-development skill at `.claude/skills/test-driven-development/` before you use this skill. That skill gives the red-green-refactor cycle. This skill applies that cycle to documents.

## Pressure Scenarios in This Repository

Run every pressure scenario through the Agent tool.

- Use the `general-purpose` agent for a fresh-context sample. The agent starts without this conversation.
- Use the `adversarial-reviewer` agent for a hostile read of a draft skill.
- Combine pressures in a scenario for a discipline skill: time pressure, sunk cost, authority pressure, and exhaustion.

## What a Skill Is

A skill is a reference that records a proven technique, a pattern, or a tool. It helps a future agent find and apply a method that works.

- A skill is: a reusable technique, a mental model, a tool guide, a reference.
- A skill is not: a story about one problem that you solved once.

## Map of Test-Driven Development to Skills

| Item in test-driven development | Work on a skill |
| --- | --- |
| Test case | A pressure scenario in the Agent tool |
| Failing test (red) | The agent breaks the rule without the skill |
| Passing test (green) | The agent obeys the skill |
| Refactor | Close each new loophole, then re-run the scenario |
| Minimal code | Write only guidance that answers the recorded rationalizations |

## The Iron Law

```
NO SKILL WITHOUT A FAILING TEST FIRST
```

This law applies to new skills and to edits of a current skill.

- Did you write the skill before a test? Delete it. Start again.
- Did you edit a skill without a test? That is the same violation.

There are no exceptions. Not for a small addition. Not for one more section. Not for a text-only edit. Do not keep an untested change as a draft. Delete means delete.

## Red: Record the Baseline

1. Write the pressure scenario. Use three or more combined pressures for a discipline skill.
2. Run the scenario through the Agent tool without the skill.
3. Record the choices that the agent made.
4. Record the rationalizations that the agent used, with the exact words.
5. Record the pressure that triggered each violation.

This step is "watch the test fail". You must see the natural behavior before you write the skill.

## Green: Write the Minimal Skill

1. Write only guidance that answers the recorded rationalizations. Do not add content for hypothetical cases.
2. Run the same scenarios with the skill.
3. Make sure that the agent now obeys the skill.

## Refactor: Close the Loopholes

When the agent finds a new rationalization, add an explicit counter. Re-run the scenario until no new rationalization appears.

## Skill Types and Their Tests

| Skill type | Example | The test | The skill passes when |
| --- | --- | --- | --- |
| Discipline: a rule under pressure | `test-driven-development` | Questions on paper. Pressure scenarios. Then combined pressures. | The agent obeys the rule at maximum pressure |
| Technique: a method with steps | a condition-based wait before a UI interaction | An application scenario. A variation scenario. A scenario that lacks information. | The agent applies the method to a new scenario |
| Pattern: a mental model | the flatten-with-flags pattern | A recognition scenario. An application scenario. A counter-example. | The agent knows when to use the pattern and when not |
| Reference: documents | a command guide | A retrieval scenario. An application scenario. A gap test of common cases. | The agent finds the information and uses it correctly |

## Match the Form to the Failure

Classify the baseline failure before you write guidance. The form that fixes one failure type can cause another type.

| Baseline failure | Correct form | Wrong form |
| --- | --- | --- |
| The agent breaks a rule under pressure and knows better | A prohibition, plus a rationalization table and a red-flags list | Soft guidance: "prefer X", "consider X" |
| The agent obeys, but the output has the wrong shape | A positive recipe: state the parts of the output and their order | A list of prohibitions |
| The agent omits a required element | A required field or slot in the template | A prose reminder near the template |
| The behavior must depend on a condition | A conditional on an observable predicate | An unconditional rule with exemptions |

A prohibition backfires when the problem is output shape. When the task gives the agent another incentive, the agent negotiates with "do not do X". In wording tests on dispatch-prompt guidance, the prohibition arm produced more of the unwanted content than the recipe arm. It also did worse than the control without guidance. A recipe leaves nothing to negotiate: the output matches the stated shape or it does not.

Rules for the form that you pick:

- Do not write a nuance clause. "Do not do X unless it matters" reopens the negotiation. Write a real exception as its own conditional on an observable predicate.
- An exemption clause does not scope. "This limit does not apply to code blocks" still suppresses code blocks. If a part must stay exempt, change the structure so the rule cannot reach it.

For a discipline failure, build two counters: a rationalization table that pairs each recorded excuse with the reality, and a red-flags list that names the sentences that signal a violation.

## Micro-Tests of Wording

A full pressure scenario is slow. Use a micro-test to examine the wording first.

1. Take one fresh-context sample per call. Use a raw API call, or one single-shot run of the `general-purpose` agent. The system prompt holds the realistic context: the full skill or template, not the guidance alone. The user message gives a task that tempts the failure.
2. Always run a no-guidance control. If the control does not show the failure, stop. There is nothing to fix.
3. Run five or more samples for each variant. One sample lies.
4. Read every flagged match yourself. Template echoes and quoted examples look like hits. Automated counts alone overstate failure and success.
5. Treat variance as a metric. When the wording binds, the samples converge on one shape. Five different interpretations across five samples mean the wording does not bind. Tighten the form before you add words.

A micro-test examines wording. It does not replace pressure scenarios for discipline skills.

## Common Excuses

| Excuse | Reality |
| --- | --- |
| "The skill is obviously clear." | Clear to you is not clear to another agent. Run the test. |
| "It is only a reference." | A reference can have gaps. Run a retrieval test. |
| "A test is too much." | An untested skill has problems. Always. |
| "I will run the test after problems appear." | The problem is an agent that cannot use the skill. Run the test before release. |
| "A test takes too much work." | A test takes less work than repair after a bad release. |
| "I am sure the skill is good." | Overconfidence produces problems. Run the test. |
| "A review on paper is enough." | An agent that reads the rule can still break the rule. Run an application scenario. |
| "There is no time for a test." | A bad release costs more time than the test. |

All these excuses mean one thing: run the test before you release the skill.

## Anti-Patterns

### A story in place of an example

"In session 2025-10-03, we found that the empty projectDir caused the failure."
Why it fails: the story is too specific. Another agent cannot reuse it.

### Examples in many languages

example-js.js, example-py.py, example-go.go
Why it fails: each example gets less care, and every example adds work to maintain. Give one excellent example in the most relevant language.

### Code in a flowchart

A flowchart node holds a line of code.
Why it fails: the reader cannot copy the code, and the diagram is difficult to read.

### Generic labels

helper1, helper2, step3, pattern4
Why it fails: a label must say what the item is.

## Conventions in This Repository

- Write the prose of a skill in ASD-STE100 Simplified Technical English. `CLAUDE.md` gives the rules.
- Start the description with "Use when". List the triggers only. Never summarize the workflow. An agent that reads a summary obeys the summary instead of the skill.
- Make the name equal the directory name. Use only letters, numbers, and hyphens in the name.
- Put personal skills in `~/.claude/skills/` on Claude Code. Put project skills in `.claude/skills/`.

## Checklist

Track each item in this checklist as a separate task.

### Red

- [ ] Write pressure scenarios with three or more combined pressures for a discipline skill.
- [ ] Run the scenarios without the skill. Record the baseline behavior with the exact words.
- [ ] Find the patterns in the rationalizations and the failures.

### Green

- [ ] Use only letters, numbers, and hyphens in the name. Make the name equal the directory name.
- [ ] Write YAML frontmatter with the `name` and `description` fields. Keep the description at or below 1024 characters.
- [ ] Start the description with "Use when". Give the specific triggers.
- [ ] Put search terms in the body: errors, symptoms, tools.
- [ ] Give a clear overview with the core principle.
- [ ] Address only the recorded baseline failures.
- [ ] Match the guidance form to the failure type.
- [ ] For guidance that shapes an output, run a micro-test against a no-guidance control. Use five or more samples per variant. Read every flagged match yourself.
- [ ] Keep one excellent example. Do not write examples in several languages.
- [ ] Run the scenarios with the skill. Make sure that the agents obey.

### Refactor

- [ ] Find each new rationalization from the tests.
- [ ] Add an explicit counter in a discipline skill for each rationalization.
- [ ] Build the rationalization table from all test iterations.
- [ ] Write the red-flags list.
- [ ] Re-run the tests until no new rationalization appears.

### Quality

- [ ] Add a small flowchart only if the decision is not obvious.
- [ ] Add a quick-reference table.
- [ ] Add a section about common mistakes.
- [ ] Write no narrative stories.
- [ ] Add supporting files only for tools or heavy reference.

### Delivery

- [ ] Complete one skill at a time. Do not batch untested skills.
- [ ] Send the skill through the `feature-pipeline` skill. That pipeline owns the branch, the review, and the merge.

## How Agents Find a Skill

An agent searches the skill descriptions, opens the skill with the matching triggers, and scans the overview. The agent then reads the quick-reference table. It loads the example only when it starts the implementation. Put search terms near the start of the description and the overview.
