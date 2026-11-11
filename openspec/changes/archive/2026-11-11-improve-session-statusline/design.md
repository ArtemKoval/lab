# Design: improve-session-statusline

## Context

The session status line renders eight blocks with one space between
neighboring blocks, and the effort block shows the raw harness level
from the payload. The z.ai coding plan maps the harness level to its
own `low`, `high`, and `max` ontology, so the line names a level the
serving path never applies. The render pipeline is one stdlib module
that reads the payload, the transcript, and the console. The change
touches the render stage only.

The C4 view is one component flow inside the status line container,
ASCII format, lightweight rigor. The format follows the archived
design of `add-session-statusline`, and no actor or boundary moves.

```
stdin payload (JSON)
   |
   +-- model.display_name ---------> model block
   +-- effort.level ---> z.ai map --> effort block (n/a when absent)
   |        (unknown level -> raw level)
   +-- rate_limits.*.used_percentage > 5h / wk blocks,
   |        payload first
   |        (absent) ---> console read, 300 s cache,
   |                      stale cache wins, else n/a
   +-- prompt_cache.hit_ratio ------> cache block (percent)
   |        (absent) sums -> cache rate from transcript usage
   +-- transcript_path ------------> in / out blocks
   +-- clock ----------------------> time block
   |
   blocks joined with " | " ------> one line, exit 0
```

- The container boundary stays: payload in, one line out, exit 0 on
  every data fault.
- The z.ai map is one new component: a module-level table with one
  lookup. It reads no model name.
- The console path, the transcript path, and the caches keep their
  behavior. The diagram names them to show the map changes no source
  and no sink.
- Assumption: the payload `effort.level` reports the level the
  harness sends. The gateway applies the mapped level.
- Open question for later probes: whether the gateway reports the
  applied effort anywhere. No probe runs in this change, because the
  docs pin the mapping and a probe spends credits.

## Goals / Non-Goals

Goals:

- The line carries one visible separator between neighboring blocks.
- The effort block names the z.ai effort the coding plan applies.
- The `--json` fields and the line agree on the effort value.

Non-goals:

- No settings change. The `statusLine` command stays as it is.
- No model detection, no transcript effort probe, no console probe.
- No change to the token totals, the cache rate, the limits, or the
  cache files.

## Decisions

### D1. Map always, no model gate

The operator chose the map-always rule. The tool applies the table
to every payload. The tool does not examine the model name.

Alternative rejected: name-gated mapping (map only a `glm-5.3` name).
The operator pins GLM names on every slot. One fixed rule keeps the
render honest without a detection component. The known cost sits in
Risks.

### D2. One module-level table, raw pass-through outside it

The table is a dict constant in `session_statusline.py`. The lookup
is `table.get(level.lower(), level)` on a string level, with any
non-string level passed raw. A falsy level stays `n/a`, as today. An
absent effort stays `n/a` before the map runs.

Alternative rejected: a config file or a registry entry. One
consumer renders one display rule, and a second source of truth
invites drift.

Alternative rejected: `n/a` for unknown levels. The raw token keeps
a new ontology visible, on the fail-open rule of the tool.

### D3. The separator joins a block list

`render` builds the eight labelled blocks it already computes and
joins them with `" | "`. `degraded_line` joins its fields the same
way behind the fault prefix. One join site per line shape.

Alternative rejected: an unchanged degraded line. Two line shapes
invite drift, and the fails-open scenario stays green either way.

### D4. The `--json` effort field carries the mapped value

The fields dict keeps its key set. The `effort` key holds the mapped
value, so the machine view and the line agree.

Alternative rejected: a new `effort_raw` key. The field set is a
contract, and one truth beats two.

### D5. The line length pin stays under 100 for the pinned payload

The separator adds 14 characters over the seven block junctions. The
pinned payload keeps the effort token `high`, because the table maps
`high` to `high`. Its line grows from 77 to 91 characters and stays
under the pin. A payload with a 24 character model name and a mapped
level can reach 106 characters, and the pin binds the pinned payload
only. An unknown raw level carries no length bound. The test keeps
the under-100 pin and adds an exact-line assertion, so the format
has one pinned example.

Alternative rejected: a relaxed bound. The pinned payload is the
realistic case, and the pin still holds.

## Risks / Trade-offs

- [The gateway changes its table] -> The README limits row carries
  the doc date 2026-11-02. A `zai_routing_audit` run verifies the
  served behavior when in doubt.
- [A foreign ontology payload shows the z.ai label] -> The operator
  accepted the trade-off. The proposal and the README record it.
- [The payload effort shape changes] -> Fail-open: a non-string
  level passes raw, an absent effort stays `n/a`, and the line still
  renders.
- [The mapped value hides the requested level] -> The line names the
  applied level. A reader who needs the requested level reads the
  transcript.
- [The identity table rows are equivalent under mutation] -> The
  mutator walks function sites, and the table is data. The
  parametrized row tests hold every row value, so a wrong value dies
  in the suite.

## Migration Plan

None. One tool renders the new format on the next refresh, the
cache files stay compatible, and a revert of the pull request
restores the old format.

## Open Questions

None. The proposal settled the map scope and the unknown level rule.
The design settled the mechanics. No new ADR follows, and the adr
manifest records that outcome.
