# Council Notes: proposal.md

## Author Summary
The proposal states the why (prototypes pay the full pipeline price),
the activation through the `fast:` prefix, the reduced flow, the
per-run debt issue, and the impact set. The author round widened the
impact set and closed two claims. The reviewer round tightened the
sentence shapes and closed the file list.

## Reviewer Challenges
- The draft claimed "no code module" while the confirmed classifier
  gap forces one small `tools/process_issues` change.
- "Trigger words in the description" was ambiguous. The decision is
  one prefix.
- The label situation was unstated in scope.
- The keep-set sentence ran 27 words with a four-word noun stack.
- The debt-issue paragraph read as one total item instead of one item
  per skip.
- The impact list omitted `adr/0016`.

## Resolutions
- Accepted: the impact set names the classifier rule, its README
  line, and its unit test. "Trigger words" became the `fast:` prefix.
  The out-of-scope list carries the label line. The keep-set sentence
  split, with "local suite run" everywhere. The per-item sentence
  split. The governed-capability rule joined the flow section. The
  ADR line joined the impact list.
- Rejected: none.
- Deferred: none.

## Remaining Risks
- The proposal merge gate runs the classifier change through the CI
  mutation gate. The local gate run in task 6.2 covers it.
