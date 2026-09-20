# Prompt files

This directory holds the system prompts and the user templates that build.sh gives to /usr/bin/fm.
Each system prompt is the measured winner of an A/B probe. Do not edit a system prompt without a new probe.

## The two file convention

Each prompt role uses two files. The file boundary is the delimiter.

- `<role>.md` holds the SYSTEM prompt. build.sh gives it to `fm respond -i`.
- `<role>.user.md` holds the USER template. build.sh fills the `{{NAME}}` holes and gives the
  result to fm on stdin.

A harness extracts a template with a plain file read. A harness fills a hole with a literal text
replacement of `{{NAME}}`. No other markup is present in a template file.

## Files

| File | Role | Measured cost |
| --- | --- | --- |
| impl.md | system prompt for a leaf function from a contract | 165 tokens |
| impl.user.md | user template for impl.md | 19 tokens empty, contract dependent |
| skeleton.md | system prompt for a function with holes | 54 tokens |
| skeleton.user.md | user template for skeleton.md | 68 tokens empty, contract dependent |
| test.md | system prompt for a node:test file | 281 tokens |
| test.user.md | user template for test.md | 34 tokens empty, contract dependent |
| repair.md | system prompt for a repair | 150 tokens |
| repair.user.md | user template for repair.md, format D | 53 tokens empty, 165 to 700 tokens filled |
| strengthen.md | system prompt for mutant kill tests | 33 tokens |
| strengthen.user.md | user template for strengthen.md | 76 tokens empty, plus 46 tokens for each FILL |
| render.md | system prompt for one browser function | 24 tokens |
| render.user.md | user template for render.md | 55 tokens empty, 174 to 272 tokens filled |
| html.md | system prompt for web/index.html | 24 tokens |
| html.user.md | user prompt for web/index.html | 184 tokens |

A token count comes from `fm count-tokens -q "$(cat <file>)"` on macOS 27.0 build 26A428.
The context window holds about 4096 tokens for the input and the output together.
Keep each assembled prompt at 1200 tokens or less.

## Rules that the probes measured

1. Never add a global object equality rule to impl.md. It repairs placeFood but it breaks turn and
   growOrMove. Put an equality hint in the one contract that needs it.
2. Never put a worked code example in a system prompt. The model copies the terse style and writes
   wrong one line logic.
3. Never use an angle bracket placeholder in a system prompt. The model copies it into the output.
4. Never say "write the file". That framing gives a markdown fence every time. Say "Write one
   JavaScript function with this exact signature:".
5. Never mix English with JavaScript in one instruction line. The model copies the English into the
   function body.
6. Never put a ??? hole inside a ternary. Put the whole ternary in the hole.
7. The CASES table is the oracle. The model transcribes it and never checks it. The contract author
   writes and verifies every expected value.
8. -g is byte deterministic. A retry with the same prompt gives the same answer. A repair must change
   the prompt text.
9. Run every fm call one after another. Parallel calls starve the system model.
10. The exit code is not a signal. Judge the text by execution.
11. The render prompt can put a const at module scope, outside the function. Cut the raw output by
    line, not by character, or the normaliser deletes that const. See the note below.

## Smoke test results

A smoke test of this directory ran on 2026-09-20 against /usr/bin/fm.

| Prompt pair | Unit | Assembled tokens | Result |
| --- | --- | --- | --- |
| impl.md | hitsWall | 317 | 129 bytes, no fence, starts with "export function" |
| test.md | hitsWall | 648 | 9 test blocks, correct 3 import lines, no fence |
| skeleton.md | isDead | 167 | one line, holes copied exactly |
| render.md | keyToInput | 194 | 8 keys mapped, unmapped key gives null |

The generated hitsWall implementation and the generated hitsWall tests ran together.
`node --test "test/**/*.test.mjs"` gave 9 pass, 0 fail, exit 0.

### Note on the render normaliser

The keyToInput smoke put `const MAP = {...}` at module scope, before the function keyword.
A character cut at the first `function keyToInput(` removes that const.
The cut file then throws `ReferenceError: MAP is not defined` at run time.
A line cut keeps the const, because the model wrote the const and the function on one line.
Step 10 of build.sh must keep every line before the function, or it must gate the file with
`node tools/drive.mjs`.
