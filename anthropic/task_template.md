ultrathink. Plan Mode. revving. split role sub-agents.


# Orchestrator Task: Feature Implementation

## Activation
```
ultrathink. Plan Mode. revving. split role sub-agents.
```

## Orchestrator Template
Execute the orchestrator workflow defined in:
```
https://github.com/ArtemKoval/lab/anthropic/orchestrator_template.md
```

---

## Main Task

### Feature Specification
```
Specs/{{FEATURE_NAME}}/spec_template.md
```

> **Note**: Replace `{{FEATURE_NAME}}` with the actual feature directory name before execution.

---

## Post-Implementation Documentation

### Console Log Capture
After implementation and validation are complete, append execution logs to the spec file.

**Target File:**
```
Specs/{{FEATURE_NAME}}/spec_template.md
```

**Log Section Format:**
```markdown
---

## Implementation Log

### Execution Summary
- **Date**: {{TIMESTAMP}}
- **Status**: {{SUCCESS|PARTIAL|FAILED}}
- **Files Changed**: {{COUNT}}

### Console Output
\`\`\`
{{PASTE_CONSOLE_LOGS_HERE}}
\`\`\`

### Validation Results
| Judge | Score | Critical Issues |
|-------|-------|-----------------|
| ... | ... | ... |

### Files Modified
- `path/to/file1.cs` - {{description}}
- `path/to/file2.cs` - {{description}}

### Notes
{{Any additional observations, deferred items, or follow-up tasks}}
```

**What to Capture in Console Logs:**
- All file creation/modification operations
- Test execution results
- Build/compilation output
- Validation phase summaries
- Any errors or warnings encountered

---

## Success Criteria

### Implementation Complete When:
- [ ] All requirements from spec_template.md are implemented
- [ ] Code compiles without errors
- [ ] All tests pass

### Documentation Complete When:
- [ ] Console logs appended to spec file
- [ ] Execution summary filled in
- [ ] Files modified list updated
- [ ] Validation results table populated

---

## Execution Checklist

```
[ ] 1. EXPLORE  - Analyze spec_template.md and codebase
[ ] 2. PLAN     - 13-team ensemble generates implementation plans
[ ] 3. PAUSE    - Wait for plan approval
[ ] 4. IMPLEMENT - Write code following the approved plan
[ ] 5. VALIDATE  - 13-judge panel reviews implementation
[ ] 6. FIX       - Apply fixes from validation
[ ] 7. DOCUMENT  - Append console logs to spec file
[ ] 8. FINALIZE  - Verify all success criteria met
```

---

## Quick Reference

| Variable | Replace With |
|----------|--------------|
| `{{FEATURE_NAME}}` | Actual feature directory name |
| `{{TIMESTAMP}}` | ISO 8601 timestamp (e.g., 2025-01-15T14:30:00Z) |
| `{{SUCCESS\|PARTIAL\|FAILED}}` | Final implementation status |
| `{{COUNT}}` | Number of files changed |
| `{{PASTE_CONSOLE_LOGS_HERE}}` | Actual console output |