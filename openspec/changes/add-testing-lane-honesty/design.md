# Design: add-testing-lane-honesty

## Plan review

The review kept the report proposal as the plan. ASIT: Unification.
The e2e marks and the gates exist, and the rules extend their reading.
No new component enters the repository.

Alternatives the review rejected:

- A lane registry tool that tracks lanes and their skips. The lab runs
  two lanes today (the hermetic suite and the opt-in e2e marks), and a
  registry earns nothing at this scale.
- A hook that fails a pull request with a skipped lane. The rule
  governs the pipeline author, and the guard test holds the text. A
  hook would need the pull request body at test time, and the
  gate-integrity surface grows for no defect.
- A retrofit that back-fills lifecycle tables for existing tools. The
  report scopes the rules to new and touched code through the
  pipeline.

## The rule texts

Step 3 gains, after the e2e bullet:

- A skipped test lane implies no coverage. The pull request body names
  each lane the run skipped.

Step 9 gains, after the quality-gates paragraph:

- A change to code with cleanup, cancellation, or ownership behavior
  lists its lifecycle scenarios: success, cleanup failure, cancellation
  mid-run, and partial completion. Each scenario names the test that
  holds it.

## Edge cases

- A run with no skips names none, and the body carries no lane list.
  The rule binds the body that names a skip, and a run without skips
  stays silent.
- A lifecycle-risky change whose scenarios live in existing tests
  lists the existing tests by name. The rule asks for the list, not
  for new tests.
- The rule does not redefine the e2e marks or the env gates. The
  marks stay, and the rule names their meaning.

## Verification

`tests/claude_infra/test_pipeline_rules.py` gains one guard test with
one assertion per rule sentence, on the collapsed skill text. A
removal fails the suite.
