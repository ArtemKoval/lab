# Council Notes: tasks.md

## Author Summary
The tasks cover the skill text, the template, the CLAUDE.md line, the
ADR, the guard tests, the classifier rule with its unit test, and the
delivery gates. The reviewer round split the over-long procedural
sentences and named the template sections one by one.

## Reviewer Challenges
- Task 5.2 (now 5.3) hid a confirmed break behind an "examine and
  extend" conditional.
- The guard-test task missed the CLAUDE.md pin, the frontmatter pin,
  and the title-prefix pin.
- The template task missed the frontmatter label, the Telemetry
  section, and the unmerged-PR close note.
- The gate task named only the suite and ruff while the changed tool
  path pulls the quality gates.
- Procedural sentences ran above the 20-word limit.

## Resolutions
- Accepted: the classifier task states the known break and the exact
  rule, split into three tasks. The guard tasks pin every rule
  sentence, every template section, the frontmatter, and the
  Workflow line. The template tasks name the label, the four
  sections, and the close note. The gate task names the three quality
  gates on the changed path.
- Rejected: none.
- Deferred: none.

## Remaining Risks
- The mutation gate run on the classifier path takes minutes. The
  task order runs it once, before the push.
