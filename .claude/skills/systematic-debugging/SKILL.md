---
name: systematic-debugging
description: "Use when a test fails, a build breaks, production code gives an unexpected result, or you plan a fix before you know the cause: find the root cause first, then fix it with the four-phase process."
metadata:
  ported:
    from: obra/superpowers
    commit: 2ce8aa15d05bd57213e6f746f953aafb7ded7a8b
    license: MIT
---

# Systematic debugging

## Overview

Find the root cause before you fix anything. A fix that only hides the symptom is a failure. Every step in this process is necessary. Do not skip a step.

## The iron law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you did not complete Phase 1, you can not propose a fix.

## When to use

Use this skill for every technical problem:

- A test fails.
- Production code gives a wrong result.
- The system behaves in a way that you did not expect.
- Performance falls.
- A build breaks.
- Two components do not work together.

Use this skill especially in these cases:

- Time pressure makes a fast guess look safe.
- One small fix looks obvious.
- You already tried more than one fix, and the problem stayed.
- You do not fully understand the problem.

## The four phases

Finish each phase before you start the next phase.

### Phase 1: Root cause investigation

Do these steps before you propose any fix.

1. **Examine the error message.**
   - Read every word of the message. It often contains the solution.
   - Read the full stack trace. Note the file paths, the line numbers, and the error codes.
2. **Make the problem occur every time.**
   - Find the exact steps that produce the problem.
   - If you can not make it occur every time, gather more data. Do not guess.
3. **Examine the recent changes.**
   - Run `git diff` and read the recent commits.
   - Search them for new dependencies and config changes.
   - Compare the environment of the failure with the environment that works.
4. **Gather evidence in a multi-component system.**
   - A request can cross many components: a workflow, a build, a signing step, an API, a service, a database.
   - Before you propose a fix, add a log line at each boundary.
   - Log the data that enters and the data that exits at every boundary.
   - Make sure that the environment and the config reach every component.
   - Run the system once. The evidence shows the boundary that fails. Examine that component alone.

   Example of a system with three layers:

   ```bash
   # Layer 1: the workflow gives the secret to the build
   echo "IDENTITY: $([ -n "${IDENTITY:-}" ] && echo SET || echo UNSET)"

   # Layer 2: the build script sees the secret in its environment
   printenv IDENTITY >/dev/null 2>&1 && echo "IDENTITY in environment" || echo "IDENTITY not in environment"

   # Layer 3: the signing step runs with the secret
   codesign --sign "$IDENTITY" --verbose=4 "$APP"
   ```

   The output shows the boundary that fails. Here the secret is present in the workflow but absent in the build.
5. **Trace the data flow.** The error can appear far from the cause.
   - Ask where the bad value starts.
   - Ask what code passed that value.
   - Move one call up the stack. Continue until you find the source.
   - Fix at the source. Do not fix at the place where the error appears.

### Phase 2: Pattern analysis

Find the pattern before you fix.

1. **Find a case that works.**
   - Find similar code in this codebase that works.
2. **Read the reference in full.**
   - Read every line of the reference implementation. Do not read it quickly.
   - Understand the pattern before you apply it.
3. **List the differences.**
   - Write every difference between the case that works and the case that fails.
   - A small difference can matter. Do not remove an item from the list.
4. **Examine the dependencies.**
   - Which components, settings, and config values does the broken part use?
   - Which assumptions does it make?

### Phase 3: Hypothesis and testing

1. **State one hypothesis.**
   - Use this form: "X is the root cause because Y."
   - Record it. Be specific. Do not write a general sentence.
2. **Do the smallest test.**
   - Change one thing only. Make the smallest change that shows whether the hypothesis is true.
3. **Make sure before you continue.**
   - Did the change fix the problem? If yes, go to Phase 4.
   - If no, form a new hypothesis. Do not add more fixes on top of the first fix.
4. **Say what you do not know.**
   - Say "I do not understand X" when it is true.
   - Ask for help. Study the material again.

### Phase 4: Implementation

Fix the root cause. Do not fix the symptom.

1. **Create the failing test first.**
   - Write the smallest test that shows the problem. If there is no test framework, write a small script that shows the problem.
   - Use the `test-driven-development` skill. Its Red step is the gate. Run the test. Make sure that it fails because the behavior is missing, not because the test is broken.
2. **Make one fix.**
   - Fix the root cause that you identified in Phase 1. Make one change.
   - Do not bundle a "while I'm here" improvement. Do not bundle a refactor.
3. **Make sure that the fix works.**
   - Run the test. Then run the full suite. Make sure that no other test breaks.
   - Use the `verification-before-completion` skill before you claim success.
4. **If the fix does not work, stop.**
   - Count the fixes that you tried.
   - If the count is below 3, return to Phase 1. Use the new information.
   - If the count is 3 or more, go to step 5. Do not try a fourth fix before that discussion.
5. **If three fixes fail, question the architecture.**
   - Each fix shows new shared state or a new problem in a different place.
   - You must do a large refactor before you can apply the fix.
   - Each fix creates a new symptom somewhere else.

   Stop. Ask these questions:

   - Is this pattern correct at its base?
   - Do we keep it only from habit?
   - Is a refactor of the architecture better than more fixes for symptoms?

   Discuss with your human partner before you try more fixes. A third failure is not a wrong hypothesis. It is usually a wrong architecture.

## Red flags — return to Phase 1

Stop when you think one of these thoughts:

- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Add multiple changes, run tests"
- "Skip the test, I'll manually verify"
- "It's probably X, let me fix that"
- "I don't fully understand but this might work"
- "Pattern says X but I'll adapt it differently"
- "Here are the main problems: [lists fixes without investigation]"
- You list fixes before you trace the data flow.
- "One more fix attempt" when you already tried two fixes.
- Each fix shows a new problem in a different place.

Every item on this list means stop. Return to Phase 1.

If three or more fixes failed, question the architecture (Phase 4, step 5).

## Signals from your human partner

These lines show that you left the process:

- "Is that not happening?" — You assumed a state that you did not examine.
- "Will it show us...?" — You did not plan a way to see the data.
- "Stop guessing" — You propose fixes before you understand the cause.
- "Ultra-think this" — Examine the fundamentals, not only the symptoms.
- "We're stuck?" — Your approach does not work.

When you see one of these lines, stop. Return to Phase 1.

## Common rationalizations

| Excuse | Reality |
| --- | --- |
| "Issue is simple, don't need process" | Simple problems have root causes too. The process is fast for a simple bug. |
| "Emergency, no time for process" | The systematic path is faster than a cycle of random fixes. |
| "Just try this first, then investigate" | The first fix sets the pattern. Do it right from the start. |
| "I'll write test after confirming fix works" | A fix without a test is not proven. Write the test first. |
| "Multiple fixes at once saves time" | You can not isolate the fix that worked. The bundle adds new bugs. |
| "Reference too long, I'll adapt the pattern" | Partial understanding causes bugs. Read the reference in full. |
| "I see the problem, let me fix it" | A visible symptom is not a root cause. |
| "One more fix attempt" after 2+ failures | Three or more failures point to the architecture. Question the pattern. Do not fix again. |

## Quick reference

| Phase | Key activities | Exit condition |
| --- | --- | --- |
| 1. Root cause | Examine the errors, make the problem occur, examine the changes, gather evidence | You know what breaks and why |
| 2. Pattern | Find a case that works, compare the cases | You can list the differences |
| 3. Hypothesis | State one theory, do a small test | The theory holds, or you form a new one |
| 4. Implementation | Create the failing test, fix, make sure | The test passes and the suite is green |

## When the process finds no root cause

Sometimes the investigation shows a real external cause: the environment, timing, or another system. Record what you examined. Add a retry, a timeout, or a clear error message. Add logs for a later investigation.

But 95% of the "no root cause" results come from an incomplete investigation. Return to Phase 1 before you accept this result.

## Further reading

These techniques are part of this skill's method:

- `root-cause-tracing` — trace a bug backward through the call stack to the first trigger. Fix at that trigger.
- `defense-in-depth` — after you find the root cause, examine the data at every layer that it crosses. One examination point is not enough, because other code paths can miss it.
- `condition-based-waiting` — in a test, wait for the condition that you care about. Do not wait a fixed time.
