## Purpose

The ssh tutor teaches the failure modes of an ssh connection. One
container environment arms one fault at a time. The learner connects
with a real ssh client, thinks through the failure with the prompts
of the catalog, and asks the tutor for hints and the reveal. The
tutor never touches the real ssh state of the learner.

## ADDED Requirements

### Requirement: The tutor lists the catalog
`chaos-ssh list` SHALL print one line per catalog file. Each line
SHALL carry the scenario id, the connection phase, and the title of
the scenario. `chaos-ssh list --json` SHALL print the same rows as
one JSON array with the fields `id`, `phase`, and `title`. The flag
`--json` SHALL switch the machine output for every subcommand.

#### Scenario: The list carries one row per catalog file
- **GIVEN** the catalog holds the files for `dns-failure` and
  `port-refused`
- **WHEN** the learner runs `chaos-ssh list`
- **THEN** the output carries one row per file, and each row carries
  the id, the phase, and the fault summary of its file

#### Scenario: The JSON rows match the text rows
- **GIVEN** the catalog holds the files for `dns-failure` and
  `port-refused`
- **WHEN** the learner runs `chaos-ssh list --json`
- **THEN** the output parses as one JSON array with one row per
  scenario, and each row carries the same three fields as the text
  row

### Requirement: The tutor arms a scenario
`chaos-ssh start <scenario-id>` SHALL validate the id, bring the
environment up, run the injection script of the scenario when the
scenario defines one, and print the armed fault notice. The notice
SHALL carry the connection command template and the first thinking
prompt. An unknown id SHALL exit 2 with the valid ids in the message.
The tool SHALL exit 2 when the pinned host port is in use, and the
message SHALL name `stop` as the next action.

#### Scenario: A valid id arms the fault
- **GIVEN** the scenario `port-refused` exists and no container runs
- **WHEN** the learner runs `chaos-ssh start port-refused`
- **THEN** the tool brings the environment up, runs the injection,
  and prints the notice with the connection template and the first
  prompt

#### Scenario: An unknown id exits 2
- **GIVEN** the catalog holds no scenario with the id
  `no-such-scenario`
- **WHEN** the learner runs `chaos-ssh start no-such-scenario`
- **THEN** the tool exits 2, and the message names the valid ids

#### Scenario: A port in use exits 2
- **GIVEN** another process holds the pinned host port `127.0.0.1:2222`
- **WHEN** the learner runs `chaos-ssh start dns-failure`
- **THEN** the tool exits 2, and the message names `stop` as the next
  action

#### Scenario: A scenario without an injection arms without one
- **GIVEN** the scenario `dns-failure` defines no injection script
- **WHEN** the learner runs `chaos-ssh start dns-failure`
- **THEN** the tool brings the environment up, prints the notice, and
  exits 0

### Requirement: The tutor hands hints in order
`chaos-ssh hint <scenario-id>` SHALL print the next hint of the
scenario in catalog order. After the last hint the command SHALL
print the last hint again. With no position file the command SHALL
print hint 1. `chaos-ssh start` SHALL reset the hint position of the
armed scenario. `chaos-ssh hint` SHALL validate the id, and an
unknown id SHALL exit 2 with the valid ids in the message.

#### Scenario: The hints come in order
- **GIVEN** the learner armed `firewall-drop` and no hint command ran
- **WHEN** the learner runs `chaos-ssh hint firewall-drop` twice
- **THEN** the first run prints hint 1, and the second run prints
  hint 2

#### Scenario: The last hint repeats
- **GIVEN** the learner printed every hint of `firewall-drop`
- **WHEN** the learner runs `chaos-ssh hint firewall-drop` again
- **THEN** the output prints the last hint again

#### Scenario: A restart resets the position
- **GIVEN** the learner printed two hints of `firewall-drop`
- **WHEN** the learner runs `chaos-ssh start firewall-drop` and then
  `chaos-ssh hint firewall-drop`
- **THEN** the hint output is hint 1 again

#### Scenario: An unknown hint id exits 2
- **GIVEN** the catalog holds no scenario with the id
  `no-such-scenario`
- **WHEN** the learner runs `chaos-ssh hint no-such-scenario`
- **THEN** the tool exits 2, and the message names the valid ids

### Requirement: The tutor reveals the fault
`chaos-ssh reveal <scenario-id>` SHALL print the fault description,
the expected client output signature, and the fix. The command reads
the catalog only, and it needs no running container. The command
validates the id, and an unknown id SHALL exit 2 with the valid ids
in the message.

#### Scenario: The reveal names the fault and the fix
- **GIVEN** the scenario `host-key-changed` exists
- **WHEN** the learner runs `chaos-ssh reveal host-key-changed`
- **THEN** the output carries the fault text, the changed-host-key
  signature, and the fix steps

#### Scenario: The reveal works without a container
- **GIVEN** no container runs
- **WHEN** the learner runs `chaos-ssh reveal port-refused`
- **THEN** the output carries the catalog texts, and the tool exits 0

### Requirement: The tutor stops clean
`chaos-ssh stop <scenario-id>` SHALL bring the environment down and
SHALL remove the scratch state of the scenario id. The environment is
one container, so the teardown is global, and the id argument names
the scratch set to remove. The command validates the id, and an
unknown id SHALL exit 2, because the command cannot name the scratch
set to remove. A second `stop` for a known id SHALL exit 0. The
message of the second stop SHALL say that no container runs.

#### Scenario: The stop removes the container and the scratch state
- **GIVEN** the learner armed `port-refused` and printed one hint
- **WHEN** the learner runs `chaos-ssh stop port-refused`
- **THEN** the tool brings the environment down, removes the scratch
  state of `port-refused`, and exits 0

#### Scenario: A second stop exits 0
- **GIVEN** no container runs and the scratch state is absent
- **WHEN** the learner runs `chaos-ssh stop port-refused` a second
  time
- **THEN** the tool exits 0, and the message says that no container
  runs

### Requirement: The tutor never touches the real ssh state of the learner
The tutor SHALL NOT write inside the real `~/.ssh` of the learner. A
client-side fault SHALL arm only inside the scratch directory of the
tutor. The printed command SHALL bind the ssh state to the scratch
directory with five settings: `-F`, `UserKnownHostsFile`,
`GlobalKnownHostsFile`, `IdentitiesOnly yes` with
`IdentityAgent none`, and `-i` where the scenario uses a key.

#### Scenario: The printed command carries the scratch bindings
- **GIVEN** the learner armed `key-permissions`
- **WHEN** the tutor prints the connection command
- **THEN** the command carries `-F`, `UserKnownHostsFile`,
  `GlobalKnownHostsFile`, `IdentitiesOnly`, and `-i`, and every
  bound path sits inside the scratch directory

#### Scenario: The scratch agent state stays in the scratch directory
- **GIVEN** the learner armed `no-agent-forwarding`
- **WHEN** the tutor prints the composed connection command
- **THEN** the command sets `SSH_AUTH_SOCK` to a path inside the
  scratch directory, and the agent pid file sits inside the scratch
  directory too
