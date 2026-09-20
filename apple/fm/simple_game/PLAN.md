# Build plan: a Snake game written by the Apple Foundation Model

This plan tells you how `./build.sh` makes a playable HTML5 Snake game.
The on-device Apple Foundation Model writes the game code.
The script writes no game logic. The script only prepares prompts, applies gates and repairs.

The model runs through `/usr/bin/fm`. The host is macOS 27.0, build 26A428.

---

## 1. What the build makes

| Output | Author | Purpose |
| --- | --- | --- |
| `src/*.js` | the model | 13 pure core functions, one file for each function |
| `test/*.test.mjs` | the model | one `node:test` file for each core function |
| `src/core.js` | `build.sh` | a mechanical re-export barrel |
| `web/game.js` | the model | canvas render and keyboard input |
| `web/index.html` | the model | the page shell |
| `test/strengthen-*.test.mjs` | the model | extra tests that kill surviving mutants |
| `.build/report.txt` | `build.sh` | the result of every gate |

The game is Snake on a 20 by 20 integer grid.
The core uses integer arithmetic only. Every core function is pure.

---

## 2. Why the design has this shape

Two measured facts control the whole design.

### 2.1 The context window is about 4096 tokens

The window holds the input and the output together.
A 3564-token prompt gives an answer.
A 4299-token prompt fails with `Error: The session's transcript exceeded the model's context size.` and exit code 1.

Therefore the build never gives the model a file, a module or a full specification.
Each prompt stays below 1200 tokens. The rest of the window holds the answer.
Step 2 measures every assembled prompt one time with `fm count-tokens -q`.
The repair loop uses a truncation ladder, because a large repair prompt also breaks the window.

### 2.2 The model writes stubs when the task is large

A measurement from this session shows the failure clearly.
The prompt was: "Write a JavaScript module for a Snake game core. Export three functions: nextHead(pos, dir), growOrMove(body, head, ate) and step(state, input, rng)."

The answer arrived in 16.9 s, in 1166 bytes, inside a ```` ```javascript ```` fence.
The code looks confident. The code is wrong:

- `nextHead` reads the cell as an array `[x, y]`, not as the object `{x, y}`.
- `growOrMove` mutates `body` and returns `undefined`.
- `growOrMove` appends the head to the tail, so the head is not element 0.
- `step` calls `input.map(...)` on a direction string.
- `step` calls `rng.boolean()`, which does not exist.

The same model answers one small contract correctly.
The contract for `hitsWall(pos, w, h)` with three worked examples gave this in 4.8 s:

```js
export function hitsWall(pos, w, h) {
    const x = pos.x;
    const y = pos.y;
    return x < 0 || y < 0 || x >= w || y >= h;
}
```

`node --check` accepts that file.

Therefore the unit of work is ONE function, with the exact signature, the literal types and
two or three worked examples. The build never asks for a module and never asks for a file.

### 2.3 Every line of a system prompt is load bearing

The measurement above used the full `prompts/impl.md` text, which costs 165 tokens.
A second run of the same call removed one line:
`- Open the body with "{" and close it with "}". The last character is "}".`

The model then answered:

```
export function hitsWall(pos, w, h)
return pos.x < 0 || pos.y < 0 || pos.x >= w || pos.y >= h
```

The braces are absent and the file does not parse.
Do not edit a system prompt without a new probe.

### 2.4 Blind dual generation

The model transcribes. The model does not verify.
Therefore one model answer is not a proof of the other model answer.

The build makes the two answers independent:

- The implementation call reads only SIGNATURE, DESCRIPTION and EXAMPLES.
- The test call reads only SIGNATURE, TYPES, BEHAVIOUR and CASES.
- No call sees the other output.

The comparison is real, but it is limited.
The CASES table holds literal expected values, because the model cannot compute an expected value.
The contract author writes the oracle.
The true comparison is contract against implementation, not test against implementation.
The mutation gate is the defence against a weak test suite.

One part of the build is not blind.
`tools/derive.mjs` reads the expected value from `src/<unit>.js`, because a killed mutant gives no expected value.
The unit gate runs before the mutation gate.
The implementation therefore agrees with every CASES row of its contract at that moment.
A strengthen test extends that agreement to one more input.
The limit is clear.
A wrong implementation that satisfies its contract gives a strengthen test that holds the wrong behaviour.
Read a mutation score as a measure of test strength, not as a measure of correctness.

### 2.5 Determinism

`fm respond -g` is byte deterministic.
Two identical calls in this session gave two byte-identical files.

This fact gives the build a cache and one hard rule:
a repair attempt must change the prompt bytes, or the answer stays the same.
The escalation ladder in section 6 supplies that change.

---

## 3. The generate, gate and repair loop

```
                     contracts/NN-<unit>.md          (frozen, sha256)
                              |
         SIGNATURE            |            SIGNATURE
         DESCRIPTION          |            TYPES
         EXAMPLES             |            BEHAVIOUR
              |               |               |      CASES
              v                               v
       prompts/impl.md                 prompts/test.md
       prompts/skeleton.md                    |
              |                               |
              v                               v
      fm respond --no-stream -g       fm respond --no-stream -g
      (flock, timeout 240, cache)     (flock, timeout 240, cache)
              |                               |
              |   the two calls never see each other: BLIND
              v                               v
      strip ``` fences                strip ``` fences
      grep for a backtick             grep for a backtick
      normalise to one function       first line must be the node:test import
      node --check                    node --check
      dynamic import                  one test( for each CASE
              |                               |
              v                               v
        src/<fn>.js                    test/<fn>.test.mjs
              |                               |
              |                               +--> sha256 -> FROZEN for ever
              |                               |
              +---------------+---------------+
                              v
                  +-----------------------+
                  |        GATES          |
                  |  1 node --test        |
                  |  2 eslint complexity  |
                  |  3 coverage           |
                  |  4 stryker mutation   |
                  +-----------------------+
                       |             |
                  pass |             | fail
                       |             v
                       |    .build/feedback/<gate>.txt
                       |      TEST | FILE | GOT | EXPECTED
                       |             |
                       |             v
                       |    prompts/repair.md + prompts/repair.user.md
                       |      attempt 1: no hint
                       |      attempt 2: the HINT as an expression
                       |      attempt 3: skeleton, hole = literal expression
                       |             |
                       |             |  writes src/<fn>.js only
                       |             |  never writes a file under test/
                       |             v
                       |      sha256sum -c .build/state/tests.sha256
                       |             |
                       +<------------+   (at most FM_RETRIES attempts)
                       |
                       v
                  next step
```

The mutation gate uses a second loop, because it may not touch the implementation:

```
  npx stryker run
        |
        v
  [Survived] mutator, file, line, - old + new
        |
        v
  tools/derive.mjs  -- brute-force the contract DOMAIN
        |                     |
        | no difference       | a difference
        v                     v
  equivalent.txt       FILL block: the input tuple and the
  (leaves the loop)    expected value from the ORIGINAL
                              |
                              v
                     prompts/strengthen.md   (at most 20 FILL blocks in one call)
                              |
                              v
                     tools/judge.sh
                      SYNTAX_FAIL | FAILS_ON_ORIGINAL | SURVIVES | KILLS
                              |
                         KILLS only
                              v
                   test/strengthen-<round>.test.mjs      (at most 3 rounds)
```

The model never finds an input. The model never computes an expected value.
`tools/derive.mjs` does both, because it runs the real code.

---

## 4. Repository layout

```
build.sh                 the governing script (bash, set -Eeuo pipefail)
PLAN.md                  this plan
README.md                the quickstart
package.json             type module, the four gate scripts
eslint.config.mjs        the complexity gate for src
eslint.web.mjs           the lint rules for web/game.js
stryker.config.json      the mutation gate
lib/log.sh               log_step log_info log_ok log_warn log_err die
lib/fm.sh                fm_preflight and fm_generate, with the lock and the cache
lib/gates.sh             gate_unit gate_coverage gate_complexity gate_mutation
contracts/NN-<unit>.md   13 frozen contracts and SHA256SUMS
contracts/render-*.md    4 frozen contracts for the browser functions
prompts/*.md             the probe-winning system prompts and user templates
tools/derive.mjs         finds the input that kills a mutant
tools/drive.mjs          drives web/game.js under a fake DOM
src/*.js                 the model implementation, plus the generated barrel core.js
test/*.test.mjs          the model tests, frozen after step 4
web/index.html           the page shell
web/game.js              the render and input layer
.build/                  state, logs, feedback, transcripts, cache, report.txt
```

---

## 5. The steps

`./build.sh --list` prints these 13 steps.
Each step writes `.build/state/NN.done` at the end. A second run skips a done step.

### Step 0 — preflight

**What it does.** The step makes `.build/{state,logs,feedback,transcripts,cache}`.
It resolves `FM_BIN`, `FM_RETRIES`, `FM_TIMEOUT`, `MUTATION_THRESHOLD`, `COVERAGE_THRESHOLD`,
`COMPLEXITY_MAX` and `ALLOW_FALLBACK`, then writes them to `.build/env.txt`.
`lib/fm.sh` takes an exclusive `flock` on `.build/fm.lock` around every model call,
because parallel calls starve the system model.
Every model call runs under `timeout 240`.

**Prompts and contracts.** None. This step makes no model call.

**Gates.** `$FM_BIN available` prints `System model available`.
`$FM_BIN count-tokens -q 'hello'` prints a bare integer.
`node --version` starts with `v24`. `npm --version` and `python3 --version` exit 0.
The `.build` tree exists and accepts a write.

**On a failure.** The build stops at once with the name of the missing tool.
No model call starts before this step passes.

### Step 1 — scaffold

**What it does.** The step writes the static files: `package.json`, `eslint.config.mjs`,
`eslint.web.mjs`, `stryker.config.json`, `.gitignore`, `lib/*.sh` and `tools/*`.
The step copies `node_modules` from the validated sandbox when that directory exists,
then runs one `npm install` to reconcile the tree.
The step then writes a throw-away `src/_smoke.js` and `test/_smoke.test.mjs`,
runs all four gates against them, and deletes both files.

**Prompts and contracts.** None.

**Gates.** `npm install` exits 0.
`node --test "test/**/*.test.mjs"` exits 0 on the smoke unit.
`npx eslint src` exits 0. `npx stryker --version` exits 0.
`grep -q 'node --test test/' package.json` returns non-zero.

**On a failure.** The build stops. A tool failure at step 9 wastes a full generation run,
so the build proves the tool chain before the first model call.
The last gate exists because `node --test test/` is broken on node 24.
That form resolves `test/` as a module and reports a false failure at `test:1:1`.
This session measured exit code 1 for the directory form and exit code 0 for the glob form
on the same passing suite.

### Step 2 — contracts

**What it does.** The step writes `contracts/00-samePos.md` to `contracts/12-step.md`.
Each contract holds the fixed sections SIGNATURE, STYLE, DEPS, DESCRIPTION, EXAMPLES,
TYPES, BEHAVIOUR, CASES, DOMAIN, HINT and FALLBACK.
The step assembles every implementation prompt and every test prompt,
measures each one time with `fm count-tokens -q`, and writes `.build/logs/tokens.txt`.
The step then writes `contracts/SHA256SUMS` and freezes the contracts.

**Prompts and contracts.** The contracts are the input of every later model call.

**Gates.** 13 contract files exist and hold every required section.
Each assembled implementation prompt is `REPAIR_BUDGET` tokens or less. The default is 1200.
Each assembled test prompt is `REPAIR_BUDGET` tokens or less.
Each contract file is `CONTRACT_HARD_MAX` tokens or less. The default is 1200.
`contracts/SHA256SUMS` matches the files on disk.

A contract above `CONTRACT_BUDGET` (400) gives a warning, not a stop.
This session measured every real contract at 368 to 844 tokens.
The 400 token target is not reachable for 12 of the 13 units.
The gate that matters is the assembled prompt, and the worst one measured 663 tokens.

**On a failure.** A prompt above the ceiling is an author error, not a model error.
The step names the file and the token count. Shorten the contract and run the step again.

### Step 3 — impl

**What it does.** For each of the 13 units, in dependency order, the step builds the cache key
`sha256(system_prompt + user_prompt)`.
A cache hit reuses `.build/cache/<key>.js`, because `-g` is byte deterministic.
A cache miss makes exactly one model call.
`tools/normalise.sh` then removes every fence line, cuts the text before `function <fn>(`,
cuts the text after the balanced closing brace, and adds `export ` when the keyword is absent.
`build.sh` writes `src/<fn>.js` as the fixed DEPS import header plus the normalised function.
The model never writes an import line.

**Prompts and contracts.** `prompts/impl.md` with `prompts/impl.user.md` for a STYLE=rules unit.
`prompts/skeleton.md` with `prompts/skeleton.user.md` for a STYLE=skeleton unit.
The prompt carries SIGNATURE, DESCRIPTION and EXAMPLES only.

**Gates.** The raw answer is over 40 bytes and holds the function name.
The normalised file holds no backtick.
The file starts with `export function <fn>(`.
`node --check src/<fn>.js` exits 0.
A dynamic import gives `typeof mod[fn] === 'function'`.

**On a failure.** The unit enters the repair loop of section 6.
An empty answer repeats at once and does not consume an attempt.

### Step 4 — tests

**What it does.** One model call for each unit writes `test/<fn>.test.mjs`.
The prompt carries SIGNATURE, TYPES, BEHAVIOUR and the numbered CASES table.
The prompt never carries the implementation.
After the last unit the step writes `.build/state/tests.sha256`.
Every test file is frozen from that moment.

**Prompts and contracts.** `prompts/test.md` with `prompts/test.user.md`.

**Gates.** The first line is exactly `import { test } from 'node:test';`.
The file holds no backtick and no `require(`.
`node --check` exits 0.
The count of `test(` equals the count of numbered CASES.
The file names no core function other than the target.
Every expected literal in the file appears in the contract CASES text.

**On a failure.** The step calls the model again with a stricter prompt.
The step never edits a test file by hand. A test file is model output or it is absent.

### Step 5 — assemble

**What it does.** `build.sh` writes `src/core.js` as a re-export barrel over the 13 unit files.
The script writes this file, because the model drops import and export lines.
The barrel gives the browser layer the single path `../src/core.js`.

**Prompts and contracts.** None.

**Gates.** `node --check src/core.js` exits 0.
A dynamic import exports all 13 names.
`npx eslint src` exits 0 for parse errors at this point.

**On a failure.** The step names the missing export. The failure points at step 3, not at the barrel.

### Step 6 — unit gate

**What it does.** The step runs `node --test "test/**/*.test.mjs"` and judges by the exit code.
The step never judges by a grep of the output.
On a failure the step repairs one unit at a time, in dependency order.
Only a file under `src/` changes.

**Prompts and contracts.** `prompts/repair.md` with `prompts/repair.user.md`, format D.

**Gates.** `node --test "test/**/*.test.mjs"` exits 0.
`sha256sum -c .build/state/tests.sha256` exits 0.

**On a failure.** Section 6 gives the escalation ladder.
A changed test file aborts the build at once.

### Step 7 — complexity

**What it does.** The step runs `npx eslint src`.
`lib/gates.sh` parses the machine-readable lines into `.build/feedback/complexity.txt`.
The exact eslint line goes into the OBSERVED slot of the repair prompt.

**Prompts and contracts.** `prompts/repair.md`, then `prompts/skeleton.md` after attempt 2.

**Gates.** `npx eslint src` exits 0 with no output.
No file under `src/` declares more than one export.

**On a failure.** The repair loop runs at most 2 attempts.
After that the step issues the unit again through the SKELETON section of the contract.
The contracts already decompose `step` and `placeFood`,
because the monolithic forms break `complexity` and `max-depth`.
This gate therefore catches a regression.

### Step 8 — coverage

**What it does.** The step runs `node --test --experimental-test-coverage "test/**/*.test.mjs"`
and parses the `all files` summary row.

**Prompts and contracts.** None. A shortfall starts the strengthen pass of step 9.

**Gates.** Line coverage is `COVERAGE_THRESHOLD` percent or more.
Branch coverage is 80 percent or more.

**On a failure.** This gate never repairs the implementation.
The uncovered file and line range go to `.build/feedback/coverage.txt`
and then to the strengthen pass as an input.

### Step 9 — mutation

**What it does.** The step runs `npx stryker run`
and parses each `[Survived]` block into mutator, file, line, column and the diff pair.
`tools/derive.mjs` writes each mutant to a temporary copy, imports the original and the mutant,
and searches the contract DOMAIN for the first argument tuple with two different results.
The expected value comes from the ORIGINAL.
A survivor with no distinguishing input is an equivalent mutant.
A survivor that the tool cannot judge, because the mutant does not load or the unit has
no domain, is UNPROVEN. The gate reads UNPROVEN as red. A mutant that does not parse is
never an equivalent mutant.

**Prompts and contracts.** `prompts/strengthen.md` with `prompts/strengthen.user.md`.
One call holds at most `STRENGTHEN_FILLS` blocks. The build measures the assembled
prompt and halves the count of blocks until the prompt fits `FM_PROMPT_BUDGET`,
because 20 blocks of the unit `step` measure about 2400 tokens.

**Gates.** The stryker score is `MUTATION_THRESHOLD` percent or more, or the amnesty
holds. The amnesty needs three facts together: the score is not more than 10 points
under the threshold, `tools/derive.mjs` reports no UNPROVEN survivor, and the set of
survivor LOCATIONS is equal to the set of proven equivalent LOCATIONS. The gate
compares two sets of locations, never two counts.
Every appended test passes against the current `src`.
`sha256sum -c .build/state/tests.sha256` exits 0.

**On a failure.** `tools/judge.sh` gives each candidate one of four states:
SYNTAX_FAIL, FAILS_ON_ORIGINAL, SURVIVES or KILLS.
Only a KILLS candidate joins `test/strengthen-<round>.test.mjs`.
The loop stops after 3 rounds, or at the threshold, or when only equivalent mutants remain.

### Step 10 — renderer

**What it does.** Five model calls write the browser layer, one function for each call:
`drawBoard(ctx, state, cell)`, `keyToInput(key)`, `startLoop(state, tick, render, ms)` and
`boot(doc, cols, rows, cell)`. A sixth call writes `web/index.html`.
`build.sh` writes four fixed header lines, then the four functions, then the fixed footer line
`boot(document, 20, 20, 20);`.
The header lines are the core import, the input queue `queued`, the closure `tick`
and the closure `press`. The model writes no import line and no shared variable.
`queued` is a FIFO queue and not one slot, so a fast two key corner turn keeps both
keys. `press` takes the whole keyboard event and calls `preventDefault`, so the arrow
keys never scroll the page.

**Prompts and contracts.** `prompts/render.md` with `prompts/render.user.md`.
`prompts/html.md` with `prompts/html.user.md`.
`contracts/render-drawBoard.md`, `contracts/render-keyToInput.md`,
`contracts/render-startLoop.md` and `contracts/render-boot.md` hold the sections
GLOSSARY, STEPS, EXAMPLES, SCOPE and RETURN_CLAUSE.
Every prompt says "Write one JavaScript function with this exact signature:".
No prompt says "write the file", because that framing gives a fence every time.

**Gates.** No generated file holds a backtick after the fence stripper runs.
`node --check web/game.js` exits 0.
`npx eslint -c eslint.web.mjs web/game.js` exits 0.
`web/game.js` holds `ArrowUp`, `ArrowDown`, `ArrowLeft` and `ArrowRight`.
`web/index.html` holds `<canvas id="game"` and `<script type="module" src="game.js">`.

**On a failure.** The step calls the model again for the one function that failed.
The HTML call always needs the fence stripper.

### Step 11 — playtest

**What it does.** `tools/drive.mjs` stubs `document`, a canvas element, a Proxy 2d context,
`window.addEventListener` and `setInterval`, then imports `web/game.js`.
The driver asserts the canvas size, the tick period, the background rectangle in pixels,
the food rectangle, one rectangle for each body cell, the score text, the key map,
the refusal of a 180 degree reversal, a score rise after the snake eats,
and the `GAME OVER` text after the snake leaves the grid.

**Prompts and contracts.** None.

**Gates.** `node tools/drive.mjs` exits 0 and prints `ALL RUNTIME ASSERTIONS PASSED`.
The recorded background rectangle is exactly `[0, 0, 400, 400]`.
The recorded interval period is 120.

**On a failure.** The step names the wrong assertion and returns to step 10 for that one function.
`node --check` is not a gate for this layer.
A markdown fence opens a template literal, so a file of pure English passes `node --check`.
Execution is the only real gate for the renderer.

### Step 12 — package

**What it does.** The step writes `.build/report.txt` with the result of every gate,
the model call count, the cache hit count, the wall time of each step,
the repair attempts and the equivalent mutant list.
The step writes `README.md` numbers and refreshes the gate numbers in this plan.
With `--serve` the step runs `python3 -m http.server 8080` in the PROJECT ROOT.
The server root is the project root, not `web`. `web/game.js` imports `../src/core.js`,
and the browser resolves that path against the server root.
This session measured 404 for `/src/core.js` with a server rooted at `web`.

**Prompts and contracts.** None.

**Gates.** Every path of section 4 exists.
A local server at the project root answers 200 for `web/index.html`, `web/game.js`,
`src/core.js`, `src/step.js` and `src/createState.js`.
`./build.sh --list` exits 0 and prints 13 steps.
A second `./build.sh` exits 0 and reports every step as done.

**On a failure.** The step names the missing path.

---

## 6. The repair loop

### 6.1 Scope

The loop writes `src/<fn>.js` only.
The loop never writes a file under `test/`.
`build.sh` runs `sha256sum -c .build/state/tests.sha256` before and after every attempt.
A mismatch aborts the build.

### 6.2 Validation order

The build validates every model answer in this order, always:

1. Size. Under 40 bytes counts as EMPTY.
2. Fence strip with `awk '/^[[:space:]]*```/ {next} {print}'`, always.
3. Backtick grep. A backtick fails the answer.
4. Normalisation to one function.
5. `node --check`.
6. Dynamic import and a `typeof` test.
7. The gate itself.

Step 3 runs before step 5 for a measured reason.
A fence opens a template literal, so a file of pure English passes `node --check`.
A build that reorders these steps ships a dead file.

### 6.3 The prompt, format D

The repair prompt holds five slots:
CONTRACT, CURRENT_CODE, FAILING_TEST_SOURCE, OBSERVED and ESCALATION.
CURRENT_CODE is never absent. The broken code anchors the answer.
Raw `node --test` output never enters a prompt.
The condenser writes four lines for each failing test:
`TEST <name> | FILE <path>:<line> | GOT <value> | EXPECTED <value>`.

### 6.4 The truncation ladder

The build measures the assembled prompt one time. The ceiling is 1200 tokens.
While the count is above the ceiling, the build applies the next rule and measures again:

| Rule | Action |
| --- | --- |
| T1 | Keep at most the first 3 failing tests |
| T2 | Clip each test block to 15 lines |
| T3 | Clip each GOT and EXPECTED value to 200 characters |
| T4 | Drop the OBSERVED block |
| T5 | Keep only the first failing test |
| T6 | Drop EXAMPLES from CONTRACT |

After T6 the gate fails with `repair prompt cannot fit the context window for <unit>`.

### 6.5 The escalation ladder

`FM_RETRIES` defaults to 3 attempts for each unit and each gate.
Every attempt must change the prompt bytes, because `-g` gives the same answer to the same bytes.

| Attempt | ESCALATION slot |
| --- | --- |
| 1 | empty |
| 2 | the contract HINT, written as an executable expression |
| 3 | `Write exactly this expression: <HINT>`, plus a switch to the skeleton prompt |

An EMPTY answer repeats at most 2 times and does not consume an attempt.

### 6.6 Two units with no repair path

`step` and `advance` never enter the normal repair loop.
The probes measured 0 of 10 on orchestrator repair and 0 of 10 on a surgical edit.
On a failure the build issues the same skeleton prompt at most 2 times.
Each new attempt states one more hole as a complete literal expression.
After that the build stops.

### 6.7 The hard failure

A red gate after `FM_RETRIES` writes `.build/feedback/<gate>.txt` and prints the unit name,
the gate name, the attempt count, the path of the last model answer,
and the exact command to reproduce the failure. The build then exits with a non-zero code.

`ALLOW_FALLBACK=1` changes this behaviour.
The build then copies the FALLBACK block of the contract into `src/<fn>.js`,
prints a loud warning, records the unit in `.build/report.txt` and continues.
That unit is not model output. `ALLOW_FALLBACK` defaults to 0.

### 6.8 The cache

Every model call has the key `sha256(system_prompt + user_prompt)` under `.build/cache/`.
A hit skips the call. This makes `--from N` and `--only N` cheap.
`--clean` removes the cache.

---

## 7. The 13 core units

The order is the dependency order of step 3.

| # | File | Signature | Style | Depends on |
| --- | --- | --- | --- | --- |
| 0 | `src/samePos.js` | `samePos(a, b)` | rules | none |
| 1 | `src/nextHead.js` | `nextHead(pos, dir)` | rules | none |
| 2 | `src/turn.js` | `turn(current, input)` | rules | none |
| 3 | `src/hitsWall.js` | `hitsWall(pos, w, h)` | rules | none |
| 4 | `src/hitsSelf.js` | `hitsSelf(pos, body)` | rules | none |
| 5 | `src/growOrMove.js` | `growOrMove(body, head, ate)` | rules | none |
| 6 | `src/freeCells.js` | `freeCells(occupied, w, h)` | rules | none |
| 7 | `src/pickCell.js` | `pickCell(free, rng)` | rules | none |
| 8 | `src/placeFood.js` | `placeFood(occupied, w, h, rng)` | skeleton | `freeCells`, `pickCell` |
| 9 | `src/createState.js` | `createState(w, h)` | rules | none |
| 10 | `src/isDead.js` | `isDead(head, state)` | skeleton | `hitsWall`, `hitsSelf`, `samePos`, `growOrMove` |
| 11 | `src/advance.js` | `advance(state, dir, head, rng)` | skeleton | `samePos`, `growOrMove`, `placeFood` |
| 12 | `src/step.js` | `step(state, input, rng)` | skeleton | `turn`, `nextHead`, `isDead`, `advance` |

Notes on the shape of this list:

- A direction is a string, not a vector. The model fails at vector arithmetic.
- `placeFood` exists as a composition of `freeCells` and `pickCell`,
  because the monolithic form breaks `max-depth 2`.
- `isDead` and `advance` exist because the monolithic `step` scores complexity 7.
- `isDead` tests the head against the body that STAYS, never against the body before
  the move. The tail leaves its cell on the same tick when the snake does not eat, so
  a head that enters the old tail cell lives. This is the classic Snake off by one.
- `placeFood`, `advance` and `boot` each take 4 parameters.
  4 is the `max-params` limit. A fifth parameter breaks the lint gate with no repair path.
- The state field is `over`, not `alive`.
- The input is `null` when the player presses no key.

---

## 8. Known risks

| Risk | Control |
| --- | --- |
| Latency of 4 s to 120 s for each call | `timeout 240`, never a tight timeout |
| A clean build makes 31 model calls or more | 15 to 60 minutes of wall time is normal |
| Parallel calls starve the model | one `flock` around every call, and one build-wide lock |
| The context ceiling of about 4096 tokens | the token gate of step 2 and the ladder of 6.4 |
| Equivalent mutants in `turn` | `tools/derive.mjs` detects them, and the loop caps at 3 rounds |
| A wrong expected value in a CASES table | read the CASES table first, do not run the build again |
| `createState` has no probe measurement | the first candidate for `ALLOW_FALLBACK` |
| The renderer has no unit test | `tools/drive.mjs` under a fake DOM, then a human with `--serve` |
| A server rooted at `web` breaks the import of the core | `gate_serve` asks a real server for every module |
| `npm install` needs the registry | step 1 proves all four tools before the first model call |
| `node --test test/` is broken on node 24 | every command uses the quoted glob form |
| A CASES row that holds an arrow function body | write a plain call, never an IIFE. The model mangles an IIFE |
| The model writes `assert.equal` for an array | `deep_gate` counts the `deepEqual` calls and refuses the answer |
| A repair answer that does not parse | the build puts the last good `src/<fn>.js` back |

Determinism cuts both ways.
A unit that fails one time fails in the same way for ever.
The first action after a failure is a read of the contract, not a second build.

---

## 9. Measurements from this session

| Measurement | Command | Result |
| --- | --- | --- |
| host | `sw_vers` | macOS 27.0, build 26A428 |
| model | `/usr/bin/fm available` | `System model available`, exit 0 |
| node | `node --version` | v24.0.1 |
| npm | `npm --version` | 11.3.0 |
| python3 | `python3 --version` | 3.12.9 |
| token count | `fm count-tokens -q 'hello'` | 2 |
| context limit | a 4299-token prompt | `Error: The session's transcript exceeded the model's context size.`, exit 1, 0 bytes on stdout |
| context headroom | a 3564-token prompt | the call returns an answer |
| module prompt | 3 functions in one call | 1166 bytes, 16.9 s, fenced, 5 defects |
| one contract | `hitsWall` with 3 examples | 129 bytes, 4.8 s, `node --check` exit 0 |
| prompt line test | the same call without the brace rule | 94 bytes, no braces, the file does not parse |
| `prompts/impl.md` cost | `fm count-tokens -q` | 165 tokens |
| determinism | the same call two times with `-g` | two byte-identical files |
| node test form | `node --test test/` | exit 1, false failure at `test:1:1` |
| node test form | `node --test "test/**/*.test.mjs"` | exit 0 on the same suite |
| eslint | a 4-parameter nested function in `src` | `Function 'messy' has a complexity of 11. Maximum allowed is 5  complexity` |
| eslint | version | 10.11.0 |
| stryker | version | 10.0.0 |
