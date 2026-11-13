# Council Notes: proposal.md

## Author Summary

The author drafted the proposal in the house shape: the issue quotes,
the catalog, the phase model, the environment, the tutor CLI, the
host-driven model, the shared signatures, the apply-time deliveries,
the new capability, and an artifacts-only impact. The author flagged
six concerns: the wrong-host strain, the held-port refusal, the
dns-failure boot cost, the tutor surface growth, the auth signature
tie width, and the kex apply risk.

## Reviewer Challenges

- The compose environment language survived in six spots across
  proposal and design, against the verified host facts. Neither
  docker compose nor docker-compose exists on this host.
- The spec delta missed the template scenario format and the Purpose
  section of the house convention.
- stop per id contradicts the one-container model.
- The start requirement was false for dns-failure, which defines no
  injection.
- The auth signature tie is three-way, wider than the declared two
  pairs.
- The Impact claim about the gate-integrity line missed the
  tests/*/conftest.py pin, and the pin is real in the guard test.

## Resolutions

- Accepted: the primary agent rewrote the environment model around
  the devcontainer CLI with the pinned dual appPort, the in-container
  decoy sshd on 2223, and the exec injection path. The proposal now
  names docker and the devcontainer CLI.
- Accepted: the spec delta carries the Purpose section and the
  scenario blocks of the house format.
- Accepted: stop now states the global teardown with the id argument
  naming the scratch set.
- Accepted: the start requirement runs the injection when the
  scenario defines one, and a scenario covers the no-injection case.
- Accepted: the proposal now states two transport faults and three
  auth faults, and the design carries the disambiguator.
- Accepted: the Impact section now states the conftest pin and the
  acknowledgment line on the apply pull request.

## Remaining Risks

- The wrong-host lesson depends on the config redirect, and the reveal
  must teach the verification probes, or the lesson teaches config
  trust instead of host verification.
- The apply phase carries the container build risk, the KEX
  availability risk, and the port collision risk named in the open
  unknowns of design.md.
