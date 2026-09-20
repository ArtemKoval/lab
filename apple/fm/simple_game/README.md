# Snake, written by the Apple Foundation Model

`./build.sh` makes a playable HTML5 Snake game.
The on-device Apple Foundation Model writes every line of the game code.
The script writes no game logic. The script prepares the prompts, applies the gates
and repairs a unit that fails.

`PLAN.md` holds the full step-by-step plan and the reason for each design decision.

---

## 1. Requirements

| Item | Needed version | Test |
| --- | --- | --- |
| macOS with Apple Intelligence | 26 or later (this host is 27.0) | `/usr/bin/fm available` |
| The `fm` command | any | `fm available` prints `System model available` |
| Node.js | v24 | `node --version` |
| npm | 11 or later | `npm --version` |
| python3 | 3.9 or later, for `--serve` | `python3 --version` |
| A modern browser | any | it must accept `<script type="module">` |

The build needs the network one time for `npm install`.
Every model call is local. No prompt leaves the machine.

Turn on Apple Intelligence in System Settings when `fm available` fails.

---

## 2. Quickstart

```sh
cd /Users/art/Documents/git/lab/apple/fm/simple_game
./build.sh
./build.sh --serve
```

Then open http://localhost:8080/web/index.html.

The server root is the project root, not the directory `web`.
`web/game.js` imports `../src/core.js`, and the browser resolves that path
against the server root. A server rooted at `web` answers 404 for the core
and the page stays black. Step 12 proves this with a real HTTP request.

The first build takes 15 to 60 minutes.
A clean build makes 31 model calls or more.
One call takes 4 s to 120 s. The model runs on the local device.

The build prints one line for each step and one line for each gate.
The build writes a full log to `.build/build.log` and a summary to `.build/report.txt`.

A second `./build.sh` exits in a few seconds and reports every step as done.

---

## 3. What the build makes

```
src/*.js            13 pure core functions, written by the model
test/*.test.mjs     one test file for each core function, written by the model
src/core.js         a re-export barrel, written by build.sh
web/game.js         canvas render and keyboard input, written by the model
web/index.html      the page shell, written by the model
.build/report.txt   the result of every gate
```

The model writes the implementation and the tests from the same frozen contract,
in two separate calls. No call sees the other answer.
`PLAN.md` section 2.4 explains the limits of that comparison.

---

## 4. Flags

A signal stops the build. `ctrl-c` releases the lock, prints the resume command and
exits with the code of the signal. The build never goes on after a signal.


| Flag | Action |
| --- | --- |
| (none) | Run every step. Resume from the ledger in `.build/state/`. |
| `--clean` | Delete `.build`, `src`, `test`, `web/game.js`, `web/index.html` and `contracts/SHA256SUMS`, then start again. |
| `--from N` | Start again at step N, `N` from 0 to 12. It clears the ledger of step N and of every later step, and the per unit ledger of the steps 3 and 4. The cache makes this cheap. |
| `--only N` | Run step N alone. It then clears the ledger of every later step, because the gates of those steps did not see the new files. |
| `--refreeze` | Accept the current contracts as the frozen ones, rewrite `contracts/SHA256SUMS` and ask the model again for every unit and every test. |
| `--list` | Print the 13 steps and stop. |
| `--serve` | After a good build, serve `web/` and print the URL. |

`--serve` runs `python3 -m http.server 8080` in the project root.
Press Control-C to stop the server.
A build without `--serve` prints the same command at the end.

---

## 5. Environment knobs

| Name | Default | Meaning |
| --- | --- | --- |
| `FM_BIN` | `/usr/bin/fm` | the model command |
| `FM_RETRIES` | `3` | repair attempts for each unit and each gate |
| `FM_TIMEOUT` | `240` | seconds for one model call |
| `MUTATION_THRESHOLD` | `80` | the minimum stryker score in percent |
| `COVERAGE_THRESHOLD` | `90` | the minimum line coverage in percent |
| `BRANCH_THRESHOLD` | `80` | the minimum branch coverage in percent |
| `FUNCS_THRESHOLD` | `90` | the minimum function coverage in percent |
| `COMPLEXITY_MAX` | `5` | the maximum cyclomatic complexity of one function |
| `ALLOW_FALLBACK` | `0` | `1` writes the contract fallback code on a hard failure |

Example:

```sh
MUTATION_THRESHOLD=90 FM_RETRIES=5 ./build.sh
```

`MUTATION_THRESHOLD` and `thresholds.break` of `stryker.config.json` must hold the
same number. The mutation gate compares the two and stops when they disagree,
because stryker judges the run by its own value and the gate judges it by the knob.

`COMPLEXITY_MAX` reaches eslint through the environment. `eslint.config.mjs` reads it.

Do not set a short `FM_TIMEOUT`.
This session measured single calls of 4.3 s, 4.8 s and 16.9 s,
and the probes measured single calls above 120 s.

`ALLOW_FALLBACK=1` makes the build continue after a hard failure.
The build then copies the FALLBACK block of the contract into the file.
That unit is not model output. The report names every such unit.
The default value 0 keeps the build honest.

---

## 6. How to play

- Open http://localhost:8080/web/index.html.
- The grid is 20 by 20 cells. Each cell is 20 pixels. The canvas is 400 by 400 pixels.
- The snake moves one cell every 120 ms.
- Press an arrow key or W, A, S or D to change the direction.
- The game refuses a 180 degree reversal. The snake never turns into its own neck.
- The snake grows by one cell for each food cell. The score rises by 1.
- The game shows `GAME OVER` when the snake hits a wall or hits itself.
- Reload the page to play again.

---

## 7. How to read a gate failure

The build stops at the first gate that stays red after `FM_RETRIES` attempts.
The build prints the unit name, the gate name, the attempt count,
the path of the last model answer and the exact command to reproduce the failure.

The machine-readable detail goes to `.build/feedback/`:

| File | Content |
| --- | --- |
| `.build/feedback/unit.txt` | `TEST <name> \| FILE <path>:<line> \| GOT <value> \| EXPECTED <value>` |
| `.build/feedback/complexity.txt` | the exact eslint lines |
| `.build/feedback/coverage.txt` | the uncovered file and line range |
| `.build/feedback/mutation.txt` | each surviving mutant and its diff |
| `.build/feedback/equivalent.txt` | mutants that no test can kill |
| `.build/feedback/serve.txt` | any file of the module graph that does not answer 200 |

### 7.1 The unit gate

Reproduce it:

```sh
node --test "test/**/*.test.mjs"
```

Always use the quoted glob.
`node --test test/` is broken on node 24.
This session measured exit code 1 and a false failure at `test:1:1` for the directory form,
and exit code 0 for the glob form on the same passing suite.

A red unit gate has two causes. Find the cause before you run the build again:

1. The implementation is wrong. The repair loop must fix it. Read `.build/feedback/unit.txt`.
2. The contract CASES table holds a wrong expected value. The loop cannot fix that.
   Read `contracts/NN-<unit>.md`, correct the value, then run `./build.sh --from 2`.

`fm respond -g` is byte deterministic.
This session ran the same call two times and got two byte-identical files.
A second build with the same inputs therefore gives the same failure.
Read the contract first.

### 7.2 The complexity gate

Reproduce it:

```sh
npx eslint src
```

A real message from this session:

```
src/_messy.js
  1:8   error  Function 'messy' has a complexity of 11. Maximum allowed is 5  complexity
  2:29  error  Blocks are nested too deeply (3). Maximum allowed is 2         max-depth
```

The build gives that exact line back to the model.
After 2 attempts the build issues the unit again from the SKELETON section of the contract.
A `max-params` error has no repair path. The signature is wrong. Correct the contract.

### 7.3 The coverage gate

Reproduce it:

```sh
node --test --experimental-test-coverage "test/**/*.test.mjs"
```

This gate never changes the implementation.
The uncovered lines go to the strengthen pass of step 9 as an input.

### 7.4 The mutation gate

Reproduce it:

```sh
npx stryker run
```

A surviving mutant means one thing only: the test suite does not see that change.
`tools/derive.mjs` searches the contract DOMAIN for an input that separates
the original from the mutant.
A survivor with no such input is an equivalent mutant.
Two mutants of `turn` are equivalent over the four legal direction strings.
No test kills them. The build lists them in `.build/feedback/equivalent.txt` and continues.

### 7.5 The playtest gate

Reproduce it:

```sh
node tools/drive.mjs
```

A pass prints `ALL RUNTIME ASSERTIONS PASSED`.
`node --check` is not a gate for the browser layer.
A markdown fence opens a template literal, so a file of pure English passes `node --check`.
Only execution proves the renderer.

---

## 8. Manual commands

```sh
npm test            # node --test "test/**/*.test.mjs"
npm run coverage    # the same, with the built-in coverage report
npm run lint        # eslint on src
npm run lint:web    # eslint on web/game.js
npm run mutation    # stryker run
npm run serve       # python3 -m http.server 8080 in the project root
```

---

## 9. Limits you must know

- The contract CASES table holds the expected values.
  The model transcribes those values. The model does not verify them.
  A wrong value in a contract gives a wrong test and a red gate for ever.
- The context window holds about 4096 tokens for the prompt and the answer together.
  A 4299-token prompt failed in this session with
  `Error: The session's transcript exceeded the model's context size.` and exit code 1.
- The model answers a small contract well and a large task badly.
  A single call for a 3-function module gave 1166 bytes of confident code with 5 defects.
  Therefore the build asks for one function for each call.
- Run one build at a time. Parallel model calls starve the system model.
- Do not edit a file under `prompts/` without a new probe.
  One removed line of `prompts/impl.md` made the model answer without braces in this session.
- A CASES row must hold a plain call. The model mangles an arrow function that runs at once.
  Two such rows gave `growOrMove([{x:1,y:1}]()` and a wrong `assert.throws` in this session.
- `assert.equal` of `node:assert/strict` is `strictEqual`. It never matches two arrays.
  The build counts the `deepEqual` calls of each answer and refuses an answer that holds too few.

---

## 10. Files

```
build.sh              the governing script
PLAN.md               the full plan and the measurements
README.md             this file
contracts/            13 core contracts, 4 renderer contracts and SHA256SUMS
prompts/              the system prompts and the user templates
lib/                  log.sh, fm.sh, gates.sh
tools/                derive.mjs, drive.mjs
src/                  the model implementation and the generated barrel
test/                 the model tests, frozen after step 4
web/                  index.html and game.js
.build/               state, logs, feedback, cache, report.txt
```
