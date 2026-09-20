# A Big Model Built the Cage. A Small One Built the Game.

*Opus designed the harness. Apple's on-device model — the one hidden at /usr/bin/fm in macOS 27 — did every line of the actual coding, one tiny function at a time.*

The division of labor was strict. Opus never wrote a single line of the game. It designed contracts, a blind-generation protocol, and four verification gates. Apple's on-device model executed inside that structure, and nothing it produced was trusted until something else proved it.

## Why the small model needed a cage

`/usr/bin/fm` has a context window of about 4096 tokens, total — input and output combined, measured by bisection. And left alone, it writes confident stubs: asked for a Pong module, it returned three functions that parse, lint, and do nothing — one nudges a coordinate, another flips a sign, neither touches a paddle or a wall.

That ruled out "point it at the spec and let it write the game." So Opus's job became architecture, not code: decompose Snake into 13 pure functions small enough that a stub would be obviously a stub, then build a structure where the model's output was never trusted, only verified.

## The harness Opus designed

Each function gets a frozen contract — signature, description, worked examples, a table of input-to-output cases. Then **blind dual generation**: one call to the on-device model writes the implementation, reading only the description and examples. A separate call writes the unit tests, reading only the types and cases. Neither call sees the other's output.

Four gates run over what comes back: unit tests, eslint complexity, coverage, Stryker mutation testing. A failure condenses into a repair prompt and goes back to the model — never fixed by hand. Opus's contribution was entirely upstream of the code: the constraints, the blindness, the gates, the repair loop. Every byte of `src/` and `test/` came from the small model executing inside that frame.

The result: 32 calls to the on-device model, zero contract fallbacks, 82 passing tests, 100% coverage, a 98.44% mutation score, all in under ten minutes.

## Where the architect's own plan had a bug

The scorecard was clean. The game was not. The snake died entering a cell its own tail was vacating that same tick — the classic Snake off-by-one — and it survived every gate, because the flaw wasn't in what the implementer wrote. It was in the contract Opus handed it. The implementation correctly implemented the wrong rule; the blind tests correctly asserted the wrong rule; the mutants that would have exposed it were killed by tests defending the wrong behaviour.

The small model had done its job perfectly. The cage itself was wrong.

## What actually caught it

Not the harness. A second, separate structure — five adversarial review lenses, each finding independently refuted or confirmed before anything got repaired — also designed and run by Opus, but sitting outside the build pipeline rather than inside it. That's what found the tail bug, a serve-path defect that left a perfectly-tested page blank, and a reference-equality bug that let food spawn inside the snake.

## The actual finding

This wasn't a test of whether a 4-billion-token-starved on-device model can code. It was a test of whether a frontier model can build a structure precise enough that a tiny, heavily constrained one can produce verified, working software inside it — and whether that same structure can catch its own architect's mistakes.

It mostly could. The harness got the implementer to write correct, tested code under real constraints, with zero human-written lines in `src/` or `test/`. But the harness could only verify *downward*, from tests toward code. It took a second, independent pass to verify *upward* — to ask whether the sentence everything was built from was actually true.

*Full write-up, with the measured prompt rules and an honest count of how much of "the model wrote every unit" was generation versus dictation: see BLOGPOST.md.*
