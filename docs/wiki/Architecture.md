# Architecture

The architecture of the crm engine, in the C4 style. The diagrams use plain
Mermaid, so they render on GitHub and in any Markdown viewer. Read them in
order: who uses the system, what runs, what lives inside the backend, and
how one case flows.

## Pages

- [C4 context](C4-Context.md) — the people and the external systems.
- [C4 containers](C4-Containers.md) — the runnable units and the stores.
- [C4 components](C4-Components.md) — the inside of the backend.
- [Case flow](Case-Flow.md) — one case, from the queue to the pay-out.
- [Deployment](Deployment.md) — the laptop route, the container, and AWS.
- [Screenshots](Screenshots.md) — the flow, captured end to end.

The source of truth for the behavior sits in
[openspec/specs/](../../openspec/specs/), and the decisions sit in
[adr/](../../adr/).
