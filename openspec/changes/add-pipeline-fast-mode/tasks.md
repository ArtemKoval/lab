# Tasks: add-pipeline-fast-mode

## 1. The skill text

- [x] 1.1 Add the Fast mode section to
      `.claude/skills/feature-pipeline/SKILL.md` after the intro,
      before the cross-cutting rules.
- [x] 1.2 Put the activation rule, the skip set with the applies
      rule, the keep set with the resync, the debt issue rule, the
      inline review rule, the Steps 4/6/7 rule, the handover rule,
      the governed-capability rule, and the peak-hours note in the
      section.
- [x] 1.3 Add the `fast:` prefix to the skill description
      frontmatter.

## 2. The debt template

- [x] 2.1 Add `.github/ISSUE_TEMPLATE/tech-debt.md` with the
      `name: Tech debt` frontmatter and the `tech-debt` label.
- [x] 2.2 Put the `## Task`, `## Telemetry`, `## Debt items`, and
      `## Follow-ups` sections in the house comment style, with the
      Write None convention.
- [x] 2.3 Add the close note to the `## Follow-ups` comment: close
      the issue when the pull request closes without a merge.

## 3. Docs

- [x] 3.1 Add the Workflow line `A \`fast:\` prefix run opens the
      debt issue instead of the handover issue.` to `CLAUDE.md`.

## 4. The ADR

- [x] 4.1 Add `adr/0016-fast-mode-delivery-contract.md` in the
      house custom style, with the rejected options in the Decision
      prose.

## 5. Tests and the classifier rule

- [x] 5.1 Add guard tests to
      `tests/claude_infra/test_pipeline_rules.py`, with one assertion
      per fast-mode rule sentence on the collapsed skill text.
- [x] 5.2 Pin the template sections, the `name: Tech debt`
      frontmatter, and the Workflow line in `CLAUDE.md` with one
      assertion each.
- [x] 5.3 Add the `tech-debt:` title-prefix skip to `classify` in
      `tools/process_issues/process_issues/core.py`, with the
      optional `title` keyword on the signature.
- [x] 5.4 Pin the rule with one unit test in
      `tests/process_issues/test_process_issues_core.py`.
- [x] 5.5 Add one line for the rule to
      `tools/process_issues/README.md`.

## 6. Spec and delivery

- [x] 6.1 Carry the delta-less declaration and pass the strict
      validate and the STE gate.
- [x] 6.2 Run the root suite, ruff, and the three quality gates on
      the changed classifier path.
- [ ] 6.3 Commit, push, open the pull request, and merge after
      review. The pull request body names the skipped lanes: none.
