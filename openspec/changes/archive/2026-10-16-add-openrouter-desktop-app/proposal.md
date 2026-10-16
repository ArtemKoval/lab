# Proposal

## Why

The lab has no desktop client for LLM chat. A local app that talks to OpenRouter gives the user a private ChatGPT-style client with their own key, and it establishes the Electron plus embedded Python packaging pattern for future lab projects.

## What Changes

- Add the `fde/` project: an Electron desktop app with a vanilla JS renderer and an embedded Python backend.
- The backend is a Python package that calls the OpenRouter API. The app ships it with a pinned python-build-standalone CPython 3.13 runtime tree and a `pip --target` dependency tree in electron-builder `extraResources`.
- The Electron main process spawns the backend once and talks line-delimited JSON-RPC over stdio with it. Backend logs go to stderr, and the main process writes them to a file in the user data folder.
- A first-launch wizard asks for the OpenRouter API key and validates it with a real API call. The app stores the key encrypted with Electron `safeStorage`. The next step lists the models from `GET /api/v1/models`, with `any` (the auto router) as the default choice.
- The chat window supports multiple conversations in a sidebar. Responses stream token by token and render as markdown. The app persists each conversation as a JSON file in the user data folder.
- electron-builder produces installers with no Developer ID signature: macOS dmg and zip for arm64 and x64 (ad-hoc signature), Windows NSIS for x64, Linux AppImage for x64. The README documents the Gatekeeper and SmartScreen steps for the first launch.
- New setup registry units give a clean clone the Node dependencies and the Python dev and gate tools.
- A GitHub Actions workflow builds the installers on all three operating systems.

## Capabilities

### New Capabilities

- `fde/backend-service`: The lifecycle of the Python backend child process and its line-delimited JSON-RPC protocol over stdio. Covers spawn, readiness handshake, request routing, crash restart, clean shutdown, and log capture.
- `fde/openrouter-client`: The Python integration with the OpenRouter API. Covers key validation, model listing, streaming chat completions over SSE, and error mapping to JSON-RPC errors.
- `fde/onboarding`: The first-launch wizard. Covers the key step, the model step with the default `any`, validation feedback, and the rule that the wizard runs once and stays available from settings.
- `fde/chat`: The chat window. Covers conversation create, rename, delete, and switching in the sidebar, streaming message exchange with markdown rendering, and JSON persistence of history in the user data folder.
- `fde/packaging`: The distributable builds. Covers the per-OS targets, the embedded runtime present in each artifact, and a launch smoke test of each packaged app.

### Modified Capabilities

None. The existing `llm-ops-eval/*` specs are unrelated.

## Impact

- New code under `fde/`: `src/main/`, `src/preload/`, `src/renderer/`, `backend/` (Python package), `scripts/` (runtime fetch and build helpers).
- New npm dev dependencies in `fde/`: `electron`, `electron-builder`, `vitest`.
- New Python dev dependencies for `fde/`: `httpx`, `pytest`, `pytest-cov`, `ruff`, `mutmut`.
- `tools/project_setup/registry.json` gains units for the Node dependencies and the Python dev and gate tools; `.claude/skills/project-setup/SKILL.md` follows.
- New `.github/workflows/` job matrix that builds the three platforms.
- New `.claude/skills/fde-app/` skill that documents the dev and build commands.
- New specs under `openspec/specs/fde/` after archive.
- Out of scope for v1: code signing certificates, app auto-update, multi-instance support, and import or export of conversations.
