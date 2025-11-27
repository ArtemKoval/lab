# {{FEATURE_NAME}} Design Spec

## Overview
<!-- Brief description of the feature/component and its purpose -->

## Problem Statement
<!-- What problem does this solve? Why is it needed? -->

## Requirements

### Functional Requirements
<!-- What the system must do -->
- [ ] FR-1: 
- [ ] FR-2: 
- [ ] FR-3: 

### Non-Functional Requirements
<!-- Performance, scalability, security, etc. -->
- [ ] NFR-1: 
- [ ] NFR-2: 

## Scope

### In Scope
<!-- What this spec covers -->
- 

### Out of Scope
<!-- Explicit exclusions to prevent scope creep -->
- 

## Technical Design

### Architecture
<!-- High-level architecture decisions, component relationships -->

### Data Model
<!-- Key data structures, schemas, state management -->

### Interfaces
<!-- APIs, contracts, integration points -->

### Dependencies
<!-- External services, libraries, other components -->
- 

## Timeline

| Phase | Description | Estimate |
|-------|-------------|----------|
| Design | | |
| Implementation | | |
| Testing | | |
| Review | | |

---

## Implementation Reference

### Mandatory Constraints

> **Expandable Framework**: Each mandatory item below can be customized per project. 
> Replace placeholders with project-specific references.

#### Code Quality
- **SSOT Compliance**: Must maintain Single Source of Truth—no duplicated logic or data definitions
- **DRY Principle**: Don't Repeat Yourself—extract shared functionality into reusable components

#### Architecture Patterns
<!-- Configure based on project architecture -->
- **Communication Pattern**: `{{PATTERN}}` 
  - Options: EventBus | Message Queue | Direct Injection | Observer | Mediator
  - Reference: `{{PATH_TO_ARCHITECTURE_DOCS}}`

#### Documentation References
<!-- Point to project-specific guidance documents -->
- **Architecture Guide**: `{{PATH_TO_ARCHITECTURE_GUIDE}}`
- **Domain Guide**: `{{PATH_TO_DOMAIN_GUIDE}}`

#### Research Requirements
- **External Research**: Use web search for best practices, library comparisons, and implementation patterns when facing unfamiliar domains

#### Testing Requirements
<!-- Configure based on project test framework -->
- **Test Framework**: `{{FRAMEWORK}}`
  - Options: xUnit | NUnit | Jest | pytest | JUnit | MSTest | Mocha
- **Required Coverage**:
  - [ ] Unit tests for business logic
  - [ ] Integration tests for external interfaces
  - [ ] Edge case coverage

### Optional Constraints
<!-- Enable/disable based on project needs -->

- [ ] **API Versioning**: Follow semantic versioning for public interfaces
- [ ] **Backwards Compatibility**: Maintain compatibility with `{{VERSION}}`
- [ ] **Performance Baseline**: Must meet `{{METRIC}}` threshold
- [ ] **Security Review**: Requires security sign-off before merge
- [ ] **Documentation**: Public APIs must have XML/JSDoc comments
- [ ] **Feature Flags**: Implement behind `{{FLAG_NAME}}` toggle

---

## Acceptance Criteria

### Definition of Done
- [ ] All functional requirements implemented
- [ ] All tests passing
- [ ] Code review approved
- [ ] Documentation updated
- [ ] No critical/high issues from validation

### Validation Checklist
<!-- Mapped to 13-judge validation panel -->
| Aspect | Criteria | Status |
|--------|----------|--------|
| Correctness | Implements all requirements | ⬜ |
| Performance | Meets performance baselines | ⬜ |
| Security | No vulnerabilities introduced | ⬜ |
| Testability | Adequate test coverage | ⬜ |
| Documentation | APIs and changes documented | ⬜ |

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| | Low/Med/High | Low/Med/High | |

---

## Open Questions
<!-- Unresolved decisions that need clarification -->
- [ ] Q1: 
- [ ] Q2: 

---

## Additional Context
<!-- Links, references, prior art, related specs -->
- 

---

## Implementation Log
<!-- Populated after implementation by orchestrator -->

### Execution Summary
- **Date**: 
- **Status**: 
- **Files Changed**: 

### Console Output
```
<!-- Paste console logs here -->
```

### Validation Results
| Judge | Score | Critical Issues |
|-------|-------|-----------------|
| | | |

### Files Modified
- 

### Notes
-