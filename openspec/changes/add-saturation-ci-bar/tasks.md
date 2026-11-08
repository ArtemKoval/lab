# Tasks: add-saturation-ci-bar

## 1 Workflow and pin

- [ ] 1.1 Remove the exit-3 score resolution from the CI mutator step
  in `.github/workflows/tests.yml`. The step drops the tee, the
  `PIPESTATUS` plumbing, and both comments, and becomes a bare
  invocation whose replacement comment names the saturation bar.
- [ ] 1.2 Update the workflow contract pin in
  `tests/claude_infra/test_ci_workflow.py`: the `s + 0 >= 95.0`
  assertion and the `/tmp/mutation.log` assertion leave, the direct
  invocation stays, negative pins assert the two strings are gone,
  and the pin comment names the bar.

## 2 Spec and docs

- [ ] 2.1 Edit the Purpose sentence of
  `openspec/specs/quality-gates/spec.md` from the 95 percent floor to
  the saturation bar.
- [ ] 2.2 Update the feature-pipeline skill's mutation gate line from
  the score floor to the saturation bar.
- [ ] 2.3 Update the harness charter's quality-gates line in
  `.claude/hooks/charter.md` from the score floor to the saturation
  bar. The path is protected, and the pull request carries the
  marker.
- [ ] 2.4 Run `python -m dspy_gate regen add-saturation-ci-bar` and
  carry the regenerated `openspec/eval_manifest.json` into the
  implementation pull request. Never hand edit it.
- [ ] 2.5 Run `openspec validate add-saturation-ci-bar --type change
  --strict`, the STE scan on the change artifacts, the full hermetic
  suite, and the gates on the changed paths.
