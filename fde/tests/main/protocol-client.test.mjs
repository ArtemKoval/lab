import { describe, expect, it, vi } from 'vitest'

import { BackendError, LineBuffer, createChannel } from '../../src/main/protocol-client.mjs'

function linesFrom(chunks) {
  const seen = []
  const buffer = new LineBuffer((line) => seen.push(line))
  for (const chunk of chunks) {
    buffer.push(chunk)
  }
  return { seen, buffer }
}

describe('LineBuffer', () => {
  it('delivers complete lines from one chunk', () => {
    const { seen } = linesFrom(['{"a":1}\n{"b":2}\n'])
    expect(seen).toEqual(['{"a":1}', '{"b":2}'])
  })

  it('reassembles a line split across chunks and acts once', () => {
    const { seen } = linesFrom(['{"a"', ':1}\n'])
    expect(seen).toEqual(['{"a":1}'])
  })

  it('keeps the partial tail for the next chunk', () => {
    const { seen } = linesFrom(['{"a"', ':1}'])
    expect(seen).toEqual([])
  })

  it('discards the partial tail when the child exits', () => {
    const { seen, buffer } = linesFrom(['{"partial"'])
    buffer.end()
    expect(seen).toEqual([])
  })
})

describe('createChannel', () => {
  function makeChannel() {
    const written = []
    const notifications = []
    const malformed = []
    const channel = createChannel({
      writeLine: (line) => written.push(line),
      onNotification: (method, params) => notifications.push({ method, params }),
      onMalformed: (line) => malformed.push(line),
    })
    return { channel, written, notifications, malformed }
  }

  it('sends requests with incrementing ids and resolves on the matching response', async () => {
    const { channel, written } = makeChannel()
    const promise = channel.request('list_models', {})
    const second = channel.request('shutdown', {})
    expect(JSON.parse(written[0]).id).toBe(1)
    expect(JSON.parse(written[1]).id).toBe(2)
    channel.handleData('{"jsonrpc":"2.0","id":2,"result":{"stopping":true}}\n')
    channel.handleData('{"jsonrpc":"2.0","id":1,"result":{"models":[]}}\n')
    await expect(second).resolves.toEqual({ stopping: true })
    await expect(promise).resolves.toEqual({ models: [] })
  })

  it('rejects with a BackendError carrying the error kind', async () => {
    const { channel } = makeChannel()
    const promise = channel.request('validate_key', {})
    channel.handleData('{"jsonrpc":"2.0","id":1,"error":{"code":-32000,"message":"Invalid key","data":{"kind":"auth"}}}\n')
    await expect(promise).rejects.toMatchObject({ kind: 'auth', message: 'Invalid key' })
    await expect(promise).rejects.toBeInstanceOf(BackendError)
  })

  it('defaults the kind to api when the error carries no data', async () => {
    const { channel } = makeChannel()
    const promise = channel.request('x', {})
    channel.handleData('{"jsonrpc":"2.0","id":1,"error":{"code":-1,"message":"boom"}}\n')
    await expect(promise).rejects.toMatchObject({ kind: 'api' })
  })

  it('routes notifications and never treats them as responses', () => {
    const { channel, notifications, malformed } = makeChannel()
    channel.handleData('{"jsonrpc":"2.0","method":"chat/chunk","params":{"text":"a"}}\n')
    expect(notifications).toEqual([{ method: 'chat/chunk', params: { text: 'a' } }])
    expect(malformed).toEqual([])
  })

  it('drops malformed lines to the onMalformed callback', () => {
    const { channel, malformed, notifications } = makeChannel()
    channel.handleData('not json\n')
    expect(malformed).toEqual(['not json'])
    expect(notifications).toEqual([])
  })

  it('drops protocol lines it cannot pair or route', () => {
    const { channel, malformed } = makeChannel()
    channel.handleData('{"jsonrpc":"2.0","id":99,"result":{}}\n')
    expect(malformed).toHaveLength(1)
  })

  it('fails pending requests when the child dies', async () => {
    const { channel } = makeChannel()
    const promise = channel.request('chat_start', {})
    channel.failPending('backend exited')
    await expect(promise).rejects.toMatchObject({ message: 'backend exited' })
  })

  it('exposes handleEnd so the manager can drop the partial tail', () => {
    const { channel, malformed, notifications } = makeChannel()
    channel.handleData('{"partial')
    expect(() => channel.handleEnd()).not.toThrow()
    expect(malformed).toEqual([])
    expect(notifications).toEqual([])
  })
})
