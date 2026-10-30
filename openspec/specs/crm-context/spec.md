# crm-context Specification

## Purpose

A stateless MCP server serves the pack's governed files, the case agent
reaches them through context tools whose steps carry their sources, its
tools route direct or through a gateway, and an optional memory holds
what the agent has seen.

## Requirements

### Requirement: The context server
A stateless MCP server SHALL serve the pack's governed files. They are the documents, the plans, the case rules, the glossary, the data dictionary, and the reference data. Each answer SHALL carry its sources: the system, the owner, and the reviewed mark.

#### Scenario: A lookup carries sources
- **GIVEN** the context server running
- **WHEN** the agent asks for one governed file
- **THEN** the answer carries the content and its sources

#### Scenario: The server is stateless
- **GIVEN** two lookups in sequence
- **WHEN** the second arrives on a new connection
- **THEN** the answer is the same as on a shared connection

### Requirement: Context tools on the case agent
The case agent SHALL reach the governed files through context tools, and each context step on a case SHALL record its sources.

#### Scenario: A context step carries sources
- **GIVEN** a case agent reading the plans
- **WHEN** the step lands on the case
- **THEN** the step carries the sources of the answer

### Requirement: Tool routing
The agent's tools SHALL route direct to the backend and the context server by default. With `CRM_GATEWAY_URL` set, they route through the gateway, with the same tool names on both routes.

#### Scenario: The gateway route serves the same tools
- **GIVEN** `CRM_GATEWAY_URL` set to a gateway stand-in
- **WHEN** the case agent works a case
- **THEN** the tools answer through the gateway with the same names

### Requirement: Memory
The agent SHALL carry a memory for case work at `CRM_MEMORY_ID`, and a run without one SHALL work with no memory calls.

#### Scenario: A memory hit lands on the case
- **GIVEN** a memory stand-in with saved events
- **WHEN** the agent works a case
- **THEN** the search lands on the case as a step
