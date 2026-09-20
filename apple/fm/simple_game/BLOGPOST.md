# 100% Coverage, 98% Mutation Score, Broken Game

*Building Snake with the on-device model that ships at /usr/bin/fm in macOS 27, and the defect every gate in the pipeline certified as green.*

The snake died when it moved into the square its own tail was leaving. That is the classic Snake tail off-by-one, and it shipped past 82 passing unit tests, 100.00% line coverage, 100.00% branch coverage and a 98.44% Stryker mutation score.

The gates were not lying. Tests, coverage and mutation each did exactly what they promise. The defect lived one level up, in the specification that the implementation *and* the tests were both generated from. The code implemented the wrong rule, the tests asserted it too, and the mutants that would have caught it were killed by tests defending the wrong behaviour.

## The tool

macOS 27.0 (build 26A428) ships a binary at `/usr/bin/fm`, the Apple Foundation Models CLI. Subcommands: `available`, `chat`, `count-tokens`, `license`, `respond`, `schema`, `serve`.

```
$ fm available
System model available
```

`fm serve` gives an OpenAI-shaped `/v1/chat/completions` endpoint, but the call I lived inside is the plain one:

```
fm respond --no-stream -g -i 'instructions' 'prompt'
```

`-g` is greedy decoding. Across the 32 calls of one clean build, the fastest took 6 seconds, the slowest 31, and the median was 13.

**The context window is about 4096 tokens, total — input plus output.** Measured, not read off a spec sheet. A prompt that `fm count-tokens` scores at 3992 comes back with an answer. One scored at 4492 comes back with

```
Error: The session's transcript exceeded the model's context size.
```

and an exit code of 0. That one fact eliminates every "point it at the repo" workflow and forces the unit of work down to a single function.

**The model writes confident stubs.** My first test asked for three functions of a Pong module. Verbatim, the whole of what came back:

```js
export function createState(w, h) {
  return {
    ball: { x: 0, y: 0 },
    paddle: { x: 0, y: 0 }
  };
}

export function stepBall(state, dt) {
  state.ball.x += 0.5 * dt;
}

export function reflect(ball, paddle) {
  ball.y = 1 - ball.y;
}
```

Syntactically perfect, semantically empty — no collision, no paddle, no bounds, just the shape of an answer with the answer removed. It parses and it lints, and nothing static has a useful opinion about it.

Two conclusions: the unit of generation has to be small enough that a stub is obviously a stub, and nothing the model writes gets believed. It gets executed.

A few more measured behaviours:

- `-g` is **byte deterministic**: the identical prompt returns the identical bytes. A retry is the same answer and another thirteen seconds. A repair must change the prompt bytes, or your error handling is an infinite loop with a price.
- It wraps code in markdown fences even when told not to. Strip them unconditionally.
- `fm` exits 0 on a bad answer, and on the context-size error above.
- Parallel calls starve the system model. Everything runs sequentially, behind a lock.

And four prompt rules, A/B tested with real calls against this binary:

- Never say "write the file." That framing produced a markdown fence every single time. What stuck is *Write one JavaScript function with this exact signature.*
- Never put a worked code example in the system prompt. It copies the terse style and returns confidently wrong one-liners — the Pong failure above.
- Never use angle-bracket placeholders. It copies them into the output literally.
- **Write each contract rule as an executable expression, not a concept.** Two phrasings of one rule:

| Phrasing | Score |
|---|---|
| `if current.x + input.x === 0 AND current.y + input.y === 0` | 4/4 |
| "if input points the opposite way" | 0/4 |

The difference is whether the sentence can be transcribed or has to be understood. It cannot turn a description into a predicate, and has no trouble turning a predicate into code. Do that translation yourself — and hold on to the rule, because it eats the project.

## The design

Snake. Integer grid, no floating point, every rule a pure function: every unit has a checkable oracle and nothing needs a tolerance.

I started with 8 units and decomposed to 13, because the eslint complexity gate is set to 5 and two of the originals could not meet it: `placeFood` split into `freeCells` + `pickCell`, `step` into `isDead` + `advance` + `step`. The function this model gets right in one shot is smaller than the one you would naturally write.

Each unit gets a frozen contract file with fixed sections — SIGNATURE, DESCRIPTION, EXAMPLES, TYPES, BEHAVIOUR, CASES, DOMAIN, HINT, FALLBACK — and the trick is **blind dual generation**:

- The implementation call reads only SIGNATURE + DESCRIPTION + EXAMPLES.
- The test call reads only SIGNATURE + TYPES + BEHAVIOUR + CASES.
- Neither sees the other's output. Neither ever sees HINT or FALLBACK.

Four gate steps then run over the assembled suite: `node --test`, eslint complexity ≤ 5, coverage, Stryker mutation. A failure condenses into a repair prompt for the failing unit. Tests freeze once accepted; after that only the implementation may be repaired, or the loop converges on deleting the assertion that hurts.

Thirteen build steps, resumable through a `.build/state` ledger. `ALLOW_FALLBACK` defaults to 0, and any fallback used prints `the unit <fn> comes from the contract FALLBACK block. The model did not write it.`

One toolchain note: on Node 24, `node --test test/` dies with MODULE_NOT_FOUND and reports a bogus failing test named `test`. Use the quoted glob `node --test "test/**/*.test.mjs"`.

## The scorecard

`./build.sh --clean`, re-verified by running the commands, not by reading the build's own summary:

- Exit 0. 32 model calls. Nine minutes thirty-three seconds of wall clock.
- 31 of the 32 calls landed on the first attempt; one test call returned a syntax error that `node --check` refused.
- 0 gate repairs, 0 contract fallbacks, 82 unit tests, 82 pass, 0 fail.
- Coverage LINE 100.00 / BRANCH 100.00, mutation score 98.44 against a threshold of 80, eslint clean at complexity max 5.
- A plain re-run exits 0 in 0.143 seconds: the ledger works.
- In real headless Chrome 153, the canvas reads back as exactly 800 `#33ee66` pixels and 400 `#ee3333` — two snake cells and one food cell at 20px.

`build.sh` is 1891 lines, `lib/` another 1049, `tools/` 470.

That is the list I would have put at the top of a README and felt good about. I was ready to write a post about how well it worked. Then I had it reviewed.

## The bug the scorecard cannot see

The shipped game had the classic tail off-by-one. The death test ran against the **pre-move** body, so the snake died entering the cell its own tail was vacating that tick.

Reproduction:

```
body [{1,1},{2,1},{3,1},{3,2},{1,2}], dir 'left', step(state, 'down')
-> over === true        // correct Snake gives over === false
```

Over 500 autoplayed games on a 12x12 grid, **37 of 500 deaths (7.4%) were spurious tail deaths**. Worse for a human, because following your own tail is standard Snake technique.

It survived 78 passing tests, 100% coverage and a 98.39% mutation score. (Those are the pre-fix numbers; the 82 and 98.44 above are the build after the contract was corrected.)

The bug was in the **contract**. The implementation implemented the wrong rule, the blind tests asserted the wrong rule and passed, and the mutants that would have exposed it were killed by tests defending the wrong behaviour. Blind dual generation protects you against an implementation and a test agreeing on a mistake *they* made. It gives you nothing when they agree on one they both inherited.

Mutation testing proves your tests are sensitive to changes in your code. It can never prove your code does the right thing. No mutation score catches a wrong oracle.

The fix had to land in the contract, not in `src/`, or the next `--clean` regenerates the bug. The corrected `isDead` computes the post-move body and tests the head against the survivors:

```js
export function isDead(head, state) {
  const ate = samePos(head, state.food);
  const rest = growOrMove(state.body, head, ate).slice(1);
  return hitsWall(head, state.w, state.h) || hitsSelf(head, rest);
}
```

Correct in both directions: entering the vacating tail cell is safe, and eating into the tail cell, where the tail stays put because the body grew, is still death.

## A green build behind a blank page

The documented serve command served the `web/` directory. `web/game.js` imports `../src/core.js`, so `/src/core.js` returned 404 and the page never loaded. Every number in the scorecard above, and a blank screen.

The gate meant to catch it probed 3 of 14 modules. The review hid `src/turn.js` and it still reported every core module answering 200. It now derives its probe list from the import graph, and the build log reads `16 files of the served game answer 200 over HTTP`. Separately, `eslint.web.mjs` declared no `no-undef` rule, so its "no undefined global" claim was worthless.

Two more, reproduced rather than theorised. `freeCells` used `new Set(occupied.map(...)).has({x, y})`. `Set.has` compares objects by **reference**, so it always returned false, `freeCells` returned every cell including the occupied ones, and food could spawn on the snake. The contract stated the value-equality rule in plain prose and the model erred anyway. That contract now says `Write no Set. Write no Map. Write no includes.`

And `set +e` inside the `ERR` trap disabled errexit for the whole process, so the first failure printed `the build stopped` and then the build carried on and exited 0.

## Limitations, counted honestly

**The executable-expression rule ate the contracts.** Apply *write the rule as an expression, not a concept* consistently and the spec starts to contain its own answer. The thirteen as they stand:

- **Six hand the model a copyable implementation.** `pickCell`'s DESCRIPTION reads *Write this line first: `if (free.length === 0) return null;`* and carries on for four lines. `freeCells` gives both of its expressions verbatim. Four more — `placeFood`, `isDead`, `advance`, `step` — pair a SKELETON of `???` holes with a HOLES block supplying every hole.
- **Five state the key expression inside the prose.** `hitsWall` rule 3 is *Return true when pos.x < 0 || pos.y < 0 || pos.x >= w || pos.y >= h.* The model assembles a function around it and derives nothing.
- **Two carry no copyable expression**, and both came back in a form I had not written: `turn` used `['up', 'down', 'left', 'right'].includes(input)` where my hidden FALLBACK used `OPP[input] ? input : current`, and `hitsSelf` came back as an indexed `for` loop.

So "the model wrote every unit" is literally true, and the word doing the work is *wrote*. Two of thirteen are generation in the sense anyone means it. Six are a slow, expensive copy-paste.

**The CASES table is a human-written oracle.** The cross-check is contract-versus-implementation, not test-versus-implementation. PLAN.md section 2.4 says so outright, and the tail bug is what that limitation looks like when it bites.

**`tools/derive.mjs`**, the pass that strengthens tests after mutation, takes its expected value from `src/<unit>.js` rather than from the contract. It is the one place in the pipeline that is not blind. It never fired in this build — mutation passed at 98.44, so no strengthen tests exist — but the weakness is architectural, and documented rather than fixed.

**`gate_unit` and `gate_coverage` pass vacuously in isolation on an empty suite**: `node --test` exits 0 on an empty glob, and the coverage table reports 100% when it loaded no files. In the real pipeline a frozen-checksum guard catches this and the build exits 1, so it is a defence-in-depth weakness, not a shipped hole. I first wrote it up as a shipped hole and was wrong.

And `build.sh` is more shell than anyone should maintain. There is no restart without a page reload.

## What the review got right, and what I got wrong

The harness was built and then adversarially reviewed by a multi-agent pipeline: probe, design, author, execute, five review lenses, per-finding refutation, repair. 57 agents, 717 tool uses, 83 minutes. I did not find the tail bug, the serve bug, the `Set.has` bug or the trap bug. The review did, and several of its findings were refuted as unreachable, which is the filter working.

Two of my own conclusions were refuted the same way: the empty-suite claim above, which the pipeline guard already catches, and a reported blank-canvas regression, where the screenshot tool was at fault. Both corrections came from running something. So did the tail bug: no gate found it, and the numbers never moved.

A wrong oracle is invisible to every tool that measures agreement, and coverage, mutation and a passing suite all measure agreement. Point all three at a wrong specification and all three certify it, in green, in under ten minutes. The only thing that sized mine was playing 500 games and counting the deaths.

Every layer here verifies the layer below it — coverage that tests reach the code, mutation that tests are sensitive to it, blind dual generation that implementation and test agree without collusion. Stack them high enough and the numbers feel like proof.

They only ever verify *downward*. Nothing in the tower looks up at the sentence everything was derived from and asks whether that sentence describes the game anyone wanted to play.
