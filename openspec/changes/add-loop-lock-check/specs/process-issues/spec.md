## ADDED Requirements

### Requirement: The loop takes and releases the run lock

The loop SHALL take the lock with `acquire --holder LABEL` before the
first scan, and the label SHALL name one run. The run SHALL release the
lock with `release --holder LABEL` at its end. The release SHALL remove
the file only on an exact holder label match, or behind `--force`. A
release with no lock file SHALL NOT be an error.

#### Scenario: A release without a lock is not an error

- **GIVEN** no lock file exists
- **WHEN** `release` runs with the holder `loop-20261108-a`
- **THEN** the exit code is 0

#### Scenario: A foreign holder release refuses

- **GIVEN** the lock file records the holder `loop-20261108-a`
- **WHEN** `release` runs with the holder `loop-20261108-b`
- **THEN** the exit code is 2
- **AND** the lock file stays

#### Scenario: A force release clears a lost lock

- **GIVEN** the lock file records a holder label that no run carries
- **WHEN** `release --force` runs
- **THEN** the lock file is gone and the exit code is 0

### Requirement: The run lock record

The lock file SHALL sit under the primary checkout root, resolved from
the git common directory, and a non-git root SHALL use the working
directory. The record SHALL carry the holder label, the host, the boot
id, the process id, the process start time, and the acquire time. The
record SHALL pin the session anchor of the calling session, or no
process id when the chain carries none.

#### Scenario: An acquire takes a free lock

- **GIVEN** no lock file exists
- **WHEN** `acquire` runs with the holder `loop-20261108-a`
- **THEN** the exit code is 0
- **AND** the lock file records the holder, the host, the boot id, the
  process id, the process start time, and the acquire time

The scan SHALL examine the lock before the first `gh` call, and a refused
scan SHALL make no `gh` call. A fresh foreign lock SHALL exit 2 with the
holder details on stderr. A scan whose holder label matches the lock in
force SHALL proceed. The scan SHALL NOT write the lock file.

#### Scenario: A fresh foreign lock refuses the scan

- **GIVEN** the lock file records a holder with a live process on this
  host and a young acquire time
- **WHEN** the scan runs with no holder label
- **THEN** the exit code is 2 and stderr names the holder
- **AND** no `gh` call runs

#### Scenario: The holder label exempts the scan

- **GIVEN** the lock file records the holder `loop-20261108-a` with a
  live process on this host
- **WHEN** the scan runs with the holder `loop-20261108-a`
- **THEN** the scan prints the queue

#### Scenario: The session anchor exempts the scan

- **GIVEN** the lock file records the process that anchors this calling
  session, with a live process on this host
- **WHEN** the scan runs with no holder label
- **THEN** the scan prints the queue

#### Scenario: A missing lock does not refuse the scan

- **GIVEN** no lock file exists
- **WHEN** the scan runs
- **THEN** the scan prints the queue

### Requirement: The stale rules of the run lock

The lock is stale when the record does not parse, the schema version is
unknown, the boot id differs from this boot, the recorded process id no
longer runs, the recorded start time differs from the running process, or
the acquire time is older than 24 hours. A lock recorded on another host
SHALL stay fresh until the acquire time passes the age rule.

#### Scenario: A dead holder marks the lock stale

- **GIVEN** the lock file records a process id that no longer runs on
  this host
- **WHEN** the scan runs
- **THEN** stderr reports the stale lock and the scan prints the queue

#### Scenario: A foreign-host lock stays fresh

- **GIVEN** the lock file records another host with a young acquire time
- **WHEN** the scan runs
- **THEN** the exit code is 2 and stderr names the holder

#### Scenario: An anchorless record ages out

- **GIVEN** the lock file records no process id and an acquire time
  more than 24 hours old
- **WHEN** the scan runs
- **THEN** stderr reports the stale lock and the scan prints the queue

#### Scenario: An old acquire time marks the lock stale

- **GIVEN** the lock file records an acquire time more than 24 hours old
- **WHEN** the scan runs
- **THEN** stderr reports the stale lock and the scan prints the queue

#### Scenario: A corrupt record is stale

- **GIVEN** the lock file does not parse
- **WHEN** the scan runs
- **THEN** stderr reports the stale lock and the scan prints the queue

### Requirement: A stale lock never wedges the loop

A stale lock SHALL draw a report on stderr, and the scan SHALL proceed.
`acquire` SHALL clear a stale lock and take it behind one exclusive file
create.

#### Scenario: The acquire clears a stale lock

- **GIVEN** the lock file records a process id that no longer runs
- **WHEN** `acquire` runs with the holder `loop-20261108-b`
- **THEN** the lock file records the holder `loop-20261108-b`
- **AND** the exit code is 0

#### Scenario: A different boot id marks the lock stale

- **GIVEN** the lock file records a boot id that differs from this boot
- **WHEN** `acquire` runs with the holder `loop-20261108-b`
- **THEN** the acquire clears the lock and takes it

#### Scenario: A start-time mismatch marks the lock stale

- **GIVEN** the lock file records a start time that differs from the running process
- **WHEN** `acquire` runs with the holder `loop-20261108-b`
- **THEN** the acquire clears the lock and takes it

### Requirement: The pre-flight stops on the halt file first

The pre-flight SHALL examine the `.claude/halt` file in the session root
or in the primary checkout before the peak window examination and the
lock. The run SHALL process no issue and SHALL report the stop when the
file exists.

#### Scenario: A halt file stops the run before the lock

- **GIVEN** the `.claude/halt` file exists in the primary checkout
- **WHEN** the run starts
- **THEN** the run takes no lock and processes no issue
- **AND** the run reports the stop

## MODIFIED Requirements

### Requirement: The scan CLI reports the queue

The `scan` subcommand SHALL print one line per open issue with its
number, state, and pull request links. The `--json` flag SHALL print the
same data as JSON. The lock examination SHALL run before the first `gh`
call. The CLI SHALL exit 0 on success and 2 on an operational failure: a
failed `gh` call, an unreadable state directory, or a fresh foreign lock.
A usage error SHALL exit 64.

#### Scenario: A scan prints the queue

- **WHEN** the scan runs with `--json`
- **THEN** the output is a JSON array
- **AND** each entry carries the issue number, the state, and the pull
  request links

#### Scenario: A broken gh fails the run

- **GIVEN** the `gh` call fails
- **WHEN** the scan runs
- **THEN** the exit code is 2
- **AND** stderr names the failure

#### Scenario: A usage error exits 64

- **WHEN** the scan runs with an unknown flag
- **THEN** the exit code is 64
- **AND** stderr carries the parser message
