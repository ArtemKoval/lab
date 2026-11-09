# Proposal: add-tool-admission-rubric

## Why

The lab adds a tool per task, and CLAUDE.md says nothing about the
shape of the next tool. Tool sprawl grows without an admission
question, and composed workflows arrive before their primitives.
Proposal P5 of `reports/2026-11-10-issue-175-rea-analysis.md`
requests the rubric. rea adds a tool only when an analyst question
needs it, shapes tools into six forms, and prefers primitives over
composed workflows.

## What Changes

### The admission rubric in Step 2

The standalone-code step of the feature-pipeline skill gains one rule.
A new tool names the question it answers, and picks one of six shapes:
inspect, search-list, trace, compare, workflow, observe-capture. A
primitive comes before a composed workflow, and each interpretation a
tool produces gets one owner.

## Capabilities

### New Capabilities

None. The rubric lives in the feature-pipeline skill, a harness
surface with no capability spec.

### Modified Capabilities

None. The change declares `skip_specs` and carries no delta.

## Out of scope

- No capability registry for tools. The lab exposes two small MCP
  servers, and the report defers the rea contract registry at rea
  scale.
- No new tool in this change. The rubric governs the next tool.
- No mechanical enforcement. The guard test pins the rule text, and
  the suite fails on a removal.

## Impact

- `.claude/skills/feature-pipeline/SKILL.md`: one rule bullet in
  Step 2, after the remediation rule.
- `tests/claude_infra/test_pipeline_rules.py`: one guard test with one
  assertion per rule sentence.
- No code module, no registry unit, no README change, no spec delta.
