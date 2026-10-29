# The harness

From the head of operations, with the IT team.

## Where this is going

The cases get harder to decide. Decisions follow the manual as well as the
wording, and new cases bring more documents, more rules to weigh, and more
to look up. The agent grows into that work: it takes on longer jobs, works
through them on its own, and deals with problems without help.

## What the harness does

1. One run works the whole queue. The team starts the agent once, and it
   works every waiting case in an order it chooses, then finishes with a
   short summary. A run can take a cap, for a cheap trial on a few cases.
   The agent can also work one named case.
2. A to-do list the team can watch. The agent plans each run as a to-do
   list and keeps it up to date, with each item to do, in progress, done,
   or left for a worker. The queue page shows the list.
3. A fresh helper for each case. The queue agent hands each case to a
   subagent that works that one case from a clean start and reports one
   line: the decision and the award, or what went wrong. Every step still
   lands on its case.
4. The documents, read the way a worker reads them. For each case the agent
   finds and reads the sections of the wording and the manual it needs,
   rather than whole documents. The case page shows what it read.
5. Problems put right automatically. One bad case never stops the run or
   leaves a case stuck in progress. A case that fails goes back to waiting
   for one more try. A case that fails twice is left for a worker. No case
   is decided or paid twice. Before it finishes, the run checks for a
   waiting case it missed within its cap.
6. The model. The default is DeepSeek V4.1 Flash on OpenRouter with low
   reasoning effort. `MODEL_NAME` overrides it.
7. Instructions the team can read. The instructions page shows the queue
   instructions and the case instructions.

## What stays the same

- The rules in `docs/BRIEF.md`, including sign-off on awards over the limit.
- The stack in `docs/TECH_STACK.md`. The harness builds on the agent
  framework the stack names, and adds no second framework.
- Tests never call a model, and the code stays simple.
