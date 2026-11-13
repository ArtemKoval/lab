# Council Notes: design.md

## Author Summary

The author drafted the five-phase analysis, the 13-scenario catalog
table, the container environment, the injection and scratch
mechanics, the tutor flow with the JSON catalog shape, the teaching
pairs, the out-of-scope list, and five open unknowns. The primary
agent supplied a binding correction to the environment model before
the review, and the review then challenged the corrected direction.

## Reviewer Challenges

- The wrong-port lesson would collide with the live decoy sshd on
  2223 and lose its refusal signature. The catalog must pin a dead
  port.
- The scratch bindings missed `GlobalKnownHostsFile` and the
  identity options, so the printed command could leak the real agent
  keys and the global known-hosts state into the practice runs.
- The no-agent-forwarding observable printed nothing on a plain
  login. The scenario needed the composed one-line command with the
  scratch agent and `-A`.
- The list scenario pinned the hard count 13, which would turn the
  KEX pivot into spec drift.
- The hard counts, the semicolons, the -ing verb forms, and the
  29-word sentence would fail the STE gate or hide from it.

## Resolutions

- Accepted: the wrong-port lesson pins dead port 2224, and the
  design states the reason.
- Accepted: the design names all five scratch bindings and the leak
  each one closes.
- Accepted: the design defines the composed one-line observable, and
  the spec scenario asserts the socket and pid paths inside the
  scratch directory.
- Accepted: the spec scenario counts rows per catalog file, with no
  hard count.
- Accepted: the primary agent repaired the prose, and the STE gate
  and the lint hold on the finals.

## Remaining Risks

- The KEX availability risk moves to apply time, and the pivot rule
  is written in design.md, so the apply run can land either form
  without a spec edit.
- The container build, the readiness wait, and the port collisions
  stay apply-time probes under the open unknowns list.
- The agent lifecycle keeps a bounded leak risk, and the e2e lane
  asserts the cleanup.
