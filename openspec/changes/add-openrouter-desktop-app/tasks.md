# Tasks

## 1. Scaffold and tooling gates

- [x] 1.1 Create the `fde/` layout (`src/main/`, `src/preload/`, `src/renderer/`, `backend/`, `scripts/`, `tests/`), `package.json` with `electron`, `electron-builder`, `vitest`, `esbuild`, `marked`, `dompurify` as dev or vendored dependencies, and `.gitignore` entries for `node_modules/`, `build/`, `dist/`, `src/renderer/vendor.js`. Verify `npm ci --prefix fde` succeeds.
- [x] 1.2 Add `backend/pyproject.toml` with ruff `C901` at `max-complexity = 10`, plus `backend/requirements-dev.txt` (`pytest`, `pytest-cov`, `ruff`, `mutmut`, `httpx`) and a dev venv bootstrap script. Verify `fde/.venv/bin/python -m pytest --version` and `ruff --version` run.
- [x] 1.3 Add `vitest.config.mjs` with global coverage thresholds at 100 lines and branches over `src/main/**`, `src/preload/**`, and the tested renderer globs. Verify `npx vitest run --coverage` loads the config and enforces the thresholds.
- [x] 1.4 Add `scripts/build-vendor.mjs` (esbuild bundles `marked` and `dompurify` into `src/renderer/vendor.js`) and wire `predev` and `prebuild` hooks. Verify the script writes `vendor.js`.
- [x] 1.5 Register setup units `fde-node-deps` and `fde-python-dev` in `tools/project_setup/registry.json` with check and install commands, and extend `.claude/skills/project-setup/SKILL.md` if its flow needs them. Verify `python -m pytest tests/project_setup` passes with the new units. (The repo has no root pytest suite; verification ran the registry JSON parse and both new check commands, each exit 0.)

## 2. Backend pure core

- [x] 2.1 Implement the OpenRouter client with an injected httpx client: `validate_key`, `list_models`, the four error kinds, 30-second timeouts, bearer header, base URL override. Cover with unit tests that use `httpx.MockTransport` (valid key, 401, 500, 429, connection failure, timeout, key-free log and error message). Verify `pytest tests/backend` passes with 100% branch coverage of the new code.
- [x] 2.2 Implement chat streaming: SSE parse, ordered chunk events, joined final text, stream idle timeout of 30 seconds, stop cancellation with a final stop notification. Cover with unit tests on recorded chunk sequences, including the end marker, a stall, and a stop. Verify the tests pass.
- [x] 2.3 Implement the JSON-RPC line codec: encode and decode of requests, responses, and notifications. Cover with unit tests for split lines, malformed lines, and id matching. Verify the tests pass.
- [x] 2.4 Run ruff `C901` on the backend and raise the pytest `fail_under` to the reached total. Verify both commands pass and report the numbers.

## 3. Backend stdio shell

- [x] 3.1 Implement the stdio shell: read lines, dispatch the five methods, flush after each write, route all logs to stderr, exit within 5 seconds when stdin closes. Cover with tests that drive the shell with byte streams, plus one local test that spawns the real interpreter. Verify the tests pass.
- [x] 3.2 Implement the ready line with the protocol version and the interpreter path, and the `chat_stop` path with the final notification. Cover with shell tests. Verify the tests pass.
- [x] 3.3 Run mutmut on the backend package from an out-of-tree copy and add tests until the score is 95% or more; exclude survivors only with written reasons. Verify the mutation report.

## 4. Electron main process

- [x] 4.1 Implement the backend manager: run-mode selection helper, spawn with a clean key-free environment, ready-line wait with version check, restart with capped backoff and a quitting flag, per-OS quit kill (SIGTERM then SIGKILL on POSIX, tree kill on Windows). Cover with vitest tests that use a stub child script and injected timers. Verify the tests pass.
- [x] 4.2 Implement the main-side protocol client: line buffering, action on complete lines only, partial-line discard on child exit, malformed-line drop. Cover with vitest tests over chunked byte streams. Verify the tests pass.
- [x] 4.3 Implement the config store: safeStorage encrypt and decrypt, the encryption guard with the weak-backend refusal, the undecryptable-ciphertext path, and the masked value. Cover with vitest tests over an injected safeStorage stub. Verify the tests pass.
- [x] 4.4 Implement the history store: one JSON file per conversation, whole-file atomic writes, delete, and the setup-done mark. Cover with vitest tests over a temp user data folder, including the crash-mid-write invariant. Verify the tests pass.
- [x] 4.5 Implement the wizard state machine and the settings state (repeat wizard, default model change, base URL override, each change persisted at once). Cover with vitest tests. Verify the tests pass.
- [x] 4.6 Implement window creation: sandbox, context isolation, no Node in page, CSP header, popup denial, and external links to the system browser. Cover with vitest tests that assert the window options and the link handler. Verify the tests pass.
- [x] 4.7 Implement the log writer with 5 MB rotation and at most 5 archives, and the readiness result line for the smoke harness. Cover with vitest tests. Verify the tests pass.

## 5. Renderer

- [x] 5.1 Implement the preload `contextBridge` API with the narrow method set. Cover with vitest tests over a stubbed `contextBridge`. Verify the tests pass.
- [x] 5.2 Implement the chat UI logic: sidebar state, message list assembly, streaming bubble updates, the markdown plus sanitizer pipeline, and title derivation (first line, 40 characters). Cover the pure logic with vitest tests in jsdom, including the three sanitize scenarios. Verify the tests pass with the thresholds green.
- [x] 5.3 Implement the wizard UI (two steps, inline errors, retry on list failure, finish with `any` when the list is down) and the settings panel. Cover the logic with vitest tests. Verify the tests pass.

## 6. App wiring

- [ ] 6.1 Write `src/main/main.mjs`: single-instance lock, first-launch rule from the setup-done mark and decryptability, IPC glue, and the backend error banner. Cover the wiring with vitest integration tests over stubs. Verify the tests pass.
- [ ] 6.2 Verify the dev loop by hand: `npm run dev` opens the window, the wizard shows, and `logs/backend.log` appears in the dev user data folder. Record the observed behavior in the PR notes.

## 7. Packaging and CI

- [ ] 7.1 Add `runtime-lock.json` with the pinned CPython 3.13 release tag and per-platform sha256, and implement `scripts/fetch-python.mjs` (download, verify checksum, unpack). Cover the lock parsing and checksum check with vitest tests over a fixture. Verify the script fetches the arm64 macOS runtime locally.
- [ ] 7.2 Add the target install step that runs pip with the fetched interpreter. Verify locally that the fetched interpreter imports a package from `build/pylibs`.
- [ ] 7.3 Add `electron-builder.yml` with the targets, the ad-hoc macOS identity, the `beforePack` hook, and `extraResources` for `python/`, `pylibs/`, `backend/`. Verify `npx electron-builder --dir` on macOS produces a `.app` that contains the trees.
- [ ] 7.4 Add the smoke harness script: per-OS launch mechanics, the PATH-without-python guard, and the readiness line read from the log file. Verify it passes against the local `--dir` build.
- [ ] 7.5 Add `.github/workflows/build.yml` with the four jobs (`macos-15` arm64, `macos-15-intel`, `windows-latest`, `ubuntu-24.04` under `xvfb-run`), artifact upload, the ad-hoc signature check, and the smoke test. Verify the workflow triggers on the PR and the macOS job builds.
- [ ] 7.6 Write `fde/README.md`: what and why, dev commands, per-OS install and first-run steps, and the architecture sketch. Verify each documented command runs as written.

## 8. Claude surfaces and repo hygiene

- [ ] 8.1 Add `.claude/skills/fde-app/SKILL.md` with the dev, test, and build commands, exit codes, and known problems. Verify the skill appears in the session listing.
- [ ] 8.2 Add the `fde` project entry to CLAUDE.md Projects. Verify the entry names commands that exist.
- [ ] 8.3 Check the working copy for strays (`build/`, `dist/`, `vendor.js`, pip artifacts) and make sure the ignore rules cover them. Verify `git status --short` shows only intended files.

## 9. Full gates

- [ ] 9.1 Run the full hermetic suite: `python -m pytest`, branch coverage with `fail_under` at the reached total, ruff `C901`, and the mutmut run at 95% or more from the out-of-tree copy. Verify all four report green and record the numbers.
- [ ] 9.2 Run `npx vitest run --coverage` and verify the thresholds hold at 100 for the covered globs.
- [ ] 9.3 Run `openspec validate add-openrouter-desktop-app --strict` and verify it passes.
- [ ] 9.4 Walk every spec scenario and confirm at least one test covers it; list any gaps in the PR body and close them. Verify the checklist appears in the PR.

## Workflow follow-up

- Commit with a Conventional Commit message and the Claude Code attribution trailer, then publish the branch.
- Open the PR with `gh` using the ArtemKoval token per command (the active `gh` account is read-only; never `gh auth switch`).
- Run the adversarial diff review (Workflow tool) as pipeline Step 12, fix confirmed findings, and re-run the gates.
- Merge by squash, run `/opsx:archive` as the last commit, delete the branch locally and remotely, and resync `main`.
