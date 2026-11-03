## MODIFIED Requirements

### Requirement: The harness wires the charter hook
The harness SHALL carry a `hooks` object in `.claude/settings.json` with a `SessionStart` group whose matcher is `startup|clear|compact` and whose command runs `.claude/hooks/harness-charter.sh`. The hook entry SHALL set `timeout` to a positive value and SHALL NOT set `async` to true. The sources `resume` and `fork` SHALL stay unmatched, because those sessions replay context that already includes the charter.

#### Scenario: The settings wire the hook
- **WHEN** a reader opens `.claude/settings.json`
- **THEN** a `hooks.SessionStart` group matches `startup|clear|compact`
- **AND** the hook entry names the script path, keeps `async` false or absent, and sets `timeout`
- **AND** the key `outputStyle` is unchanged
- **AND** the keys `enabledMcpjsonServers` and `permissions` hold the zai-routing-audit entries and the dspy-gate entries

### Requirement: The harness wires the spec STE hook
The harness SHALL carry a `PreToolUse` group in the `hooks` object of `.claude/settings.json`. The group SHALL match the `Write` and `Edit` tools and SHALL run `.claude/hooks/spec-ste-gate.sh`. The hook entry SHALL set `timeout` to a positive value and SHALL NOT set `async` to true. The key `outputStyle` SHALL stay unchanged. The keys `enabledMcpjsonServers` and `permissions` SHALL hold the zai-routing-audit entries and the dspy-gate entries.

#### Scenario: The settings wire the STE hook
- **WHEN** a reader opens `.claude/settings.json`
- **THEN** a `hooks.PreToolUse` group matches `Write|Edit`, names the script path, sets `timeout`, and keeps `async` false or absent
- **AND** the key `outputStyle` stays unchanged
- **AND** the keys `enabledMcpjsonServers` and `permissions` hold the zai-routing-audit entries and the dspy-gate entries

## ADDED Requirements

### Requirement: The change template carries the gate artifacts
The intent-driven schema SHALL list `gates.yaml` and `rubrics/` as change artifacts. The schema directory SHALL carry a `gates.yaml` template and a rubric template. The proposal and specs instructions SHALL name the two artifacts.

#### Scenario: The schema lists the gate artifacts
- **WHEN** a reader opens `openspec/schemas/intent-driven/schema.yaml`
- **THEN** the artifact list carries `gates.yaml` and `rubrics/`
- **AND** the templates directory carries the `gates.yaml` template

### Requirement: The harness wires the protect hook
The harness SHALL carry a `PreToolUse` group that runs `.claude/hooks/spec-gates-protect.sh` for the `Write` and `Edit` tools. The protect hook SHALL deny a write to a GENERATED path with a decision JSON. The hook entry SHALL set `timeout` to a positive value and SHALL NOT set `async` to true.

#### Scenario: The settings wire the protect hook
- **WHEN** a reader opens `.claude/settings.json`
- **THEN** a `hooks.PreToolUse` group runs `.claude/hooks/spec-gates-protect.sh` with a positive `timeout` and no `async` true

#### Scenario: The protect hook denies a generated path
- **WHEN** the protect hook receives a Write event for a GENERATED path
- **THEN** the hook prints a deny decision JSON and exits 0 with the deny decision recorded

### Requirement: The harness wires the bridge hook
The harness SHALL carry a `PostToolUse` group that runs `.claude/hooks/spec-gates-bridge.sh` for the `Write` and `Edit` tools. The bridge hook SHALL run the bridge verifier on an edit under `openspec/changes/**/specs/**`. The hook entry SHALL set `timeout` to a positive value and SHALL NOT set `async` to true.

#### Scenario: The bridge hook verifies a spec edit
- **WHEN** the bridge hook receives an Edit event for a file under `openspec/changes/<id>/specs/`
- **THEN** the hook runs the bridge verifier for that change and reports the result as context

### Requirement: The feature-pipeline skill carries the gate steps
The `feature-pipeline` skill SHALL name the dspy-gate tool. The skill SHALL carry the Gate 0 lint rule in the proposal flow. The skill SHALL carry the regeneration rule after a spec edit. The skill SHALL carry Gate 1 and Gate 3 in the test and gates step. The skill SHALL carry Gate 2 for a module with impl optimized. The skill SHALL carry Gate 4 in the archive step and Gate 5 on a model pin change. The skill SHALL carry the conformance matrix in the review request step.

#### Scenario: A reader finds the gate steps
- **WHEN** a reader scans the `feature-pipeline` skill
- **THEN** the text names all six gates with their step placement and the regeneration rule

### Requirement: The gate-status MCP server registers in the harness
The file `.mcp.json` SHALL carry a `dspy-gate` server entry that runs the tool venv interpreter on the MCP wrapper module. The `enabledMcpjsonServers` key SHALL name `dspy-gate`. The `permissions.allow` list SHALL carry the `mcp__dspy-gate` rule.

#### Scenario: The registration resolves
- **WHEN** a reader opens `.mcp.json` and `.claude/settings.json`
- **THEN** the server entry, the enabled server name, and the permission rule all name dspy-gate
