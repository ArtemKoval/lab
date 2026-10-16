# FDE Chat — an OpenRouter desktop client

FDE Chat is a desktop chat app for [OpenRouter](https://openrouter.ai). It looks and feels like the ChatGPT or Claude desktop apps: a sidebar with conversations, streaming markdown replies, and a first-launch wizard that collects your OpenRouter API key and your default model.

The user interface is Electron with a vanilla JS renderer. The OpenRouter work lives in an embedded Python backend: a pinned [python-build-standalone](https://github.com/astral-sh/python-build-standalone) CPython 3.13 tree plus a hash-locked dependency tree, shipped inside the app resources. The Electron main process spawns the backend once and talks line-delimited JSON-RPC over stdio with it.

## Development

```bash
npm ci              # Node dependencies (Electron, electron-builder, vitest, esbuild)
npm run py:setup    # Python dev and gate tools into .venv
npm run vendor      # bundle renderer libraries and the app entry (predev runs it too)
npm run dev         # open the app with the host interpreter on the backend source
```

The dev-mode user data folder is `~/Library/Application Support/FDE Chat` (Windows: `%APPDATA%\FDE Chat`). The backend log lands in `logs/backend.log` there, the main log in `logs/main.log`.

## Tests and gates

```bash
npm test                     # vitest, thresholds at 100% for src/main, src/preload, renderer logic
npm run test:coverage        # the same, with the coverage report
.venv/bin/python -m pytest   # backend suite, 100% line and branch coverage enforced
.venv/bin/ruff check backend # complexity gate: cyclomatic complexity at most 10
```

The mutation run (mutmut at 95% or more) executes from an out-of-tree copy of `backend/`, `tests/`, and `pyproject.toml`, never in place.

## Packaging

```bash
npm run fetch-python      # download the pinned runtime, verify its sha256
npm run install-pylibs    # pip install --target with the embedded interpreter
npm run build:dir         # unpacked app for this OS (fast local check)
npm run build             # installers for this OS
npm run smoke             # start the packaged app and wait for backend readiness
```

`runtime-lock.json` pins the runtime release tag and the sha256 of every target archive; a mismatch fails the build. Tag builds run in GitHub Actions on four jobs: `macos-15` (arm64), `macos-15-intel` (x64), `windows-latest`, and `ubuntu-24.04` (the smoke test runs under `xvfb-run` there).

## Releases

A tag push (`v0.1.0` shape, matching the app version) builds the installers on all four CI jobs and publishes a GitHub release with them attached. Download the installers from the repository's Releases page.

## Install and first run

## Install and first run

The v1 artifacts carry an ad-hoc macOS signature and no Developer ID identity, so the operating system asks for confirmation on the first launch:

- **macOS**: open the dmg, drag the app to Applications, then control-click the app and choose **Open**, or use System Settings → Privacy & Security → **Open Anyway**. The first launch shows a short **Verifying** delay while macOS scans the bundled runtime; this is expected.
- **Windows**: SmartScreen shows **Windows protected your PC**. Click **More info**, then **Run anyway**.
- **Linux**: make the AppImage executable (`chmod +x FDE Chat.AppImage`) and start it. On systems without libfuse2, run it with `--appimage-extract-and-run`.

## Known limits of v1

- No code signing, no notarization: the per-OS first-run steps above stay necessary until certificates exist.
- No auto-update: upgrade by reinstalling. The runtime stays pinned, so future app-only releases stay small.
- One app instance at a time; a second launch focuses the first.
- The API key is stored encrypted through the OS keychain (Electron safeStorage). On Linux without a keyring service the app keeps the key for the session only and asks again at the next launch.
