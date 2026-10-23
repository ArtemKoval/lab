# 0002 - Claude Code is the single harness

- Status: accepted
- Date: 2026-10-23

## Context

The intent-driven template ships OpenCode-native surfaces: .opencode/ agents, .opencode/ skills, .agents/ skills, and opencode.json. Claude Code reads .claude/agents/ and .claude/skills/ only. Keeping both trees makes two sources that drift.

## Decision

Port everything into .claude/ and keep Claude Code as the single harness surface. Carry no OpenCode mirrors. Record provenance in each ported file so future template upgrades stay reviewable.

## Consequences

OpenCode users get none of this setup until someone regenerates surfaces from .claude/. The upstream template stays one pinned commit away for future ports.
