# Tasks: add-devops-chaos-ssh

## 1. Planning

- [x] 1.1 Record the phase analysis, the failure catalog, and the
      teaching pairs in design.md.
- [x] 1.2 Record the environment model, the injection and scratch
      mechanics, and the tutor flow in design.md.
- [x] 1.3 Carry the spec delta for the six requirements of the
      `devops-chaos-ssh` capability.

## 2. Spec and delivery

- [x] 2.1 Pass the strict validate, the STE gate, and the builder
      review.
- [x] 2.2 Commit, push, open the proposal pull request with the
      `Refs #216` line, and merge it.
- [x] 2.3 Post the spec references on issue 216 and add the
      `waiting-human-approval` label.

## 3. Environment (apply)

- [x] 3.1 Write the Dockerfile and the `devcontainer.json` with the
      pinned `appPort`, the `NET_ADMIN` run argument, and the decoy
      sshd setup.
- [x] 3.2 Write the injection scripts for the scenarios that define
      one under `environments/inject/`.
- [x] 3.3 Boot the environment with the devcontainer CLI, and run one
      injection against the built image.

## 4. Catalog and tutor (apply)

- [x] 4.1 Write the 13 catalog JSON files with the shape from
      design.md.
- [x] 4.2 Implement the `chaos_ssh` package: the loader, the five
      subcommands, the scratch state, and the exit contract.
- [x] 4.3 Write the catalog loader as data-driven code with no
      scenario names in the module.

## 5. Tests and gates (apply)

- [x] 5.1 Write the hermetic unit suite with the faked container
      boundary: the catalog parse, the five subcommands, the exit
      contract, the hint order, and the scratch path rules.
- [x] 5.2 Write the opt-in e2e lane behind `DEVOPS_CHAOS_SSH_E2E=1`,
      and run it once against the real stack.
- [x] 5.3 Run the full hermetic suite, crapper at 10, dryer at 0.8,
      and the mutator with no survivors on the new package. Widen the
      gated-path regex, the coverage `--source` list, and the dryer
      and mutator filters of the protected workflow to the new
      prefix, so the gates reach the package in CI.
- [x] 5.4 Examine the `kex-mismatch` scenario against the built image,
      and land either the KEX form or the host-key-type pivot from
      design.md.

## 6. Docs (apply)

- [x] 6.1 Write `devops/chaos/ssh/README.md`: the commands, the safety
      rules, the `sg docker` note, and the port override note.
- [x] 6.2 Add the `devops/chaos/ssh` entry to the Projects section of
      `CLAUDE.md`.

## 7. Review and merge (apply)

- [x] 7.1 Run `sec-scan --diff` on the staged diff.
- [ ] 7.2 Give the whole diff one adversarial review. Fix the
      confirmed findings. Re-run the suite and the gates.
- [ ] 7.3 Open the implementation pull request with the test plan and
      merge it green.
