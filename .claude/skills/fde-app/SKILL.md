---
name: fde-app
description: Build, test, and package the fde OpenRouter chat desktop app. Use this skill to run the fde app in dev mode, to run its Python or JS test suites and gates, to package installers, or to find the cause of a packaging or smoke-test failure. Gives the commands, the exit codes, and the known problems.
---

# fde app

The `fde/` project is an Electron desktop chat app for OpenRouter with an embedded Python backend. All commands run from `fde/`.

## Dev run

```bash
npm ci              # once per clone
npm run py:setup    # once per clone; creates .venv
npm run dev         # opens the window; predev bundles the renderer first
```

`npm run dev` opens the window and shows the wizard on the first run. The dev user data folder is `~/Library/Application Support/FDE Chat` (Windows: `%APPDATA%\FDE Chat`).

## Tests and gates

```bash
npx vitest run --coverage    # JS gate; thresholds at 100% for src/main, src/preload, renderer logic
npm test                     # the same without the report
.venv/bin/python -m pytest   # Python gate; 100% line and branch coverage enforced
.venv/bin/ruff check backend # complexity gate; every function at most 10
```

Exit codes: vitest and pytest exit 1 on failures or missed thresholds; ruff exits 1 on findings.

The mutation run (mutmut, score at least 95%) runs from an out-of-tree copy: copy `backend/`, `tests/`, and `pyproject.toml` to a temp folder, strip the `--cov*` options from the copy's `addopts` (mutmut's stats run measures mutated code, and the coverage gate would abort it), then run `mutmut run` there with this project's venv.

## Packaging and smoke test

```bash
npm run fetch-python     # downloads the pinned runtime; exit 2 on checksum mismatch
npm run install-pylibs   # installs the hash-locked deps with the embedded interpreter
npm run build:dir        # unpacked app for this OS into dist/
npm run build            # installers for this OS
npm run smoke            # starts the packaged app; exit 0 on ready, 2 on failure
```

`runtime-lock.json` pins the python-build-standalone tag and the sha256 of each target archive. `beforePack` runs the two fetch steps, and `extraResources` copies `python/`, `pylibs/`, and `backend/` into the app resources.

## Known problems

- A packaged app that starts but shows nothing, with empty logs, usually means a module is missing from the asar `files` list. Run the app binary with `ELECTRON_ENABLE_LOGGING=1` or load `Resources/app.asar` with `npx electron` to see the load error. The main process imports `src/renderer/logic/chat-logic.mjs`, so that glob must stay in `files`.
- `npm run dev` and a packaged app share the `FDE Chat` user data folder; delete its `logs/` folder before a smoke run, because the smoke reads only the newest readiness line.
- Two app instances refuse to start by design; a stale Electron process from a killed dev run holds the single-instance lock. Kill it with `pkill -f "FDE Chat"`.
- `python-build-standalone` ships no `pip.exe` on Windows; always call `python.exe -m pip`.
