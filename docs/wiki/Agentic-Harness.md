# The agentic harness

The harness is the system around the agents that build the product. The
full text lives in [HARNESS.md](../../HARNESS.md); this page shows the
three phases with their artifacts.

## Inception: intent to units of work

One request becomes one OpenSpec change under `openspec/changes/`, with the
proposal, the design, the spec delta, and the task list. Each task line is
one unit of work, and `tools/plan_exec` extracts one brief per unit and
keeps an append-only ledger. The proposal pull request merges to main
before any implementation starts, and the review agents attack the proposal
before that merge.

## Construction: the flow per unit

1. Extract the brief with `tools/plan_exec`.
2. Write the test first, and see it fail.
3. Write the smallest code that passes.
4. Run the gates: coverage, complexity, mutation, duplication.
5. Commit one atomic change.
6. Tick the task, and append the ledger line.

The `library-uow` slash command encodes the flow
(`.claude/commands/library-uow.md`), and the `senior-dev` and `senior-qa`
agents own implementation and acceptance. The whole-diff review runs on the
pull request before the merge, and every finding gets a verification
against the code.

## Observability: what the run tracks

| Signal | Where it lives |
| --- | --- |
| Every tool call and permission event | `.cc_logging/`, from the hook |
| The execution ledger per unit | `.plan_exec/` beside the change |
| Coverage, complexity, mutation, duplication | the gate tools |
| Spec conformance | `openspec validate --strict`, the STE gate |
| Product accuracy | the runs, the evaluations, the scoreboard |
| Handover telemetry | one block per handover issue |

## The video

The one-minute tour: [factory.mp4](../videos/factory.mp4), rendered by
`tools/slidecast` from [its deck](../videos/decks/factory.json).
