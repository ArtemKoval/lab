# Proposal: add-devops-chaos-ssh

## Why

Issue 216 asks for a chaos teaching area for ssh at
`devops/chaos/ssh/`. The issue names three asks:

```
analyze ways where ssh connection could go wrong and broken
create devcontainer setups to emulate all of the problems
create a command line wrapper which will launch a tutor, where a
person would be prompted to enter some ssh connection command, a
problem appears, then some ways to think about it proposed, then some
hints and finally a description of what is wrong in the current
scenario
```

A broken ssh state is hard to study. The client prints one short
message, and the cause hides in one phase of the connection. The
learner cannot make the fault appear again on demand. The analysis
belongs in a reviewed artifact. The environment and the tutor follow
after the review.

## What Changes

### The failure catalog

13 scenario files at `devops/chaos/ssh/catalog/`, one JSON file per
fault. Each file carries the id, the phase, the fault text, the
injection reference, the output signature, the thinking prompts, the
ordered hints, and the reveal text. The tutor reads the files as
data, and no scenario name sits in the tutor code.

### The phase model

The catalog rows map to five connection phases: resolve, transport,
handshake, auth, and session. Design.md carries the phase analysis,
the catalog table, and the shared-signature groups.

### The container environment

One devcontainer at `devops/chaos/ssh/` with one Dockerfile. The
image carries Ubuntu LTS, `openssh-server`, and `iptables`. The
container runs the practice sshd and a decoy sshd with its own host
key. The `appPort` pins publish `127.0.0.1:2222` and
`127.0.0.1:2223` on the host. The run arguments carry
`--cap-add=NET_ADMIN` for the firewall scenario. One injection script
per container-side scenario arms the fault inside the container. The
host needs docker and node, and the devcontainer CLI drives the
container with the house `up`, `exec`, and `down` pattern.

### The tutor CLI

The package `chaos_ssh` at `devops/chaos/ssh/tutor/` with the entry
`python -m chaos_ssh`. Five subcommands: `list`, `start`, `hint`,
`reveal`, and `stop`. The CLI follows the house contract with
argparse and `--json`. Exit 0 marks success. Exit 2 marks an
operational failure, and the message names one next action.

### The host-driven model

The learner runs a real ssh client on the host against the pinned
ports. Server faults inject inside the container. Client faults arm
inside a tutor scratch directory that binds the ssh state for the
run. The printed command carries five bindings that hold the run to
the scratch state, and the tutor never touches the real `~/.ssh` of
the learner. The safety rule is its own requirement in the spec
delta.

### The shared signatures

Three auth faults share one client signature on purpose, and the two
transport faults teach the contrast between a reset and a refusal.
The same client output hides different causes, and the scenarios
train differential diagnosis. Design.md gives the groups and the
discriminators.

### Apply-time deliveries

The README at `devops/chaos/ssh/README.md`, the suite at
`tests/devops_chaos_ssh/`, the CI path additions, and one CLAUDE.md
Projects entry. This proposal ships no code. The apply phase starts
after the proposal merge, per the pipeline discipline.

## Capabilities

### New Capabilities

- `devops-chaos-ssh`: The tutor lists the catalog, arms a scenario in
  the container environment, hands hints in order, reveals the fault,
  and stops clean. The tutor never touches the real ssh state of the
  learner. Client-side faults arm only in the tutor scratch
  directory.

### Modified Capabilities

None.

## Out of scope

- The faults that one container cannot emulate: MTU blackhole,
  carrier-grade NAT, Kerberos or GSSAPI domains, fail2ban timing,
  VPN routing, and hardware tokens. Design.md carries the reasons.
- No MCP server and no Claude skill in this change. The tutor serves
  a human at a terminal.

## Impact

- `devops/chaos/ssh/`: the catalog files, the Dockerfile, the
  devcontainer config, the injection scripts, the `chaos_ssh`
  package, and the README. All files are new.
- `tests/devops_chaos_ssh/`: the hermetic suite and the opt-in e2e
  lane. Both arrive at apply time.
- `CLAUDE.md`: one Projects entry at apply time.
- `.github/workflows/tests.yml`: the apply
  change adds the new suite and package paths, and both are protected
  gate paths.
- The apply pull request carries `gate-integrity: acknowledged`,
  because the suite needs a `tests/*/conftest.py` for the package
  path insert, and that pattern is pinned.
- `reports/saturation/scores.json`: the saturation store gains the
  new module at apply time.
- No `.claude/settings.json` change. No dspy-gate `gates.yaml` and no
  `rubrics/`. The harness registry declares no such capability. The
  change does not register itself. The opt-in stays with the
  operator.
- `tools/project_setup/registry.json`: no unit in this proposal. The
  apply phase adds a unit if the environment needs a setup step.
- No new dependency in any tool venv. The tutor uses the Python
  standard library. The environment uses docker and the devcontainer
  CLI on the host.
