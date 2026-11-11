# Tasks: improve-session-statusline

## 1. Render change, test first

- [ ] 1.1 Write the failing tests for all seven table rows and the mapped `--json` value
- [ ] 1.2 Write the failing tests for the unknown, mixed-case, and absent levels
- [ ] 1.3 Write the failing tests for the separator, the degraded separator, and the no-model payload
- [ ] 1.4 Implement the table and the lookup helper in `session_statusline.py`. Apply the lookup in the render.
- [ ] 1.5 Keep an absent effort at `n/a`. Pass unknown and non-string levels raw.
- [ ] 1.6 Join the render blocks with ` | `. Join the degraded fields behind the fault prefix.
- [ ] 1.7 Examine the under-100 pin against the new worst case. Pin the exact standard line at 91 characters.

## 2. Verification

- [ ] 2.1 Run the session_statusline test file and drive it green
- [ ] 2.2 Run the full hermetic suite and the Claude infra contract tests
- [ ] 2.3 Run crapper at threshold 10 on the changed code. Run dryer at threshold 0.8. Run the mutator with no survivors. Measure branch coverage of the changed lines.
- [ ] 2.4 Run the tool with the observed payload shape. Record the before and after lines.
- [ ] 2.5 Run `openspec validate improve-session-statusline --type change --strict`

## 3. Docs

- [ ] 3.1 Update `tools/session_statusline/README.md`: new line example, the mapping table, and a limits row with the doc date
- [ ] 3.2 Update the `tools/session_statusline` entry in `CLAUDE.md` to say the line carries the z.ai-mapped effort

## 4. Review and merge

- [ ] 4.1 Run `sec-scan --diff` on the staged diff
- [ ] 4.2 Give the whole diff one adversarial review. Fix the confirmed findings. Re-run the suite and the gates.
- [ ] 4.3 Open the implementation pull request with the test plan and merge it green
