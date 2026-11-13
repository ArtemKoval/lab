# Design: add-devops-chaos-ssh

## The analysis

An ssh connection moves through five phases. The client resolves the
host name. The client opens the TCP transport. The two sides negotiate
algorithms and exchange keys in the handshake. The client proves the
identity in the auth phase. The server starts a session with a shell
or a command.

A fault in each phase gives a distinct client symptom. The table maps
the 13 catalog scenarios to the phases. The table drives the catalog
files, the injection scripts, and the spec scenarios.

| id | phase | fault | the client sees |
| --- | --- | --- | --- |
| `dns-failure` | resolve | the practice host name resolves nowhere | `Could not resolve hostname` |
| `wrong-host` | resolve | the scratch config sends the name `practice` to the decoy sshd. The decoy carries its own host key and banner | a login to the wrong machine, or a host key warning |
| `firewall-drop` | transport | an iptables DROP rule on the forwarded port | `Connection timed out` |
| `port-refused` | transport | the injection stops the practice sshd | `Connection reset by peer` behind the published port. `Connection refused` on an unpublished port |
| `wrong-port` | transport | the command names port `2224`, and nothing listens there | `Connection refused` |
| `host-key-changed` | handshake | the injection regenerates the practice host key | the `REMOTE HOST IDENTIFICATION HAS CHANGED` warning |
| `kex-mismatch` | handshake | the server offers only key exchange algorithms the client refuses | `no matching key exchange method found` |
| `pubkey-rejected` | auth | `authorized_keys` lacks the practice key | `Permission denied (publickey)` |
| `key-permissions` | auth | the practice private key mode is `0644` | the `UNPROTECTED PRIVATE KEY FILE` warning, key ignored |
| `password-disabled` | auth | the injection disables password authentication | `Permission denied (publickey)` with no password prompt |
| `wrong-user` | auth | the server restricts its allowed users | `Permission denied (publickey)` |
| `broken-shell` | session | the injection sets the account shell to `/bin/false` | `Permission denied` with the full method list. The daemon refuses an account whose shell sits outside `/etc/shells` |
| `no-agent-forwarding` | session | the injection disables agent forwarding on the server | an empty `SSH_AUTH_SOCK` on the target |

Two transport faults and three auth faults share client signatures on
purpose. The teaching pairs section gives the groups and the
disambiguator.

## The environment

One devcontainer at `devops/chaos/ssh/` serves every scenario. The
Dockerfile builds one image with Ubuntu LTS, `openssh-server`, and
`iptables`. The `devcontainer.json` sets the build, the run
arguments, and the ports. The run arguments carry
`--cap-add=NET_ADMIN` for the firewall scenario. The `appPort` pins
publish both ports on the host loopback:

```
"appPort": ["127.0.0.1:2222:22", "127.0.0.1:2223:2223"]
```

The practice sshd listens on container port 22. The decoy sshd for
the `wrong-host` scenario listens on container port 2223 with its own
host key and its own banner. The entrypoint starts both daemons. The
tutor adds a bounded readiness wait on the forwarded port before any
injection, so the injection starts only after the daemon answers.

The host needs docker with a live daemon, the `docker` group, and
node for `npx`. The devcontainer CLI drives the container with the
house pattern from `llm_ops/eval` and the notebook recipe: `up` and
`exec`, both with `--workspace-folder devops/chaos/ssh`. The
`--remove-existing-container` flag of `up` gives the recreate-on-
start behavior, and the eval README shows the same flag. The tutor
stops the container with a forced `docker rm` on the container of
the workspace. The first `npx` call fetches the CLI. The README
records the CLI version in its provenance, as the notebook recipe
does. On hosts where the shell session lacks the docker group, the
`sg docker -c` prefix gives the command the group, as the notebook
recipe shows.

```
learner at a host terminal
   |
   | python -m chaos_ssh start <scenario-id>
   v
tutor CLI (chaos_ssh, stdlib python)
   |                                  |
   | devcontainer up / exec           | devcontainer down
   | (boot, inject)                   | (tear down)
   v                                  v
+------------------------------------------------------+
| container "chaos-ssh"                                |
|                                                      |
|   practice sshd  :22    <- 127.0.0.1:2222 (appPort)  |
|   decoy sshd     :2223  <- 127.0.0.1:2223 (appPort)  |
+------------------------------------------------------+
   ^
   | the real ssh client of the learner, on the host:
   | SSH_AUTH_SOCK=... ssh -A -F <scratch>/config ...
   |     -o UserKnownHostsFile=... -o GlobalKnownHostsFile=...
   |     -o IdentitiesOnly=yes -o IdentityAgent=none
   |     -i <scratch>/id_ed25519 -p 2222 practice@127.0.0.1
```

The client of the learner stays on the host. The client behavior is
then real: the timeouts, the refusals, and the algorithm negotiation
come from the client of the operating system. Alternative rejected:
a client container with the learner attached to it. The attach flow
hides the real client behavior, and the teaching goal is the real
client. Alternative rejected: docker-in-docker. The nested daemon
adds cost with no teaching value.

### The injection mechanics

Nine scenarios arm container-side faults, and nine scripts sit at
`environments/inject/<scenario-id>.sh`: `firewall-drop`,
`port-refused`, `host-key-changed`, `kex-mismatch`,
`pubkey-rejected`, `password-disabled`, `wrong-user`, `broken-shell`,
and `no-agent-forwarding`. Four scenarios carry no script, and their
catalog rows carry `"inject": null`: `dns-failure` (the fault lives
in the host name, and the name is `.invalid`), `wrong-host` (the
redirect lives in the scratch config on the host), `wrong-port` (the
fault is the dead port in the command), and `key-permissions` (the
mode change happens on the host, inside the scratch directory).

The Dockerfile copies the scripts to `/opt/chaos/inject/`. The tutor
runs the script of the armed scenario through `devcontainer exec`.
The scripts change only the state inside the container. Typical
actions: stop the practice sshd, regenerate the host key, edit
`authorized_keys`, restrict the allowed users, or add the iptables
rule. The host scratch directory is never mounted into the
container. The tutor passes the values a script needs, such as the
practice public key text, as script arguments on the exec command
line.

The auth scenarios need a pinned auth config. The image sets
`PasswordAuthentication yes` as the base. The `pubkey-rejected` and
`wrong-user` injections set the value to no. The
`password-disabled` injection sets the value to no as well, and its
printed command omits `-i`. The method list in the client message is
then the lesson.

The `wrong-port` lesson pins its dead port at `2224`. The decoy
sshd lives on `2223`, so a wrong-port command against `2223` would
reach a live daemon and print a host key prompt. The pin keeps the
refusal signature of the pair intact.

The account inventory is part of the image. The practice account is
`practice`, and the practice key opens it. The second account is
`guest`, and it exists with no authorized key, so the `wrong-user`
lesson connects as `guest` while the injection restricts the allowed
users to `practice`. The decoy sshd accepts the same `practice`
account with the same key, and it carries its own host key and the
banner text `decoy-ssh`. The image builds the accounts, and the
injections only mutate their runtime state.

### The scratch mechanics

The tutor creates one scratch directory per scenario under
`devops/chaos/ssh/.state/<scenario-id>/`. The directory holds the
practice keypair, the ssh config, the seeded known_hosts file, the
empty global known_hosts file, the hint position file, and the agent
socket with its pid file. The `.gitignore` at the area root ignores
`.state/`. The printed command binds five settings into the scratch
directory. Each setting closes one leak into the real learner state:

- `-F <scratch>/config` replaces `~/.ssh/config`.
- `UserKnownHostsFile` pins the scratch known_hosts file.
- `GlobalKnownHostsFile` points to a scratch file too, because the
  client otherwise reads the global `/etc/ssh/ssh_known_hosts`.
- `IdentitiesOnly yes` with `IdentityAgent none` stops the client
  from offering the default identities and the real agent keys.
- `-i <scratch>/id_ed25519` names the practice key.

The tutor never reads or writes the real `~/.ssh` of the learner.

At `start` the tutor generates one ed25519 practice keypair in the
scratch directory, seeds the scratch known_hosts file with the
practice host key, and then arms the fault. The seed order matters
for `host-key-changed`: the old key must sit in the scratch
known_hosts file before the injection regenerates the server key, or
the client prints a first-contact prompt instead of the changed-key
warning. The seed runs through `ssh-keyscan` on the host, after the
readiness wait and before the injection. The injection installs the
public key into `authorized_keys` of the practice account. The
`pubkey-rejected` injection removes it again. The
`key-permissions` injection sets the mode of the private key to
`0644` on the host side, inside the scratch directory.

For `wrong-host` the printed command is
`ssh -F <scratch>/config practice`. The config maps `Host practice`
to the decoy port with the scratch identity and host key values, and
it sets `HostKeyAlias decoy`. The start flow seeds the alias key
through `ssh-keyscan` of the decoy port before the arm, so the
learner connects without a first-contact prompt. The learner then
meets a machine that the learner did not expect, and the lesson is
the banner and the `ssh -G practice` probe of the reveal. The config
redirect is the armed fault.

For `no-agent-forwarding` the tutor starts a scratch `ssh-agent` with
its socket and pid file inside the scratch directory. The printed
command prints one composed command line:

```
SSH_AUTH_SOCK=<scratch>/agent.sock ssh -A -F <scratch>/config ... 'echo "$SSH_AUTH_SOCK"'
```

The remote echo prints the forwarded socket path when the forwarding
works, and it prints nothing when the server refuses the forwarding.
The `start` flow removes a stale socket and pid file first. The `stop`
flow ends the agent process and removes the state. The stale-agent
leak stays an open unknown with a probe.

## The tutor

The package `chaos_ssh` sits at
`devops/chaos/ssh/tutor/chaos_ssh/`. The command `python -m chaos_ssh`
runs from the `tutor/` directory. The CLI uses argparse. The flag
`--json` switches every command to machine output. Exit 0 marks
success. Exit 2 marks an operational failure, and the message names
one next action.

The subcommand flow:

- `list` reads the catalog and prints the rows. No container starts.
- `start <id>` validates the id, examines the pinned ports, starts
  the environment with the `up` command, waits for daemon readiness,
  seeds the scratch host key, runs the injection when the scenario
  defines one, writes the scratch state, and prints the notice. The
  `up` step carries `--remove-existing-container`, so no fault state
  survives from a previous scenario. When the tutor container itself
  holds a pinned port, the flag removes it first, and the port
  refusal fires only for a foreign process.
- `hint <id>` validates the id, reads the position file, and prints
  the next hint. The command starts no environment.
- `reveal <id>` validates the id and prints the catalog texts. The
  command starts no environment.
- `stop <id>` validates the id, removes the container with a forced
  `docker rm`, ends the scratch agent of the id, and deletes the
  scratch directory of the id. The removal is global, because one
  workspace holds one container. A stop for a different id than the
  armed one removes the container and cleans only its own scratch
  set, and the armed scratch stays in place until its own stop. An
  unknown id exits 2, because the command cannot name the scratch
  set to remove. The exit 0 of a second stop applies to a known id
  with no container and no scratch state.

The spec text writes `chaos-ssh` as the shorthand for
`python -m chaos_ssh` run from the `tutor/` directory. Version one
carries no launcher script, and the README carries the module command.

The list rows carry the fields `id`, `phase`, and `title`. The
`title` is the one-line fault summary of the row.

The catalog data shape. One JSON file per scenario in `catalog/`. The
files are JSON, because the tutor stays standard library only, and
Python carries no YAML parser in the standard library.

```json
{
  "id": "port-refused",
  "title": "The ssh daemon is stopped",
  "phase": "transport",
  "fault": "The injection stops the practice sshd.",
  "inject": "environments/inject/port-refused.sh",
  "command": "ssh -F {scratch}/config {target}",
  "signature": "Connection reset by peer",
  "prompts": [
    "What does the client message name as the failure?",
    "Is the server machine reachable at all?"
  ],
  "hints": [
    "Examine the port number in your command.",
    "The port forwards into the container. Ask what listens there."
  ],
  "reveal": {
    "wrong": "The injection stopped the practice sshd, so nothing answers behind the published port.",
    "fix": "Start the ssh service, or connect to the port that sshd really uses."
  },
  "connection": {
    "target": "practice",
    "hostname": "127.0.0.1",
    "user": "practice",
    "port": 2222,
    "identity": true,
    "hostkeyalias": null,
    "arm": null,
    "agent": false
  }
}
```

The `{scratch}` and `{target}` placeholders get their values at print
time. The `connection` block holds the arm data of the scenario. The
five bindings of the safety rule live in the scratch config, and the
printed command stays short. The `hostname` value fills the
`HostName` line of that config. The row of `dns-failure` carries
`null` there, so the config omits the line and the client resolves
the target name itself. The resolve fault fires only on that path.
The catalog files sit under `devops/`, outside the openspec
STE gate, but the tutor strings and the README stay STE by house
style.

The exit contract. Exit 0 on success. Exit 2 on an operational
failure with one named next action in the message. Examples: an
unknown id names the valid ids, a port in use names the holder
examination or the port override, and a container fault names the
devcontainer command. On hosts where the session lacks the docker
group, the message names the `sg docker -c` prefix, as the notebook
recipe shows.

## The teaching pairs

Two transport faults teach one contrast. The apply run observed the
published port of the container answering a dead daemon with
`Connection reset by peer`, because the port publisher listens on
the host while nothing answers behind it. The dead port `2224` of
`wrong-port` sits outside the publisher, so the host refuses it
outright with `Connection refused`. The pair trains the difference
between a reset and a refusal, and the reveal of `port-refused`
names it.

Three auth faults share one client signature.
`pubkey-rejected`, `wrong-user`, and `password-disabled` all print
`Permission denied (publickey)`. In the first fault the server lacks
the public key of the learner. In the second fault the server
refuses the user name. In the third fault the server disables the
password method, and the printed command omits `-i`, so the absence
of a password prompt is the observable.

The apply run added one more refuser to the set. `broken-shell`
prints `Permission denied` with the full method list, because the
daemon refuses an account whose shell sits outside `/etc/shells`.
The method list separates it from the three auth faults: the base
auth config still stands, so the list still names the password
method. The method list is the discriminator across the whole
auth-adjacent group.

The message alone does not name the cause. The method list of `ssh
-v` cannot separate the three either, because the three injections
set the same auth config. The real discriminators are the account in
the command, the offered key, and the omitted `-i`. The command of
`wrong-user` names `guest`, and the account is the fault. The
command of `password-disabled` offers no key, so the method list
shows a dead path. The command of `pubkey-rejected` offers the right
key that the server rejects. The hints lead from the message through
the discriminators to the cause, and the reveal of each scenario
carries the distinction.

## Out of scope

- MTU blackhole faults. The emulation needs packet-level path control
  that one container network cannot give.
- ISP and CGNAT realities. No container equivalent exists for
  carrier-grade address translation.
- Kerberos and GSSAPI domains. The emulation needs a domain
  controller.
- fail2ban timing faults. The timing makes the scenario flaky.
- VPN routing faults. The emulation needs an outer network that the
  host owns.
- Hardware token authentication. The emulation needs physical
  hardware.

## Open unknowns

- The legacy key exchange set for `kex-mismatch`. Status: open.
  Modern Ubuntu builds may drop the legacy family from the `sshd`
  binary. Next probe: at apply time, run `sshd -T` in the built
  image and read the `kexalgorithms` line. If the legacy set is
  absent, the catalog row switches to a restricted host key type
  set, and the client then prints
  `no matching host key type found`. The spec stays count-free and
  mechanism-free on this scenario, so the pivot is catalog drift and
  not a spec change.
- The `appPort` override form. Status: observed, one half resolved.
  The triple form `127.0.0.1:2222:22` published both ports and
  answered connections on the real stack. The substitution of a
  host environment variable into `appPort` stays unprobed. Next
  probe: probe the `${localEnv:VAR}` support of the pinned CLI
  version. The fallback pins the two ports in the committed file,
  and the README documents the edit.
- The readiness wait bounds. Status: observed. The warm e2e run
  answers in about seven seconds, and the cold build took about one
  minute on the apply host. The bounded wait covered both, and the
  lane reports no timeouts.
- The client output strings across environments. Status: observed
  and resolved for `port-refused`. The apply run found that the
  published port answers a dead daemon with a reset, not a refusal,
  because the port publisher listens on the host. The catalog
  signature now names the reset, the e2e lane accepts both the
  refusal and the reset, and the remaining scenarios keep substring
  signatures for the version drift.
- The stale-agent leak. Status: open. A crashed run can leave an
  agent process. Next probe: `start` removes a stale socket and pid
  file, `stop` kills the agent, and the e2e lane asserts that no
  agent process survives `stop`.

## Verification

The hermetic suite at `tests/devops_chaos_ssh/` fakes the container
boundary. The suite covers the catalog parse, the five subcommands,
the exit contract, the hint order, and the scratch path rules. The
suite needs no docker daemon and runs in the root suite. The path
insert for the package import lives in the test conftest, as the
mutation rules of the house require. The conftest is a protected
gate path, so the apply pull request carries
`gate-integrity: acknowledged`.

The opt-in e2e lane runs with `DEVOPS_CHAOS_SSH_E2E=1` and a docker
daemon on the host. The lane examines ports `2222` and `2223` and
asserts both free before the run, starts the container, arms
`port-refused`, runs the printed command, examines the refused
output substring, stops clean, and asserts that no agent process
survives the stop.

The CI gate paths cover `tools/<listed>/` and `tests/` today. The
package lives under `devops/chaos/ssh/tutor/`, so the apply change
widens the gated-path regex and the coverage `--source` list of the
protected workflow, and the dryer and mutator filters gain the new
prefix. Without the widening, the quality gates skip the package in
CI while the local run passes.

The strict OpenSpec validate passes on the change directory. The STE
gate scans the change prose with zero errors. The quality gates
apply to the tutor at apply time. The bar: CRAP at 10 or less,
duplication with no pair at or above 0.8, and mutation with no
survivors.
