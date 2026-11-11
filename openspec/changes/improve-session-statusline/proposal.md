# Proposal: improve-session-statusline

## Why

Issue 206 tracked the change that added the session status line.
Issue 210
(https://github.com/ArtemKoval/lab/issues/210) asks for two changes
to it. The first ask is a visible separator between the blocks of
the line. The line carries eight blocks with one space between
neighboring blocks, and the operator wants clear block boundaries.

The second ask is an effort field that shows the effort of the
serving path. The field today shows the raw harness level from the
payload. The harness reports levels in the Anthropic ontology. The
coding plan of z.ai applies its own ontology. This session runs
glm-5.3-flash with harness effort `xhigh`, and the line shows
`effort xhigh`. The z.ai coding plan maps that request to the effort
`max`. The line names a level that the serving path never applies.

The z.ai docs pin the mapping, coding plan section, page dated
2026-11-02. The docs sentence is verbatim:

```
"For GLM-5.3 and GLM-5.3-FLASH, `none`, `minimal`, and `low` are
mapped to `low`; `medium`, `high` are mapped to `high`; `xhigh` and
`max` are mapped to `max`."
-- docs.z.ai/guides/capabilities/thinking, 2026-11-02
```

## What Changes

- The line joins its blocks with the ` | ` separator. The issue
  names the pipe character. The degraded line gains the same
  separator.
- The tool maps the payload effort level through the coding plan
  table of z.ai before the render:

  ```
  none     -> low
  minimal  -> low
  low      -> low
  medium   -> high
  high     -> high
  xhigh    -> max
  max      -> max
  ```

- The operator chose the map-always rule. The tool applies the table
  to every payload. The tool does not examine the model name. This
  decision settles the detection ask of the issue in favor of one
  fixed table.
- An unknown level stays raw. An absent effort keeps the `n/a`
  render.
- The `--json` output keeps its field set. The `effort` field
  carries the mapped value, so the machine view and the line agree.
  No new field enters.
- The operator accepts one trade-off. A payload from a gateway with
  a native Anthropic ontology shows the z.ai label. Example:
  `minimal` renders `low` on an Anthropic-backed session.
- The mapping changes the render only. The tool rewrites no payload
  and sends no request.

Breaking judgment: the change carries no **BREAKING** marker. A
human reads the line, and no program parses the line text. The
`--json` field set stays the same. The effort value changes from the
raw level to the mapped level. That is a visible value change, not a
contract break.

The suite pins the line under 100 characters in the complete payload
test of `tests/session_statusline/test_session_statusline.py`. The
separator adds 14 characters over seven junctions. The pinned line
grows to 91 characters and stays under the pin. The implementation
pins the exact line in the test.

## Capabilities

### New Capabilities

None. The change modifies the existing `session-statusline`
capability only.

### Modified Capabilities

- `session-statusline`: the requirement `The status line renders the
  session summary` changes. The line format gains the separator. The
  effort field shows the mapped coding plan effort. The delta
  restates the three scenarios of this requirement with the mapped
  effort. It adds scenarios for three table rows, an unknown level, a
  mixed-case level, the map without a model, the JSON field, the
  separator shape, and the degraded separator. The requirement
  `The tool fails open` also changes, because the degraded line
  gains the separator. The other four requirements keep their
  behavior.

## Impact

- `tools/session_statusline/session_statusline.py`: the render and
  the degraded render gain the separator. One small mapping helper
  joins the field helpers.
- `tests/session_statusline/test_session_statusline.py`: new cases
  for the table rows, the unknown and mixed-case levels, and the
  separators. The under-100 pin stays, and the test pins the exact
  line.
- `tools/session_statusline/README.md`: new line example, mapping
  table, and a limits row with the doc date, because a remote
  gateway can change its table.
- `CLAUDE.md`: the `tools/session_statusline` entry says the line
  carries the z.ai-mapped effort.
- No `.claude/settings.json` change. The `statusLine` command and
  the wiring stay as they are, so the diff needs no
  `gate-integrity: acknowledged` line.
- No new unit in `tools/project_setup/registry.json`. The
  `session-statusline` unit exists.
- No dspy-gate `gates.yaml` and no rubrics. No harness registry
  declares this capability.
- No new dependency. The tool stays standard library only.
