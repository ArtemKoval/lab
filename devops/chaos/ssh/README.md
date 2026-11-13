# devops chaos: ssh

One container environment that arms one ssh failure at a time, and
one tutor CLI that walks a learner through the failure: connect,
think, take hints, and reveal the fault.

The catalog holds 13 scenarios over five connection phases: resolve,
transport, handshake, auth, and session. Two transport faults and
three auth faults share client signatures on purpose, so the
scenarios train differential diagnosis.

## Before you start

- A Linux host with docker and a running daemon, and your user in
  the `docker` group.
- Node with `npx`, so the devcontainer CLI can run. The first call
  fetches the CLI.
- An ssh client on the host.
- Where the shell session lacks the docker group, the
  `sg docker -c '...'` prefix gives the command the group.

## The commands

Run the tutor from the area root, `devops/chaos/ssh/tutor/`:

```bash
cd devops/chaos/ssh/tutor
python3 -m chaos_ssh list
python3 -m chaos_ssh start port-refused
python3 -m chaos_ssh hint port-refused
python3 -m chaos_ssh reveal port-refused
python3 -m chaos_ssh stop port-refused
```

`start` boots the container, seeds your scratch host key, arms the
fault, and prints the connection command. Run that command in a
second terminal with your own ssh client. `hint` hands the hints of
the scenario in order. `reveal` names the fault and the fix. `stop`
removes the container and the scratch state.

The `--json` flag switches every command to machine output.

## The safety rules

The tutor never touches your real `~/.ssh`. Every scenario carries
its own scratch directory under `.state/`, and the printed command
binds the run to it: the config with `-F`, the scratch known_hosts
files, `IdentitiesOnly yes`, and `IdentityAgent none`. The scratch
directory holds the practice keypair, and `.gitignore` keeps it out
of the repository. `stop` removes it.

## The ports

The container publishes `127.0.0.1:2222` (the practice sshd) and
`127.0.0.1:2223` (the decoy sshd of the wrong-host scenario). The
pins live in `.devcontainer/devcontainer.json`. When another process
holds a port, `start` exits 2 and names the holder examination. To
move the ports, edit the `appPort` pins in that file, and read the
notes in design.md of the change about the override form.

## The scenarios

| id | phase | what it arms |
| --- | --- | --- |
| `dns-failure` | resolve | a name no resolver answers |
| `wrong-host` | resolve | the decoy sshd answers the practice name |
| `firewall-drop` | transport | an iptables DROP on the port |
| `port-refused` | transport | the practice sshd is stopped |
| `wrong-port` | transport | the command names the dead port 2224 |
| `host-key-changed` | handshake | the server host key regenerates |
| `kex-mismatch` | handshake | a legacy key exchange set only |
| `pubkey-rejected` | auth | the key disappears from authorized_keys |
| `key-permissions` | auth | the private key mode becomes 0644 |
| `password-disabled` | auth | the password method disappears |
| `wrong-user` | auth | only practice may log in |
| `broken-shell` | session | the account shell becomes /bin/false |
| `no-agent-forwarding` | session | the server refuses agent forwarding |

## The e2e lane

The hermetic suite fakes the container boundary and runs in the root
suite. The e2e lane boots the real container:

```bash
DEVOPS_CHAOS_SSH_E2E=1 tools/zai_routing_audit/.venv/bin/python -m pytest tests/devops_chaos_ssh/test_chaos_e2e.py -q
```

The lane needs docker, the docker group, and `npx`.

## Provenance

The area landed through the change `add-devops-chaos-ssh` (issue
216). The container image is Ubuntu 24.04 with OpenSSH from the
distribution. The devcontainer CLI version on this host at the first
run was 0.90.0 (the same version the notebook recipe at
`tools/knights_notebook_run/` records). The kex-mismatch scenario
pins a legacy key exchange set; the apply run confirmed the set
exists in the built image, and if a future OpenSSH build drops it,
the catalog row pivots to a restricted host key type set, as the
change design records.
