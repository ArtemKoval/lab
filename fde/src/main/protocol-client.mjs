// Line framing and JSON-RPC plumbing for the parent side of the stdio pipe.
// The buffer acts only on complete lines and discards a partial line when the
// child exits, so a truncated line can never pair with the next child's output.

export class BackendError extends Error {
  constructor(kind, message) {
    super(message)
    this.name = 'BackendError'
    this.kind = kind
  }
}

export class LineBuffer {
  constructor(onLine) {
    this._onLine = onLine
    this._rest = ''
  }

  push(chunk) {
    let text = this._rest + chunk
    let index = text.indexOf('\n')
    while (index !== -1) {
      this._onLine(text.slice(0, index))
      text = text.slice(index + 1)
      index = text.indexOf('\n')
    }
    this._rest = text
  }

  end() {
    // A partial line from a dead child is dropped, never acted on.
    this._rest = ''
  }
}

export function createChannel({ writeLine, onNotification, onMalformed, requestTimeoutMs = 60000 }) {
  let nextId = 1
  const pending = new Map()

  const buffer = new LineBuffer((line) => {
    let message
    try {
      message = JSON.parse(line)
    } catch {
      onMalformed(line)
      return
    }
    if (message && message.id != null && pending.has(message.id)) {
      const { resolve, reject, cancelTimer } = pending.get(message.id)
      pending.delete(message.id)
      cancelTimer()
      if (message.error) {
        const kind = (message.error.data && message.error.data.kind) || 'api'
        reject(new BackendError(kind, message.error.message))
      } else {
        resolve(message.result)
      }
      return
    }
    if (message && message.method) {
      onNotification(message.method, message.params)
      return
    }
    onMalformed(line)
  })

  return {
    handleData: (chunk) => buffer.push(chunk),
    handleEnd: () => buffer.end(),
    request(method, params) {
      const id = nextId
      nextId += 1
      writeLine(JSON.stringify({ jsonrpc: '2.0', id, method, params }) + '\n')
      return new Promise((resolve, reject) => {
        const timer = setTimeout(() => {
          /* v8 ignore next 3 -- the resolve path cancels this timer before it
             can fire, so the cleared-pending case is unreachable; the guard
             only covers a same-tick answer race. */
          if (pending.has(id)) {
            pending.delete(id)
            reject(new BackendError('api', `The backend did not answer ${method} within ${requestTimeoutMs} ms`))
          }
        }, requestTimeoutMs)
        pending.set(id, {
          resolve,
          reject,
          cancelTimer: () => clearTimeout(timer),
        })
      })
    },
    failPending(reason) {
      for (const entry of pending.values()) {
        clearTimeout(entry.cancelTimer)
        entry.reject(new BackendError('api', reason))
      }
      pending.clear()
    },
  }
}
