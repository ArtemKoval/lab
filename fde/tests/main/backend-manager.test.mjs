import { describe, expect, it, vi } from 'vitest'

import {
  BACKOFF_CAP_MS,
  createBackendManager,
  backoffDelay,
} from '../../src/main/backend-manager.mjs'
import { PROTOCOL_VERSION } from '../../src/main/backend-command.mjs'

class StubChild {
  constructor() {
    this.pid = 4242
    this.writes = []
    this.stdin = {
      write: (line) => {
        this.writes.push(line)
        return true
      },
      end: () => {
        this.ended = true
      },
    }
    this.stdout = new EventTarget()
    this.stderr = new EventTarget()
    this.signals = []
  }

  kill(signal) {
    this.signals.push(signal)
  }

  emitStdout(text) {
    this.stdout.dispatchEvent(new MessageEvent('data', { data: text }))
  }

  emitStderr(text) {
    this.stderr.dispatchEvent(new MessageEvent('data', { data: text }))
  }

  exit() {
    this.onexit && this.onexit()
  }

  failToSpawn(message) {
    this.onerror && this.onerror(new Error(message))
  }
}

// Node EventTarget has no removeEventListener need here; wire uses on(...).
// The manager calls .on(name, fn) on the streams and the child, so give the
// stubs an .on facade over addEventListener.
function withOn(emitter) {
  emitter.on = (name, fn) => emitter.addEventListener(name, (event) => fn(event.data ?? event))
  return emitter
}

function makeChild() {
  const child = new StubChild()
  child.stdout = withOn(child.stdout)
  child.stderr = withOn(child.stderr)
  child.on = (name, fn) => {
    if (name === 'exit') {
      child.onexit = fn
    }
    if (name === 'error') {
      child.onerror = fn
    }
  }
  return child
}

function readyLine(version = PROTOCOL_VERSION, interpreter = '/runtime/python3') {
  return JSON.stringify({
    jsonrpc: '2.0',
    method: 'ready',
    params: { version, interpreter },
  }) + '\n'
}

function makeManager(overrides = {}) {
  const children = []
  const spawns = []
  const logs = []
  const states = []
  const notifications = []
  const treesKilled = []
  const timers = []
  const manager = createBackendManager({
    options: { isPackaged: false, venvPython: '/venv/python', backendDir: '/repo/backend' },
    spawn: (command, args, opts) => {
      spawns.push({ command, args, opts })
      const child = overrides.makeChild ? overrides.makeChild() : makeChild()
      children.push(child)
      return child
    },
    killTree: (pid) => treesKilled.push(pid),
    platform: 'darwin',
    onLog: (line) => logs.push(line),
    onNotification: (method, params) => notifications.push({ method, params }),
    onStateChange: (state) => states.push(state),
    ...overrides.deps,
    arm: (fn, ms) => {
      const timer = { fn, ms, cancelled: false }
      timers.push(timer)
      return () => {
        timer.cancelled = true
      }
    },
  })
  const fireTimers = (ms) => {
    for (const timer of timers.filter((t) => t.ms === ms && !t.cancelled)) {
      timer.cancelled = true
      timer.fn()
    }
  }
  const liveTimers = () => timers.filter((t) => !t.cancelled)
  return { manager, children, spawns, logs, states, notifications, treesKilled, fireTimers, liveTimers }
}

const lastChild = (harness) => harness.children[harness.children.length - 1]

describe('backoffDelay', () => {
  it('doubles from the base and caps', () => {
    expect(backoffDelay(0)).toBe(1000)
    expect(backoffDelay(1)).toBe(1000)
    expect(backoffDelay(2)).toBe(2000)
    expect(backoffDelay(3)).toBe(4000)
    expect(backoffDelay(4)).toBe(8000)
    expect(backoffDelay(5)).toBe(BACKOFF_CAP_MS)
    expect(backoffDelay(50)).toBe(BACKOFF_CAP_MS)
  })
})

describe('createBackendManager', () => {
  it('spawns once and reaches ready after the ready line', () => {
    const h = makeManager()
    h.manager.start()
    h.manager.start()
    expect(h.spawns).toHaveLength(1)
    expect(h.spawns[0].command).toBe('/venv/python')
    expect(h.spawns[0].args).toEqual(['-m', 'backend'])
    expect(h.states).toEqual(['starting'])
    lastChild(h).emitStdout(readyLine())
    expect(h.states).toEqual(['starting', 'ready'])
    expect(h.logs.some((line) => line.includes('/runtime/python3'))).toBe(true)
  })

  it('shows the error state at once when the ready line is late', () => {
    const h = makeManager()
    h.manager.start()
    h.fireTimers(30000)
    expect(lastChild(h).signals).toEqual(['SIGKILL'])
    lastChild(h).exit()
    expect(h.states[h.states.length - 1]).toBe('error')
    expect(h.spawns).toHaveLength(1)
  })

  it('arms real timers through the default arm when none is injected', () => {
    vi.useFakeTimers()
    try {
      const children = []
      // No injected timers, loggers, or state callbacks: default everything.
      const plain = createBackendManager({
        options: { isPackaged: false, venvPython: '/venv/python', backendDir: '/repo/backend' },
        spawn: () => {
          const child = makeChild()
          children.push(child)
          return child
        },
        killTree: () => {},
        platform: 'darwin',
      })
      plain.start()
      children[0].emitStdout('{"jsonrpc":"2.0","method":"chat/chunk","params":{"text":"a"}}\n')
      children[0].exit()
      vi.advanceTimersByTime(1000)
      expect(children).toHaveLength(2)
      children[1].exit()
      vi.advanceTimersByTime(2000)
      expect(children).toHaveLength(3)
      vi.advanceTimersByTime(60000)
      expect(children[2].signals).toEqual(['SIGKILL'])
      children[2].exit()
    } finally {
      vi.useRealTimers()
    }
  })

  it('discards the partial output tail when the child stdout ends', () => {
    const h = makeManager()
    h.manager.start()
    lastChild(h).emitStdout(readyLine())
    lastChild(h).emitStdout('{"partial')
    lastChild(h).stdout.dispatchEvent(new MessageEvent('end'))
    expect(h.states[h.states.length - 1]).toBe('ready')
  })

  it('tolerates a stdout end event that arrives after a stop', async () => {
    const h = makeManager()
    h.manager.start()
    lastChild(h).emitStdout(readyLine())
    const stopped = h.manager.stop()
    lastChild(h).exit()
    await stopped
    expect(() => lastChild(h).stdout.dispatchEvent(new MessageEvent('end'))).not.toThrow()
    expect(h.states[h.states.length - 1]).toBe('stopped')
  })

  it('tolerates a stdout end event that arrives after an unexpected exit', () => {
    const h = makeManager()
    h.manager.start()
    lastChild(h).emitStdout(readyLine())
    lastChild(h).exit()
    expect(h.states).toContain('restarting')
    expect(() => lastChild(h).stdout.dispatchEvent(new MessageEvent('end'))).not.toThrow()
  })

  it('tolerates a stdout data event that arrives after the child exit', () => {
    const h = makeManager()
    h.manager.start()
    lastChild(h).exit()
    expect(() => lastChild(h).emitStdout('{"jsonrpc":"2.0","method":"chat/chunk","params":{"text":"a"}}\n')).not.toThrow()
    expect(h.states).toContain('restarting')
  })

  it('treats a second ready line as a repeated ready state', () => {
    const h = makeManager()
    h.manager.start()
    lastChild(h).emitStdout(readyLine())
    lastChild(h).emitStdout(readyLine())
    expect(h.states).toEqual(['starting', 'ready', 'ready'])
    expect(h.children).toHaveLength(1)
  })

  it('fails pending requests with no channel without throwing', async () => {
    const h = makeManager()
    expect(() => h.manager._failPendingNow('gone')).not.toThrow()
    h.manager.start()
    lastChild(h).emitStdout(readyLine())
    const promise = h.manager.request('list_models', {})
    h.manager._failPendingNow('gone')
    await expect(promise).rejects.toMatchObject({ message: 'gone' })
  })

  it('shows the error state at once on a protocol version mismatch', () => {
    const h = makeManager()
    h.manager.start()
    lastChild(h).emitStdout(readyLine(99))
    expect(lastChild(h).signals).toEqual(['SIGKILL'])
    lastChild(h).exit()
    expect(h.states[h.states.length - 1]).toBe('error')
    expect(h.states).not.toContain('ready')
    expect(h.spawns).toHaveLength(1)
  })

  it('drops malformed child lines to the log and keeps the channel', () => {
    const h = makeManager()
    h.manager.start()
    lastChild(h).emitStdout('garbage\n')
    lastChild(h).emitStdout(readyLine())
    expect(h.states).toEqual(['starting', 'ready'])
    expect(h.logs.some((line) => line.includes('dropped malformed line'))).toBe(true)
  })

  it('routes non-ready notifications through', () => {
    const h = makeManager()
    h.manager.start()
    lastChild(h).emitStdout(readyLine())
    lastChild(h).emitStdout('{"jsonrpc":"2.0","method":"chat/chunk","params":{"text":"a"}}\n')
    expect(h.notifications).toEqual([{ method: 'chat/chunk', params: { text: 'a' } }])
  })

  it('writes child stderr to the log', () => {
    const h = makeManager()
    h.manager.start()
    lastChild(h).emitStderr('backend says hi\n')
    expect(h.logs).toContain('backend says hi')
  })

  it('restarts a crashed child with backoff and resets the counter on ready', () => {
    const h = makeManager()
    h.manager.start()
    lastChild(h).exit()
    expect(h.states).toContain('restarting')
    h.fireTimers(1000)
    expect(h.spawns).toHaveLength(2)
    lastChild(h).emitStdout(readyLine())
    expect(h.states[h.states.length - 1]).toBe('ready')
    lastChild(h).exit()
    h.fireTimers(1000)
    expect(h.spawns).toHaveLength(3)
  })

  it('gives up after five failed starts and arms no further restart', () => {
    const h = makeManager()
    h.manager.start()
    for (let attempt = 1; attempt <= 4; attempt += 1) {
      lastChild(h).exit()
      h.fireTimers(1000 * 2 ** (attempt - 1))
    }
    lastChild(h).exit()
    expect(h.states[h.states.length - 1]).toBe('error')
    expect(h.spawns).toHaveLength(5)
    h.fireTimers(10000)
    expect(h.spawns).toHaveLength(5)
  })

  it('swallows an error reply to the shutdown request', async () => {
    const h = makeManager()
    h.manager.start()
    lastChild(h).emitStdout(readyLine())
    const stopped = h.manager.stop()
    lastChild(h).emitStdout('{"jsonrpc":"2.0","id":1,"error":{"code":-32000,"message":"busy","data":{"kind":"api"}}}\n')
    lastChild(h).exit()
    await expect(stopped).resolves.toBeUndefined()
    expect(h.states[h.states.length - 1]).toBe('stopped')
  })

  it('stops the backend with the shutdown request and confirms the exit', async () => {
    const h = makeManager()
    h.manager.start()
    lastChild(h).emitStdout(readyLine())
    const stopped = h.manager.stop()
    const child = lastChild(h)
    expect(child.writes.join('')).toContain('"method":"shutdown"')
    expect(child.ended).toBe(true)
    child.exit()
    await expect(stopped).resolves.toBeUndefined()
    expect(h.states[h.states.length - 1]).toBe('stopped')
    expect(h.liveTimers()).toHaveLength(0)
    expect(child.signals).toEqual([])
  })

  it('escalates to SIGTERM and SIGKILL on POSIX when the child stays up', async () => {
    const h = makeManager()
    h.manager.start()
    lastChild(h).emitStdout(readyLine())
    const stopped = h.manager.stop()
    h.fireTimers(5000)
    expect(lastChild(h).signals).toEqual(['SIGTERM'])
    h.fireTimers(10000)
    expect(lastChild(h).signals).toEqual(['SIGTERM', 'SIGKILL'])
    lastChild(h).exit()
    await expect(stopped).resolves.toBeUndefined()
  })

  it('kills the process tree on Windows after the grace period', async () => {
    const h = makeManager({ deps: { platform: 'win32' } })
    h.manager.start()
    lastChild(h).emitStdout(readyLine())
    const stopped = h.manager.stop()
    h.fireTimers(5000)
    expect(h.treesKilled).toEqual([4242])
    lastChild(h).exit()
    await expect(stopped).resolves.toBeUndefined()
  })

  it('resolves immediately when stop is called with no child', async () => {
    const h = makeManager()
    await expect(h.manager.stop()).resolves.toBeUndefined()
    expect(h.states[h.states.length - 1]).toBe('stopped')
  })

  it('cancels a pending restart when stop arrives first', async () => {
    const h = makeManager()
    h.manager.start()
    lastChild(h).exit()
    expect(h.states).toContain('restarting')
    await h.manager.stop()
    const spawnCount = h.spawns.length
    h.fireTimers(1000)
    expect(h.spawns).toHaveLength(spawnCount)
  })

  it('does not restart after quit', async () => {
    const h = makeManager()
    h.manager.start()
    lastChild(h).emitStdout(readyLine())
    const stopped = h.manager.stop()
    lastChild(h).exit()
    await stopped
    h.fireTimers(5000)
    h.fireTimers(10000)
    expect(h.states[h.states.length - 1]).toBe('stopped')
  })

  it('treats a spawn error as a failed start', () => {
    const h = makeManager()
    h.manager.start()
    lastChild(h).failToSpawn('ENOENT')
    lastChild(h).exit()
    expect(h.states).toContain('restarting')
  })

  it('handles an exit that arrives after the spawn error without double counting', () => {
    const h = makeManager()
    h.manager.start()
    lastChild(h).failToSpawn('ENOENT')
    lastChild(h).exit()
    h.fireTimers(1000)
    expect(h.spawns).toHaveLength(2)
  })

  it('logs a kill that fails', () => {
    const h = makeManager({
      makeChild: () => {
        const child = makeChild()
        child.kill = () => {
          throw new Error('cannot kill')
        }
        return child
      },
    })
    h.manager.start()
    h.fireTimers(30000)
    expect(h.logs.some((line) => line.includes('kill failed'))).toBe(true)
  })

  it('rejects requests before the backend is ready', async () => {
    const h = makeManager()
    expect(h.manager.state).toBe('stopped')
    await expect(h.manager.request('list_models', {})).rejects.toThrow('backend is not ready')
  })

  it('logs and still resolves when the shutdown write fails', async () => {
    const h = makeManager({
      makeChild: () => {
        const child = makeChild()
        child.stdin.write = () => {
          throw new Error('stdin gone')
        }
        return child
      },
    })
    h.manager.start()
    lastChild(h).emitStdout(readyLine())
    expect(h.manager.state).toBe('ready')
    const stopped = h.manager.stop()
    expect(h.logs.some((line) => line.includes('could not be written'))).toBe(true)
    lastChild(h).exit()
    await expect(stopped).resolves.toBeUndefined()
  })

  it('sends requests when ready and resolves on the matching response', async () => {
    const h = makeManager()
    h.manager.start()
    lastChild(h).emitStdout(readyLine())
    const promise = h.manager.request('list_models', {})
    lastChild(h).emitStdout('{"jsonrpc":"2.0","id":1,"result":{"models":[]}}\n')
    await expect(promise).resolves.toEqual({ models: [] })
    expect(JSON.parse(lastChild(h).writes[0]).method).toBe('list_models')
  })

  it('fails pending requests when asked', async () => {
    const h = makeManager()
    h.manager.start()
    lastChild(h).emitStdout(readyLine())
    const promise = h.manager.request('list_models', {})
    h.manager._failPendingNow('backend exited')
    await expect(promise).rejects.toMatchObject({ message: 'backend exited' })
  })

  it('stays stopped when start is called during shutdown', async () => {
    const h = makeManager()
    h.manager.start()
    lastChild(h).emitStdout(readyLine())
    const stopped = h.manager.stop()
    h.manager.start()
    expect(h.spawns).toHaveLength(1)
    lastChild(h).exit()
    await stopped
  })
})
