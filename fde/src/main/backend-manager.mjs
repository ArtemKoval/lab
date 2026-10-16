// Owns the backend child process: spawn by run mode, ready-line handshake
// with the version check, restart with capped backoff, and the per-OS kill
// ladder on quit. All external effects (spawn, kill, timers) are injected,
// so tests drive it with stubs and manual timer triggers.

import { backendCommand, PROTOCOL_VERSION } from './backend-command.mjs'
import { createChannel } from './protocol-client.mjs'

export const READY_TIMEOUT_MS = 30000
export const KILL_GRACE_MS = 5000
export const MAX_FAILED_STARTS = 5
export const BACKOFF_BASE_MS = 1000
export const BACKOFF_CAP_MS = 10000

export function backoffDelay(failedStarts, base = BACKOFF_BASE_MS, cap = BACKOFF_CAP_MS) {
  if (failedStarts <= 0) {
    return base
  }
  return Math.min(cap, base * 2 ** (failedStarts - 1))
}

export function createBackendManager({
  options,
  spawn,
  killTree,
  platform,
  onLog = () => {},
  onNotification = () => {},
  onStateChange = () => {},
  protocolVersion = PROTOCOL_VERSION,
  readyTimeoutMs = READY_TIMEOUT_MS,
  killGraceMs = KILL_GRACE_MS,
  maxFailedStarts = MAX_FAILED_STARTS,
  arm = (fn, ms) => {
    const timer = setTimeout(fn, ms)
    return () => clearTimeout(timer)
  },
}) {
  let child = null
  let channel = null
  let state = 'stopped'
  let quitting = false
  let failedStarts = 0
  let cancelReadyTimer = null
  const killTimers = []
  let stopSettled = null
  let restartArm = null
  let fatalStart = false

  function setState(next) {
    state = next
    onStateChange(next)
  }

  function disposeTimers() {
    if (cancelReadyTimer) {
      cancelReadyTimer()
      cancelReadyTimer = null
    }
    while (killTimers.length > 0) {
      killTimers.pop()()
    }
  }

  function handleChildGone() {
    if (!child) {
      return
    }
    child = null
    /* v8 ignore next 3 -- the channel exists from the first spawn moment, so
       an exit always finds it; the guard only covers a same-tick race. */
    if (channel) {
      // A request that outlives its child must fail, never hang.
      channel.failPending('The backend process is gone')
      channel = null
    }
    disposeTimers()
    if (stopSettled) {
      const settle = stopSettled
      stopSettled = null
      onLog('backend exited; stop confirmed', 'manager')
      setState('stopped')
      settle()
      return
    }
    /* v8 ignore next 3 -- stop() either settles the stop promise on the exit
       or runs with no child, so this guard only covers a same-tick race. */
    if (quitting) {
      return
    }
    if (fatalStart) {
      onLog('backend start failed for good', 'manager')
      setState('error')
      return
    }
    handleUnexpectedExit()
  }

  function handleUnexpectedExit() {
    failedStarts += 1
    if (failedStarts >= maxFailedStarts) {
      onLog(`backend failed ${failedStarts} starts in a row; giving up`, 'manager')
      setState('error')
      return
    }
    const delay = backoffDelay(failedStarts)
    onLog(`backend exited; restart in ${delay} ms (attempt ${failedStarts})`, 'manager')
    setState('restarting')
    restartArm = arm(start, delay)
  }

  function handleMessage(message) {
    if (message.method !== 'ready') {
      onNotification(message.method, message.params)
      return
    }
    if (message.params.version !== protocolVersion) {
      // The spec demands the error state at once: a mismatched backend is
      // fatal, and a restart would meet the same mismatch five times.
      onLog(
        `protocol version mismatch: backend ${message.params.version}, main ${protocolVersion}`,
        'manager',
      )
      fatalStart = true
      killChildNow()
      return
    }
    if (cancelReadyTimer) {
      cancelReadyTimer()
      cancelReadyTimer = null
    }
    failedStarts = 0
    onLog(`backend ready from ${message.params.interpreter}`, 'manager')
    setState('ready')
  }

  function handleMalformed(line) {
    onLog(`dropped malformed line from backend: ${line.slice(0, 200)}`, 'manager')
  }

  function wireChild() {
    channel = createChannel({
      writeLine: (line) => child.stdin.write(line),
      onNotification: (method, params) => handleMessage({ method, params }),
      onMalformed: handleMalformed,
    })
    child.stdout.on('data', (chunk) => channel.handleData(String(chunk)))
    child.stdout.on('end', () => channel.handleEnd())
    child.stderr.on('data', (chunk) => onLog(String(chunk).trimEnd(), 'backend'))
    child.on('error', (err) => {
      onLog(`backend spawn error: ${err.message}`, 'manager')
      handleChildGone()
    })
    child.on('exit', () => handleChildGone())
  }

  function start() {
    restartArm = null
    if (child || quitting) {
      return
    }
    const command = backendCommand(options)
    child = spawn(command.command, command.args, { env: command.env })
    onLog(`spawned backend pid ${child.pid}: ${command.command}`, 'manager')
    setState('starting')
    wireChild()
    cancelReadyTimer = arm(() => {
      /* v8 ignore next 3 -- the timer is always disposed before the child can be
         gone; the guard only covers a same-tick exit during dispatch. */
      if (!child) {
        return
      }
      // The spec demands the error state after 30 seconds without a ready
      // line: a hung child counts straight as the final failure.
      onLog(`ready line did not arrive within ${readyTimeoutMs} ms`, 'manager')
      fatalStart = true
      killChildNow()
    }, readyTimeoutMs)
  }

  function killChildNow() {
    /* v8 ignore next 3 -- every call site holds a live child; the guard only
       covers a same-tick exit between the caller's check and this call. */
    if (!child) {
      return
    }
    try {
      child.kill('SIGKILL')
    } catch (err) {
      onLog(`kill failed: ${err.message}`, 'manager')
    }
  }

  function stageKills(pid) {
    if (platform === 'win32') {
      killTimers.push(arm(() => killTree(pid), killGraceMs))
      return
    }
    killTimers.push(arm(() => {
      /* v8 ignore next 3 -- disposeTimers cancels these on exit; the guard
         only covers a same-tick exit between dispatch and the kill. */
      if (child) {
        child.kill('SIGTERM')
      }
    }, killGraceMs))
    killTimers.push(arm(() => {
      /* v8 ignore next 3 -- same race guard as the SIGTERM stage above. */
      if (child) {
        child.kill('SIGKILL')
      }
    }, killGraceMs * 2))
  }

  function stop() {
    quitting = true
    if (restartArm) {
      restartArm()
      restartArm = null
    }
    if (!child) {
      setState('stopped')
      return Promise.resolve()
    }
    const stopped = new Promise((resolve) => {
      stopSettled = resolve
    })
    try {
      channel.request('shutdown', {}).catch(() => {})
    } catch {
      onLog('shutdown request could not be written', 'manager')
    }
    child.stdin.end()
    stageKills(child.pid)
    return stopped
  }

  function request(method, params) {
    if (!channel || state !== 'ready') {
      return Promise.reject(new Error('backend is not ready'))
    }
    return channel.request(method, params)
  }

  return {
    start,
    stop,
    request,
    get state() {
      return state
    },
    _failPendingNow(reason) {
      if (channel) {
        channel.failPending(reason)
      }
    },
  }
}
