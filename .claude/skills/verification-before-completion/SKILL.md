---
name: verification-before-completion
description: Use when you want to claim that work is complete, fixed, or passing, before you commit, push, or open a pull request, or before you trust an agent success report - run the proof command fresh, read its full output, and state the claim only with evidence.
metadata:
  ported:
    from: obra/superpowers
    commit: 2ce8aa15d05bd57213e6f746f953aafb7ded7a8b
    license: MIT
---

# Verification Before Completion

Use the repository's own test, lint, and build commands. Run them yourself. An earlier run is not evidence.

## Principle

Evidence comes before claims. Always.

**No completion claim without fresh verification evidence.** If you did not run the proof command in the current session, you cannot claim that it passes.

A breach of the letter of this rule is a breach of its spirit.

## The gate

Before you claim a status, do these steps in this order:

1. **Identify**: select the command that proves the claim.
2. **Run**: run the full command, fresh and complete.
3. **Read**: read the full output. Examine the exit code. Count the failures.
4. **Compare**: does the output confirm the claim? If no, state the true status with the evidence. If yes, state the claim with the evidence.
5. **Claim**: only then make the claim.

A skipped step is a false report, not a verification.

## Claims and evidence

| Claim | Requires | Not enough |
|-------|----------|------------|
| Tests pass | Test output with 0 failures | A previous run, "should pass" |
| Linter clean | Linter output with 0 errors | A partial run, an extrapolation |
| Build succeeds | Build command with exit code 0 | A clean linter, logs that look good |
| Bug fixed | A test of the original symptom passes | Changed code, an assumption |
| Regression test works | The red-green cycle below | One passing run |
| Agent finished | The VCS diff shows the changes | An agent report of success |
| Requirements met | A line-by-line checklist | Passing tests |

## Red flags: stop

- You use the words "should", "probably", or "seems to".
- You show satisfaction before verification: "Great", "Perfect", "Done".
- You want to commit, push, or open a pull request without verification.
- You trust a success report from an agent.
- You accept a partial verification as proof.
- You think "just this once".
- You feel tired and want the work to end.
- Your wording implies success before you ran the proof command.

## Rationalizations

| Excuse | Reality |
|--------|---------|
| "It should work now." | Run the proof command. |
| "I am confident." | Confidence is not evidence. |
| "Just this once." | The rule has no exceptions. |
| "The linter passed." | A linter is not a compiler. |
| "The agent reported success." | Confirm it yourself. |
| "I am tired." | Exhaustion is not an excuse. |
| "A partial run is enough." | A partial run proves nothing. |
| "I used other words, so the rule does not apply." | The spirit rules over the letter. |

## Regression tests

A regression test is real only after this red-green cycle:

1. Write one test for the fixed bug.
2. Run the test and see it pass.
3. Revert the fix.
4. Run the test again and see it fail.
5. Restore the fix.
6. Run the test again and see it pass.

The fail step proves that the test finds the bug. A test with no fail step is not evidence. For new code, the test-driven-development skill owns the red-green cycle. The cycle above is its regression variant.

## Patterns

**Tests**

```
Pass: run the test command and see 34/34 pass. Then say "All tests pass".
Fail: say "It should pass now" or "The code looks correct".
```

**Build**

```
Pass: run the build and see exit code 0. Then say "The build passes".
Fail: say "The linter passed". A linter does not examine compilation.
```

**Requirements**

```
Pass: read the plan again. Make a checklist. Confirm each item. Report the gaps or the completion.
Fail: say "Tests pass, so this phase is complete".
```

**Agent delegation**

```
Pass: the agent reports success. Examine the VCS diff. Confirm the changes. Report the true state.
Fail: trust the agent report.
```

## When to apply

Apply the gate before:

- Any claim of success or completion.
- Any expression of satisfaction.
- Any positive statement about the state of the work.
- A commit, a push, a pull request, or a report of task completion.
- A move to the next task.
- Delegation to an agent.

The rule covers exact phrases, paraphrases, synonyms, and implications of success. It covers any message that suggests completion or correctness.

## Boundary with verify-change

This skill governs every success claim during a run. The verify-change skill verifies a finished change against its OpenSpec artifacts on demand. Neither skill replaces the other.
