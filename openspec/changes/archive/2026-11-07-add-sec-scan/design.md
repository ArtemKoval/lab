# Design: add-sec-scan

## Source

Issue #49: "Create Sec Scan Skill — to scan repo for the possibly exposed keys
and secrets, and automatically revoke them."

## Plan review

One scoping decision was made at Step 0 and carried: revocation is destructive
and provider-gated, so it runs only behind `--revoke`, prefers disabling over
deleting (recoverable), and works only for OpenRouter — the provider this repo
actually carries keys for. AWS and GitHub findings print their exact manual
revoke commands instead. The memory lesson on fixture secrets drove the test
design: fixture secrets are assembled at test time from concatenated fragments,
so no literal provider-shaped string ever lands in the repository for push
protection to block.

## Key decisions

- Stdlib only, one module with a CLI, on the house tool pattern
  (`tools/sec_scan/sec_scan.py`, `--json` for machine output, exit 0/2).
- Pattern matching over provider shapes, plus a Shannon-entropy examination
  of assignments to credential-looking names. Entropy alone is reported as
  "suspected", never as a confirmed provider key.
- `--history` walks `git log -p` and reports commit and path. It is opt-in
  because full history on this repo is bounded but slow.
- Revocation: OpenRouter provisioning API disable (recoverable) behind
  `--revoke` and a provisioning key. Every other provider prints its manual
  command. Without `--revoke`: no network call at all.
- A skipped-path set mirrors the tree walk's ignore of vendored and dependency
  directories, so a decoy in node_modules never fires.

## Failure modes

- A false positive on a test fixture: the report says "suspected" for entropy
  hits, and the memory lesson keeps provider-shaped literals out of the tree.
- The provisioning API is unreachable: the revoke step reports the failure and
  exits 2 with the manual command alongside.
