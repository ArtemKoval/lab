# 0007 - CRM engine with domain packs

- Status: proposed
- Date: 2026-10-29

## Context

The lab takes on the UnderCover project, a working operations backoffice with an agent, from `github.com/ed-donner/undercover`. The project mixes a reusable engine with one insurance domain. Queue, decisions, sign-off, and payment share code and text with claims, payouts, and policy wording. The goal is a CRM engine that a skill can onboard to a new domain from a free-form description. The new domain carries its own rules, roles, policies, and processes. The engine must run in a devcontainer, and its AWS parts must run against a local emulator first. Three independent design attempts and a synthesis chose the seam.

## Decision

Adopt a standalone project at `crm/` that ports the upstream milestones in order. The engine is `crm/` without `crm/domains/`. Each domain is one pack at `crm/domains/<name>/` with a manifest, policy documents, seed data, agent instructions, rules, and evals. The engine reads the active pack named by `CRM_DOMAIN` through one loader, and no engine module names a pack. Deterministic decision rules plug in as a pure Python module per pack, not a data language. Engine code, tables, routes, tools, and dashboard text carry only engine nouns: case, contract, award, worker, decision. A pack keeps its own wording in content and labels, and a root-suite guard fails on a domain noun in engine code. New engine vocabulary beyond these nouns needs a superseding record. Rejected options:

- Port the insurance wording through the engine and abstract later. The final rewrite would touch every file twice.
- One merged `crm/engine/` package. The upstream import graph and the deploy targets split the backend and the agent, and the merge would rewrite every import for no behavior.
- A per-pack adapter layer. The pack files use engine schemas, and the manifest carries display labels, so the translation layer does nothing.
- A data language for rules. The upstream rules are small typed code, and a language adds a parser, tests, and docs before three domains show a repeated shape.

## Consequences

The upstream milestones land as mechanical diffs behind the seam, and the port order follows the upstream branch order. A new domain is a pack plus a validation and smoke run, with no engine change. The pack content sits outside the spec gate scope and keeps upstream prose as vendored text. The local auth and checkpoint choices land with the changes that port them, and this record owns only the seam.
