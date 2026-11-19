# C4 containers

The runnable units of the engine, and where each one lives.

```mermaid
flowchart LR
    spa["Dashboard<br/>React SPA on Vite<br/>:5173"]
    backend["Backend<br/>FastAPI<br/>:8000"]
    agent["Agent service<br/>LangGraph<br/>:8080"]
    copilot["Copilot<br/>:8081"]
    context["Context server<br/>MCP<br/>:8006"]
    auth["Dev auth service<br/>:8004"]
    db[("SQLite<br/>crm.db")]
    pack[("Domain pack<br/>manifest, policy, seed")]

    worker(["Worker"]) --> spa
    spa -->|"REST"| backend
    backend -->|"cases and steps"| agent
    backend -->|"questions"| copilot
    agent -->|"policy and facts"| context
    backend -->|"JWKS"| auth
    backend -->|"queue and decisions"| db
    backend -->|"pack files"| pack
    agent -->|"pack files"| pack
    context -->|"pack files"| pack
```

## Notes

- **Runnable units.** Five services and one file-backed store; `npm run dev`
  starts all five, and the e2e suite starts its own set on other ports.
- **The pack is data.** `CRM_DOMAIN` names it, and three services read it
  through one loader; no pack name appears in engine code.
- **Open question.** The runtime route (`CRM_AGENT_RUNTIME`) swaps the agent
  service for an AgentCore invoke; the wiring gate proves it against floci.
