## 1. Delta gates

- [ ] 1.1 Run `openspec validate fix-strict-spec-validate-failures
      --type change --strict` and hold it green.
- [ ] 1.2 Run `tools/spec_ste_check` on the change text and hold it
      clean.

## 2. Apply

- [ ] 2.1 Add one test for the lock-order scenario in
      `tests/process_issues/`, beside the refusal test.
- [ ] 2.2 Replace the placeholder Purpose in
      `openspec/specs/saturation-pass/spec.md` with the real Purpose
      through a direct edit.
- [ ] 2.3 Run the full hermetic suite with the shared venv
      interpreter and hold it green.
- [ ] 2.4 Tick each task in this file as the work lands.

## 3. Archive gates

- [ ] 3.1 Run `openspec validate --all --type spec --strict` before
      the archive step and hold 0 failed.
