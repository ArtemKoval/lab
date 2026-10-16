# Design

## Context

The repo is a personal lab of standalone projects. `fde/` is empty. OpenSpec and the setup registry exist. The research for this change (four parallel reviews plus a critic, October 2026) settled the packaging landscape; this design turns it into decisions. The user picked: python-build-standalone runtime, multi-chat with history, vanilla JS renderer.

## Goals / Non-Goals

**Goals:**

- One Electron process tree: main process owns everything privileged, sandboxed renderer shows UI, one Python backend child does all OpenRouter work.
- A protocol between main and backend that is easy to test without a display, a network, or a real API key.
- Package the same code for macOS, Windows, and Linux from one CI tag build.
- Backend code that meets the repo gates: 100% branch coverage, complexity 10 or less per function, mutation score 95% or more.

**Non-Goals:**

- Code signing and notarization (unsigned v1; README documents the first-run steps).
- App auto-update (v1 upgrades by reinstall; runtime pinning keeps most future releases small).
- Multi-instance support; a second app instance is refused with `requestSingleInstanceLock`.
- Import, export, or sync of conversations.

## Decisions

### D1. Transport: NDJSON JSON-RPC 2.0 over stdio

The main process spawns the backend once and speaks line-delimited JSON-RPC 2.0 on stdin and stdout. Stream chunks travel as notifications. All backend logs go to stderr.

- Alternatives: localhost HTTP (needs port discovery, a token, Host header checks, and a DNS rebinding surface), Unix domain socket (platform code on Windows), gRPC (codegen and large binaries for one service).
- Rationale: no ports, no tokens, no network exposure, and the simplest lifecycle. The MCP stdio transport rules are the frame template. A parent-child pipe cannot be reached by other local processes or by web pages.

### D2. Runtime: python-build-standalone, pinned and checksummed

A lock file pins the CPython 3.13 `install_only_stripped` release tag and the sha256 of each platform tarball. A build script downloads the tarball, verifies the checksum, and unpacks it. The script then installs the dependencies with the fetched interpreter itself: `<runtime>/bin/python3 -m pip install --target build/pylibs` on POSIX, `python\python.exe -m pip ...` on Windows, from hash-pinned per-platform requirement files. The runtime ships pip, so no setup-python step exists in CI, and wheel selection pins to CPython 3.13 instead of the host Python. No venv ships (venvs hold absolute paths and do not move). At spawn the main process sets `PYTHONPATH` to `pylibs`, `PYTHONNOUSERSITE=1`, and strips `PYTHONHOME` from the child environment.

- Alternatives: PyInstaller onedir (antivirus reputation on Windows, re-freeze on each code change, slower start), conda embed (three times the size).
- Rationale: no antivirus false-positive class, no recompile of anything when Python code changes, and the escape hatch stays open: if the Python layer shrinks to thin glue, a plain runtime tree is easy to delete.

### D3. Two run modes behind one selector

`app.isPackaged` picks the child command. Packaged: the interpreter of the embedded tree from `process.resourcesPath`, with `pylibs` on the module path. Development: the project virtualenv interpreter on `fde/backend` source. One helper module owns the selection, so no other code branches on run mode.

- Alternative: fetch the embedded runtime in dev too (full parity, slower dev loop and a big download for a first run).
- Rationale: the dev loop stays fast; the packaged smoke test (see the packaging spec) catches parity drift.

### D4. Key storage: safeStorage ciphertext in one config file

The main process encrypts the key with Electron `safeStorage` and writes base64 ciphertext to `userData/config.json` next to the default model. The renderer gets a masked value (last four characters) and a validity flag only. Decryption happens in the main process alone. The key never enters a log line, an error message, or a child argument. Before the first store, the main process asks `safeStorage.isEncryptionAvailable()` and, on Linux, examines the selected storage backend: when encryption is unavailable or the backend is the weak `basic_text` fallback, the app keeps the key for the session only, warns the user, and stores no key and no setup-done mark. A stored ciphertext that no longer decrypts (keychain reset, reinstall of an unsigned bundle) counts as an absent key and returns the user to the wizard.

- Alternatives: plain JSON (rejected: key readable on disk), keytar (extra native module for what safeStorage already gives).
- Rationale: OS keychain-backed encryption with no new dependency.

### D5. History: one JSON file per conversation, atomic writes

`userData/chats/<conversation-id>.json` holds title, model, and messages in order. Writes go to a temp file and rename, so a crash leaves no partial file. `config.json` stays separate from chat data.

- Alternatives: one store file (one corrupt write loses everything), SQLite (native module and query power the UI does not need).
- Rationale: per-chat files make delete equal file removal, keep writes small, and stay debuggable.

### D6. Renderer: vanilla ES modules plus one vendored bundle

The renderer has no framework and no bundler of its own. Two libraries (markdown rendering and HTML sanitizing) come from npm and get bundled once by a small esbuild script into `src/renderer/vendor.js`, which `.gitignore` excludes; `predev` and `prebuild` hooks run the script. The renderer sandbox stays on: `sandbox: true`, `contextIsolation: true`, `nodeIntegration: false`, a strict CSP with no inline scripts, popups denied, and one narrow `contextBridge` API. Links in replies go to the system browser through the main process.

- Alternatives: hand-rolled markdown (an XSS risk), full Vite + React chain (rejected by the user; the UI is thin).
- Rationale: dependencies stay auditable in `package.json`, and the repo needs no second build system beyond one esbuild call.

### D7. Protocol surface: five methods, versioned ready line

Methods: `validate_key`, `list_models`, `chat_start` (returns a stream id), `chat_stop`, `shutdown`. Stream events are notifications named `chat/chunk`, `chat/done`, and `chat/error`, each carrying the stream id. The ready line carries a protocol version, so future main and backend builds can refuse a mismatch before the first request.

- Alternative: one `chat` method per message (no stop or multiplexing control).
- Rationale: the stream id lets the user stop one generation and, later, run two conversations without a second child.

### D8. Backend shape: pure core plus thin stdio shell

The Python package splits into a pure core (OpenRouter client, protocol codec, error mapping; no I/O of its own beyond an injected HTTP client) and a thin stdio shell that reads lines and writes lines. Tests drive the core in-process with `httpx.MockTransport` (no network, no extra mocking package) and drive the codec with byte strings. The mutation run targets the core and the codec.

- Rationale: the repo gates (branch coverage, complexity, mutation) need code that does not need a pipe or a display to test.

### D9. Packaging: electron-builder with a beforePack runtime fetch

`fde/electron-builder.yml` sets the targets: macOS `dmg` plus `zip` for arm64 and x64, Windows `nsis` for x64, Linux `AppImage` for x64. The macOS identity pins to the ad-hoc value with no hardened runtime, so every build machine ships the same signature state. A `beforePack` hook runs the fetch script and the target install, then the config copies `python/`, `pylibs/`, and `backend/` through `extraResources`. The CI matrix runs four jobs: `macos-15` (arm64), `macos-15-intel` (x64), `windows-latest`, `ubuntu-24.04`. Each job uploads its artifacts and runs the launch smoke test on what it built: Linux runs the app under `xvfb-run -a` with the AppImage extract-and-run option, macOS starts the binary inside the bundle directly, and Windows starts the executable of the unpacked build. The smoke test reads the readiness result line that the main process writes to its log file in the user data folder.

- Alternatives: PyInstaller per-arch builds (double the matrix), one universal2 build (no such pbs release, fragile).
- Rationale: the runtime needs no compilation, so each job only downloads and installs; the matrix matches what the platform targets need. Image notes for the future: `macos-14` retired on November 2, 2026, so the arm64 job uses `macos-15`; the `macos-15-intel` image stays available until August 2027, and its retirement forces a decision between dropping Intel macOS and cross-arch work; `ubuntu-22.04` deprecation began in September 2026, so the Linux job uses `ubuntu-24.04`, which also ships `xvfb` for the smoke test.

### D10. JavaScript gates: vitest over main, preload, and renderer logic

Main-process modules (spawn helper, history store, wizard state machine, protocol client) and renderer logic (message list assembly, title derivation) get vitest unit tests. The vitest config sets global coverage thresholds at 100 for lines and branches over named globs (`src/main/**`, `src/preload/**`, and the tested renderer modules), with the exclusion list in the same config, so the JS gate runs as a fixed check. Electron APIs arrive through injected stubs, so no test starts real Electron.

- Alternative: no JS tests because the Python side carries the logic.
- Rationale: the repo gate policy covers every changed function; the main process holds security-critical code (key handling, spawn, kill) that must not go untested.

## Risks / Trade-offs

- [First launch on macOS scans hundreds of Mach-O files and adds a Verifying delay] → keep the stripped runtime, trim Tcl/Tk and test tooling from the packed tree, and document the delay in the README.
- [Dev and packaged behavior drift apart] → the packaged smoke test runs on every tag build; the protocol version lives in one shared constant.
- [A third-party library prints to stdout and corrupts the protocol] → the backend logger binds every library logger to stderr; a contract test asserts stdout carries only protocol lines.
- [Windows quit leaves the child alive] → quit kills through the process tree (`taskkill /T /F` path), and a test drives the kill helper with a stub child.
- [x64 macOS needs binary wheels that arm64 runners cannot install] → v1 pins pure-Python dependencies only (HTTP client, markdown toolchain); if a binary wheel becomes necessary, the matrix already builds on `macos-15-intel`.
- [Mutation scoring the stdio shell is expensive and awkward] → the shell stays thin; the mutation scope names the core package, and shell survivors become explicit follow-ups.
- [An app with no Developer ID signature erodes user trust in the field] → the ad-hoc signature keeps macOS arm64 launches deterministic, the README documents per-OS first-run steps, and signing is the first follow-up when certificates exist.

## Migration Plan

New project; nothing to migrate. Rollback is deleting `fde/` and the specs after archive.

## Open Questions

None that block the specs or the task breakdown. The signing certificate question is a documented non-goal, not an unknown.
