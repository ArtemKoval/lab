# Spec Delta

## Purpose

Runs the Python backend as a child process of the Electron main process, and gives both sides one line-delimited JSON-RPC channel over stdio.

## ADDED Requirements

### Requirement: One backend process runs at a time
The main process MUST spawn the backend at app start and MUST run at most one backend process at any moment. A restart MUST start only after the old process has exited.

#### Scenario: One spawn at start
- **WHEN** the app starts
- **THEN** the main process spawns exactly one backend process

#### Scenario: Restart starts after exit
- **WHEN** the main process restarts the backend
- **THEN** the old process has exited before the new one starts

### Requirement: The renderer has no direct channel to the backend
The renderer MUST NOT receive the child process handle. The renderer MUST call the preload API, and the main process MUST forward each request to the backend.

#### Scenario: Renderer path goes through the preload API
- **WHEN** the renderer needs backend data
- **THEN** the main process forwards the request to the backend

### Requirement: The ready line carries the version and the interpreter path
The backend MUST print one ready line on stdout before it serves the first request. The line MUST carry the protocol version and the path of the interpreter that runs the backend. The main process MUST wait for this line before it sends requests. If the line does not arrive within 30 seconds, the main process MUST kill the child and show the backend error state.

#### Scenario: Ready line arrives before the first request
- **WHEN** the backend finishes its startup work
- **THEN** it prints one ready line with the protocol version and the interpreter path

#### Scenario: Ready line never arrives
- **WHEN** no ready line arrives within 30 seconds
- **THEN** the main process kills the child and shows the backend error state

### Requirement: A version mismatch stops the start
The main process MUST compare the ready line version with its own protocol version. On a mismatch, the main process MUST kill the child, MUST show the backend error state, and MUST send no requests.

#### Scenario: Mismatched version
- **WHEN** the ready line carries a version that differs from the version of the main process
- **THEN** the main process kills the child and shows the backend error state

### Requirement: Lines are framed and flushed
The backend MUST write each message as one line that ends with a newline and MUST flush stdout before it waits for input. The main process MUST buffer the child output and MUST act only on complete lines. When the child exits, the main process MUST discard any partial line left in the buffer.

#### Scenario: Line split across chunks reassembles
- **WHEN** one ready line arrives in two chunks
- **THEN** the main process acts on the line once the line is complete

#### Scenario: Partial line before exit is discarded
- **WHEN** the child exits and the buffer holds a partial line
- **THEN** the main process discards the partial line and does not act on it

#### Scenario: Backend flushes before it waits
- **WHEN** the backend writes a response line
- **THEN** the line reaches the main process at once and does not sit in a buffer

### Requirement: A malformed line does not stop the protocol
The main process MUST drop a line that is not valid JSON, MUST log it, and MUST keep the channel open.

#### Scenario: Malformed line
- **WHEN** the backend writes a line that is not valid JSON
- **THEN** the main process logs the line and keeps the channel open

### Requirement: Each response matches its request
Each response MUST carry the id of its request. Stream events MUST be notifications without an id.

#### Scenario: Response matches its request
- **WHEN** the main process sends a request with id 7
- **THEN** the matching response carries id 7

### Requirement: The app stops the backend on quit, per operating system
On app quit, the main process MUST send a stop request. On macOS and Linux, the main process MUST then send SIGTERM and, if the child still runs 5 seconds later, MUST send SIGKILL. On Windows, the main process MUST then kill the child process tree in one forceful step. The main process MUST confirm the exit before the app quits.

#### Scenario: Backend stops after the stop request
- **WHEN** the user quits the app and the backend exits after the stop request
- **THEN** the main process confirms the exit and the app quits with no backend process left

#### Scenario: Escalation on macOS and Linux
- **WHEN** the backend still runs 5 seconds after SIGTERM
- **THEN** the main process sends SIGKILL and the backend exits

#### Scenario: Windows kills the process tree
- **WHEN** the user quits the app on Windows and the backend spawned worker processes
- **THEN** the forceful kill ends the backend and its workers

### Requirement: The backend exits when stdin closes
The backend MUST exit within 5 seconds after its stdin closes. This rule holds at any moment, with or without a stop request.

#### Scenario: Stdin closes without a stop request
- **WHEN** the main process dies and the backend stdin closes
- **THEN** the backend exits within 5 seconds and no orphan process stays

### Requirement: The main process restarts a crashed backend
If the backend exits while the app runs, the main process MUST restart it with an exponential backoff. The backoff MUST cap at 10 seconds. After 5 failed starts in a row, the main process MUST stop and MUST show the backend error state. During app shutdown, the main process MUST NOT start a new backend.

#### Scenario: Restart after one crash
- **WHEN** the backend exits while the user works
- **THEN** the main process restarts it after a short wait, the next request succeeds, and no backend error state shows

#### Scenario: Give up after repeated crashes
- **WHEN** the backend fails to stay up five times in a row
- **THEN** the main process shows the backend error state and starts no further attempts

### Requirement: The app selects the backend executable by run mode
In the packaged app, the main process MUST run the Python interpreter of the embedded runtime tree from the app resources. In development, the main process MUST run the project Python interpreter with the backend source. The run mode decides the choice.

#### Scenario: Packaged app uses the embedded interpreter
- **WHEN** the packaged app spawns the backend
- **THEN** it runs the interpreter from the app resources, with the dependency tree on its module path

#### Scenario: Development run uses the host interpreter
- **WHEN** the app starts with the dev command
- **THEN** it runs the project Python interpreter on the backend source in the repository

### Requirement: Logs go to a file in the user data folder
The backend MUST send logs to stderr only, and MUST keep stdout for protocol lines. The main process MUST write each stderr line to `logs/backend.log` in the user data folder. The log MUST keep at most 5 files of 5 MB and delete the oldest.

#### Scenario: Log line reaches the file
- **WHEN** the backend writes a log line to stderr
- **THEN** the main process appends the line to `logs/backend.log` in the user data folder

#### Scenario: Log rotation
- **WHEN** `backend.log` grows past 5 MB
- **THEN** the app moves it to a numbered archive and starts a new file, and keeps at most 5 archives

### Requirement: The key never enters the spawn
The spawn argument list and the child environment MUST NOT contain the OpenRouter key. The key travels only as a parameter of the validate and chat requests. The backend MUST NOT keep the key between requests.

#### Scenario: Spawn stays key-free
- **WHEN** the main process spawns the backend
- **THEN** the argument list and the environment hold no key text

#### Scenario: Restart needs no key state
- **WHEN** the main process restarts the backend after a crash
- **THEN** the first request after the restart carries the key again as a parameter
