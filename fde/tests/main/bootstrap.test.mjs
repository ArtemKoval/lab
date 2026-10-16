// Integration test: the whole app wiring over stubbed Electron and a stub
// backend child. Exercises the wizard, the first chat, persistence, the
// delete-last-conversation rule, and the quit path end to end.

import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { PROTOCOL_VERSION } from '../../src/main/backend-command.mjs'
import { bootstrap } from '../../src/main/bootstrap.mjs'

const fdeDir = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..')

let dir

beforeEach(() => {
  dir = fs.mkdtempSync(path.join(os.tmpdir(), 'fde-app-'))
})

afterEach(() => {
  vi.restoreAllMocks()
})

function flush() {
  return new Promise((resolve) => setTimeout(resolve, 0))
}

function makeStubChild() {
  const child = {
    pid: 555,
    writes: [],
    ended: false,
    signals: [],
    stdin: {
      write: (line) => {
        child.writes.push(line)
        return true
      },
      end: () => {
        child.ended = true
      },
    },
    stdout: { on: (name, fn) => { child.stdoutHandlers[name] = fn } },
    stderr: { on: (name, fn) => { child.stderrHandlers[name] = fn } },
    kill: (signal) => child.signals.push(signal),
  }
  child.stdoutHandlers = {}
  child.stderrHandlers = {}
  child.emitStdout = (text) => child.stdoutHandlers.data(text)
  child.emitStderr = (text) => child.stderrHandlers.data(text)
  child.on = (name, fn) => {
    if (name === 'exit') {
      child.exitFn = fn
    }
    if (name === 'error') {
      child.errorFn = fn
    }
  }
  return child
}

function makeElectronStub(tmp, childBox) {
  // ipcMain.handle registers (event, payload) functions; the tests invoke
  // them with the payload alone, like the renderer side of invoke does.
  const ipc = { handlers: {}, handle: (channel, fn) => { ipc.handlers[channel] = (payload) => fn(null, payload) } }
  const timers = []
  const arm = (fn, ms) => {
    const timer = { fn, ms, cancelled: false }
    timers.push(timer)
    return () => {
      timer.cancelled = true
    }
  }
  const fireTimers = (ms) => {
    for (const timer of timers.filter((t) => t.ms === ms && !t.cancelled)) {
      timer.cancelled = true
      timer.fn()
    }
  }
  const sent = []
  const webContents = {
    send: (channel, payload) => sent.push({ channel, payload }),
    on: vi.fn(),
    setWindowOpenHandler: vi.fn(),
  }
  const windows = []
  class BrowserWindow {
    constructor(options) {
      this.options = options
      this.webContents = webContents
      windows.push(this)
    }

    once(name, fn) {
      if (name === 'ready-to-show') {
        this.showFn = fn
      }
    }

    loadFile() {
      this.loaded = true
    }

    focus() {}

    isDestroyed() {
      return false
    }
  }
  const sessionStub = { webRequest: { onHeadersReceived: vi.fn() } }
  const appEvents = {}
  const spawn = () => {
    childBox.current = makeStubChild()
    return childBox.current
  }
  const electron = {
    app: {
      isPackaged: false,
      getAppPath: () => fdeDir,
      getPath: () => tmp,
      requestSingleInstanceLock: () => true,
      whenReady: () => Promise.resolve(),
      on: (name, fn) => {
        appEvents[name] = fn
      },
      quit: vi.fn(),
    },
    BrowserWindow,
    ipcMain: ipc,
    safeStorage: {
      isEncryptionAvailable: () => true,
      encryptString: (text) => Buffer.from(`enc:${text}`, 'utf8'),
      decryptString: (buffer) => buffer.toString('utf8').slice(4),
    },
    session: { defaultSession: sessionStub },
    shell: { openExternal: vi.fn() },
    killTree: vi.fn(),
  }
  return { electron, ipc, sent, windows, appEvents, arm, fireTimers, spawn }
}

function readyLine() {
  return JSON.stringify({
    jsonrpc: '2.0',
    method: 'ready',
    params: { version: PROTOCOL_VERSION, interpreter: '/venv/python' },
  }) + '\n'
}

function respond(child, id, result) {
  child.emitStdout(JSON.stringify({ jsonrpc: '2.0', id, result }) + '\n')
}

function respondError(child, id, kind, message) {
  child.emitStdout(JSON.stringify({
    jsonrpc: '2.0',
    id,
    error: { code: -32000, message, data: { kind } },
  }) + '\n')
}

function emitNotification(child, method, params) {
  child.emitStdout(JSON.stringify({ jsonrpc: '2.0', method, params }) + '\n')
}

function lastRequest(child) {
  return JSON.parse(child.writes.at(-1))
}

describe('bootstrap', () => {
  async function startConfiguredApp(dir, extraOverrides = {}) {
    const childBox = {}
    const stubs = makeElectronStub(dir, childBox)
    const app = await bootstrap(stubs.electron, { arm: stubs.arm, spawn: stubs.spawn, ...extraOverrides })
    await flush()
    const child = childBox.current
    child.emitStdout(readyLine())
    await flush()
    const validated = stubs.ipc.handlers['fde:validateKey']({ key: 'sk-key' })
    await flush()
    respond(child, lastRequest(child).id, { valid: true })
    await flush()
    respond(child, lastRequest(child).id, { models: [{ id: 'any', name: 'Any (auto router)' }] })
    await validated
    await flush()
    await stubs.ipc.handlers['fde:finishWizard']({ model: 'any' })
    const state = await stubs.ipc.handlers['fde:getState']()
    return { stubs, app, child, conversationId: state.active.id }
  }

  it('runs the wizard, the first chat, and the quit path end to end', async () => {
    const childBox = {}
    const stubs = makeElectronStub(dir, childBox)
    const app = await bootstrap(stubs.electron, { arm: stubs.arm, spawn: stubs.spawn })
    await flush()

    const child = childBox.current
    expect(child).toBeTruthy()
    expect(stubs.windows).toHaveLength(1)
    expect(stubs.windows[0].options.webPreferences.sandbox).toBe(true)
    expect(stubs.windows[0].loaded).toBe(true)

    child.emitStdout(readyLine())
    await flush()
    expect(app.manager.state).toBe('ready')
    const mainLog = fs.readFileSync(path.join(dir, 'logs', 'main.log'), 'utf8')
    expect(mainLog).toContain('"outcome":"ready"')

    let state = await stubs.ipc.handlers['fde:getState']()
    expect(state.view).toBe('wizard')

    // Step 1: validate the key through the backend. submitKey stays pending
    // until the model list answers, so respond to both before awaiting it.
    const validated = stubs.ipc.handlers['fde:validateKey']({ key: 'sk-key' })
    await flush()
    expect(lastRequest(child).method).toBe('validate_key')
    respond(child, lastRequest(child).id, { valid: true })
    await flush()
    const modelsRequest = lastRequest(child)
    expect(modelsRequest.method).toBe('list_models')
    respond(child, modelsRequest.id, { models: [{ id: 'any', name: 'Any (auto router)' }] })
    await validated
    await flush()
    expect(app.wizard.snapshot().state).toBe('models')

    // Finish stores key, model, and the setup mark in one step.
    await stubs.ipc.handlers['fde:finishWizard']({ model: 'any' })
    expect(app.wizard.snapshot().state).toBe('done')
    const configText = fs.readFileSync(path.join(dir, 'config.json'), 'utf8')
    expect(configText).not.toContain('sk-key')
    expect(JSON.parse(configText).setupDone).toBe(true)
    state = await stubs.ipc.handlers['fde:getState']()
    expect(state.view).toBe('chat')
    expect(state.active.messages).toEqual([])

    // The first chat round trip.
    const conversationId = state.active.id
    const sendResult = await stubs.ipc.handlers['fde:sendMessage']({ id: conversationId, text: 'hello' })
    expect(sendResult).toEqual({ ok: true })
    await flush()
    const startRequest = lastRequest(child)
    expect(startRequest.method).toBe('chat_start')
    expect(startRequest.params.key).toBe('sk-key')
    expect(startRequest.params.model).toBe('any')
    respond(child, startRequest.id, { stream_id: 9 })
    await flush()
    emitNotification(child, 'chat/chunk', { stream_id: 9, text: 'Hi' })
    emitNotification(child, 'chat/done', { stream_id: 9, text: 'Hi there', stopped: false })
    await flush()

    const conversation = app.history.get(conversationId)
    expect(conversation.title).toBe('hello')
    expect(conversation.messages.at(-1)).toEqual({ role: 'assistant', content: 'Hi there' })
    const chatEvents = stubs.sent.filter((s) => s.channel === 'fde:chat-event')
    expect(chatEvents.at(-1).payload).toMatchObject({ conversationId, type: 'done' })

    // Deleting the last conversation creates a fresh empty one.
    await stubs.ipc.handlers['fde:deleteChat']({ id: conversationId })
    state = await stubs.ipc.handlers['fde:getState']()
    expect(state.active.id).not.toBe(conversationId)
    expect(state.active.messages).toEqual([])

    // Quit stops the backend before the app quits.
    const quitEvent = { preventDefault: vi.fn() }
    stubs.appEvents['before-quit'](quitEvent)
    expect(quitEvent.preventDefault).toHaveBeenCalled()
    await flush()
    expect(child.ended).toBe(true)
    child.exitFn()
    await flush()
    expect(stubs.electron.app.quit).toHaveBeenCalled()
  })

  it('surfaces a chat error notification when the backend rejects the send', async () => {
    const childBox = {}
    const stubs = makeElectronStub(dir, childBox)
    const app = await bootstrap(stubs.electron, { arm: stubs.arm, spawn: stubs.spawn })
    await flush()
    const child = childBox.current
    child.emitStdout(readyLine())
    await flush()

    const validated = stubs.ipc.handlers['fde:validateKey']({ key: 'sk-key' })
    await flush()
    respond(child, lastRequest(child).id, { valid: true })
    await flush()
    const modelsRequest = lastRequest(child)
    respond(child, modelsRequest.id, { models: [] })
    await validated
    await flush()
    await stubs.ipc.handlers['fde:finishWizard']({ model: 'any' })
    const state = await stubs.ipc.handlers['fde:getState']()
    const conversationId = state.active.id

    stubs.ipc.handlers['fde:sendMessage']({ id: conversationId, text: 'hi' })
    await flush()
    const startRequest = lastRequest(child)
    respondError(child, startRequest.id, 'rate', 'slow down')
    await flush()

    const chatEvents = stubs.sent.filter((s) => s.channel === 'fde:chat-event')
    expect(chatEvents.at(-1).payload).toMatchObject({
      conversationId,
      type: 'error',
      kind: 'rate',
      message: 'slow down',
    })
    const conversation = app.history.get(conversationId)
    expect(conversation.messages.at(-1).role).toBe('user')
  })

  it('refuses a second instance', async () => {
    const childBox = {}
    const stubs = makeElectronStub(dir, childBox)
    stubs.electron.app.requestSingleInstanceLock = () => false
    const app = await bootstrap(stubs.electron)
    expect(app).toBeNull()
    expect(stubs.electron.app.quit).toHaveBeenCalled()
  })

  it('honors the FDE_USER_DATA override for the user data folder', async () => {
    const childBox = {}
    const stubs = makeElectronStub(dir, childBox)
    const overrideDir = fs.mkdtempSync(path.join(os.tmpdir(), 'fde-override-'))
    stubs.electron.app.setPath = vi.fn()
    process.env.FDE_USER_DATA = overrideDir
    try {
      await bootstrap(stubs.electron, { arm: stubs.arm, spawn: stubs.spawn })
      await flush()
      expect(stubs.electron.app.setPath).toHaveBeenCalledWith('userData', overrideDir)
    } finally {
      delete process.env.FDE_USER_DATA
    }
  })

  it('writes the start-failed readiness line when the backend gives up', async () => {
    const childBox = {}
    const stubs = makeElectronStub(dir, childBox)
    const app = await bootstrap(stubs.electron, { arm: stubs.arm, spawn: stubs.spawn })
    await flush()
    // Five failed starts: each crash fires its backoff timer, then the fifth
    // start fails for good.
    for (const delay of [1000, 2000, 4000, 8000]) {
      childBox.current.exitFn()
      await flush()
      stubs.fireTimers(delay)
    }
    childBox.current.exitFn()
    await flush()
    expect(app.manager.state).toBe('error')
    const mainLog = fs.readFileSync(path.join(dir, 'logs', 'main.log'), 'utf8')
    expect(mainLog).toContain('"outcome":"start-failed"')
    // The readiness line is written once per app run: a later state change
    // adds no second line.
    const readinessLines = mainLog.split('\n').filter((line) => line.includes('backend-readiness'))
    expect(readinessLines).toHaveLength(1)
  })

  it('writes the readiness line once even when the backend later dies', async () => {
    const childBox = {}
    const stubs = makeElectronStub(dir, childBox)
    const app = await bootstrap(stubs.electron, { arm: stubs.arm, spawn: stubs.spawn })
    await flush()
    const child = childBox.current
    child.emitStdout(readyLine())
    await flush()
    expect(app.manager.state).toBe('ready')
    for (const delay of [1000, 2000, 4000, 8000]) {
      child.exitFn()
      await flush()
      stubs.fireTimers(delay)
    }
    child.exitFn()
    await flush()
    expect(app.manager.state).toBe('error')
    const readinessLines = fs.readFileSync(path.join(dir, 'logs', 'main.log'), 'utf8')
      .split('\n')
      .filter((line) => line.includes('backend-readiness'))
    expect(readinessLines).toHaveLength(1)
    expect(readinessLines[0]).toContain('"outcome":"ready"')
    const state = await stubs.ipc.handlers['fde:getState']()
    expect(state.backend).toBe('error')
  })

  it('serves the settings, the chat CRUD, and the remaining handlers', async () => {
    const { stubs, app, child, conversationId } = await startConfiguredApp(dir)

    // Settings panel fields.
    const settings = await stubs.ipc.handlers['fde:getSettings']()
    expect(settings.hasStoredKey).toBe(true)
    expect(settings.model).toBe('any')
    expect(settings.baseUrl).toBe('https://openrouter.ai/api/v1')
    expect(settings.keyMasked).toContain('••••')

    await stubs.ipc.handlers['fde:setDefaultModel']({ model: 'm2' })
    expect(JSON.parse(fs.readFileSync(path.join(dir, 'config.json'), 'utf8')).model).toBe('m2')

    await stubs.ipc.handlers['fde:setBaseUrl']({ baseUrl: 'http://127.0.0.1:9/v1' })
    expect(JSON.parse(fs.readFileSync(path.join(dir, 'config.json'), 'utf8')).baseUrl).toBe('http://127.0.0.1:9/v1')

    // Conversation CRUD.
    const listed = await stubs.ipc.handlers['fde:listChats']()
    expect(listed).toHaveLength(1)
    const second = await stubs.ipc.handlers['fde:newChat']()
    expect(second.id).not.toBe(conversationId)
    expect((await stubs.ipc.handlers['fde:listChats']())).toHaveLength(2)

    const opened = await stubs.ipc.handlers['fde:openChat']({ id: conversationId })
    expect(opened.id).toBe(conversationId)
    expect(await stubs.ipc.handlers['fde:openChat']({ id: 'nope' })).toBeNull()

    const renamed = await stubs.ipc.handlers['fde:renameChat']({ id: conversationId, title: 'Rust' })
    expect(renamed).toEqual({ ok: true })
    expect(app.history.get(conversationId).title).toBe('Rust')
    expect(await stubs.ipc.handlers['fde:renameChat']({ id: 'nope' })).toEqual({ error: 'No such conversation.' })

    const modelChanged = await stubs.ipc.handlers['fde:changeModel']({ id: conversationId, model: 'm1' })
    expect(modelChanged).toEqual({ ok: true })
    expect(app.history.get(conversationId).model).toBe('m1')
    expect(await stubs.ipc.handlers['fde:changeModel']({ id: 'nope' })).toEqual({ error: 'No such conversation.' })

    // A stop request reaches the backend as chat_stop.
    const stopping = stubs.ipc.handlers['fde:stopStream']({ streamId: 42 })
    await flush()
    const stopRequest = lastRequest(child)
    expect(stopRequest.method).toBe('chat_stop')
    expect(stopRequest.params).toEqual({ stream_id: 42 })
    respond(child, stopRequest.id, { stopping: true })
    await stopping

    // Wizard helpers.
    expect(stubs.ipc.handlers['fde:getWizardState']().state).toBe('done')
    await stubs.ipc.handlers['fde:repeatWizard']()
    expect(app.wizard.snapshot().state).toBe('key')
    // The model list reloads through the backend on demand.
    const loading = stubs.ipc.handlers['fde:listModels']()
    await flush()
    const reloadRequest = lastRequest(child)
    expect(reloadRequest.method).toBe('list_models')
    respond(child, reloadRequest.id, { models: [{ id: 'any', name: 'Any (auto router)' }] })
    await loading
    expect(app.wizard.snapshot().state).toBe('models')
    await stubs.ipc.handlers['fde:cancelWizard']()
    expect(app.wizard.snapshot().state).toBe('cancelled')
  })

  it('keeps the key session-only when encryption is unavailable', async () => {
    const childBox = {}
    const stubs = makeElectronStub(dir, childBox)
    stubs.electron.safeStorage.isEncryptionAvailable = () => false
    const app = await bootstrap(stubs.electron, { arm: stubs.arm, spawn: stubs.spawn })
    await flush()
    const child = childBox.current
    child.emitStdout(readyLine())
    await flush()
    const validated = stubs.ipc.handlers['fde:validateKey']({ key: 'sk-key' })
    await flush()
    respond(child, lastRequest(child).id, { valid: true })
    await flush()
    respond(child, lastRequest(child).id, { models: [] })
    await validated
    await flush()
    // Finish with any while the list is down and encryption is off.
    await stubs.ipc.handlers['fde:finishWizard']()
    expect(fs.existsSync(path.join(dir, 'config.json'))).toBe(false)
    const state = await stubs.ipc.handlers['fde:getState']()
    // The chat works in this session even though nothing persisted, and the
    // user is told about the session-only key.
    expect(state.view).toBe('chat')
    expect(state.notice).toContain('session only')
  })

  it('drops notifications for streams it no longer tracks', async () => {
    const { stubs, app, child, conversationId } = await startConfiguredApp(dir)
    const chatEventsBefore = stubs.sent.filter((s) => s.channel === 'fde:chat-event').length
    emitNotification(child, 'chat/chunk', { stream_id: 999, text: 'ghost' })
    emitNotification(child, 'unrelated', { x: 1 })
    const chatEvents = stubs.sent.filter((s) => s.channel === 'fde:chat-event')
    expect(chatEvents).toHaveLength(chatEventsBefore)

    // A stream error for a live stream surfaces as an error event.
    stubs.ipc.handlers['fde:sendMessage']({ id: conversationId, text: 'hi' })
    await flush()
    const startRequest = lastRequest(child)
    respond(child, startRequest.id, { stream_id: 5 })
    await flush()
    emitNotification(child, 'chat/error', { stream_id: 5, kind: 'network', message: 'stalled' })
    await flush()
    const errorEvents = stubs.sent.filter((s) => s.channel === 'fde:chat-event' && s.payload.type === 'error')
    expect(errorEvents.at(-1).payload).toMatchObject({
      conversationId,
      type: 'error',
      kind: 'network',
      message: 'stalled',
    })
    // The conversation holds the user message with no assistant reply.
    expect(app.history.get(conversationId).messages.at(-1).role).toBe('user')
  })

  it('writes child stderr to the backend log', async () => {
    const { child } = await startConfiguredApp(dir)
    child.emitStderr('backend says hi\n')
    await flush()
    const backendLog = fs.readFileSync(path.join(dir, 'logs', 'backend.log'), 'utf8')
    expect(backendLog).toContain('backend says hi')
  })

  it('hands web links from the window to the system browser', async () => {
    const { stubs } = await startConfiguredApp(dir)
    const win = stubs.windows[0]
    const handler = win.webContents.setWindowOpenHandler.mock.calls[0][0]
    const decision = handler({ url: 'https://example.com/docs' })
    expect(decision).toEqual({ action: 'deny' })
    expect(stubs.electron.shell.openExternal).toHaveBeenCalledWith('https://example.com/docs')
  })

  it('guards the send path and reports the errors', async () => {
    // Backend not ready: the send refuses at once.
    const childBox = {}
    const stubs = makeElectronStub(dir, childBox)
    const app = await bootstrap(stubs.electron, { arm: stubs.arm, spawn: stubs.spawn })
    await flush()
    const early = stubs.ipc.handlers['fde:newChat']()
    expect(stubs.ipc.handlers['fde:sendMessage']({ id: early.id, text: 'hi' })).toEqual({
      error: 'The backend is starting. Try again in a moment.',
    })

    // Ready backend: a duplicate send while a stream runs refuses.
    childBox.current.emitStdout(readyLine())
    await flush()
    const validated = stubs.ipc.handlers['fde:validateKey']({ key: 'sk-key' })
    await flush()
    respond(childBox.current, lastRequest(childBox.current).id, { valid: true })
    await flush()
    respond(childBox.current, lastRequest(childBox.current).id, { models: [] })
    await validated
    await flush()
    await stubs.ipc.handlers['fde:finishWizard']({ model: 'any' })
    expect(stubs.ipc.handlers['fde:sendMessage']({ id: 'nope', text: 'hi' })).toEqual({
      error: 'No such conversation.',
    })

    const state = await stubs.ipc.handlers['fde:getState']()
    stubs.ipc.handlers['fde:sendMessage']({ id: state.active.id, text: 'hi' })
    await flush()
    const startRequest = lastRequest(childBox.current)
    respond(childBox.current, startRequest.id, { stream_id: 7 })
    await flush()
    expect(stubs.ipc.handlers['fde:sendMessage']({ id: state.active.id, text: 'again' })).toEqual({
      error: 'A reply is already streaming in this chat.',
    })
  })

  it('keeps the first title on later messages and refuses empty sends', async () => {
    const { stubs, app, child, conversationId } = await startConfiguredApp(dir)
    expect(stubs.ipc.handlers['fde:sendMessage']({ id: conversationId })).toEqual({
      error: 'Type a message first.',
    })
    stubs.ipc.handlers['fde:sendMessage']({ id: conversationId, text: 'first message' })
    await flush()
    respond(child, lastRequest(child).id, { stream_id: 3 })
    await flush()
    emitNotification(child, 'chat/done', { stream_id: 3, text: 'ok', stopped: false })
    await flush()
    stubs.ipc.handlers['fde:sendMessage']({ id: conversationId, text: 'second message' })
    await flush()
    respond(child, lastRequest(child).id, { stream_id: 4 })
    await flush()
    emitNotification(child, 'chat/done', { stream_id: 4, text: 'ok again', stopped: false })
    await flush()
    const conversation = app.history.get(conversationId)
    expect(conversation.title).toBe('first message')
    expect(conversation.messages).toHaveLength(4)
  })

  it('deletes a background conversation and keeps the active one', async () => {
    const { stubs, app, conversationId } = await startConfiguredApp(dir)
    const second = await stubs.ipc.handlers['fde:newChat']()
    await stubs.ipc.handlers['fde:openChat']({ id: conversationId })
    const result = await stubs.ipc.handlers['fde:deleteChat']({ id: second.id })
    expect(result).toEqual({ ok: true })
    expect(app.history.get(conversationId)).toBeTruthy()
    const state = await stubs.ipc.handlers['fde:getState']()
    expect(state.active.id).toBe(conversationId)
  })

  it('skips the persistence of a done stream whose conversation is gone', async () => {
    const { stubs, app, child, conversationId } = await startConfiguredApp(dir)
    stubs.ipc.handlers['fde:sendMessage']({ id: conversationId, text: 'hi' })
    await flush()
    const startRequest = lastRequest(child)
    respond(child, startRequest.id, { stream_id: 11 })
    await flush()
    fs.rmSync(path.join(dir, 'chats', `${conversationId}.json`))
    emitNotification(child, 'chat/done', { stream_id: 11, text: 'lost', stopped: false })
    await flush()
    const chatEvents = stubs.sent.filter((s) => s.channel === 'fde:chat-event')
    expect(chatEvents.at(-1).payload.type).toBe('done')
  })

  it('fails a pending request when the child dies mid-stream', async () => {
    const { stubs, child, conversationId } = await startConfiguredApp(dir)
    const sendResult = stubs.ipc.handlers['fde:sendMessage']({ id: conversationId, text: 'hi' })
    expect(sendResult).toEqual({ ok: true })
    await flush()
    // The child dies before it can answer chat_start.
    child.exitFn()
    await flush()
    const chatEvents = stubs.sent.filter((s) => s.channel === 'fde:chat-event')
    expect(chatEvents.at(-1).payload).toMatchObject({ conversationId, type: 'error' })
  })

  it('boots with a session that has no default session object', async () => {
    const childBox = {}
    const stubs = makeElectronStub(dir, childBox)
    stubs.electron.session = { webRequest: { onHeadersReceived: vi.fn() } }
    const app = await bootstrap(stubs.electron, { arm: stubs.arm, spawn: stubs.spawn })
    await flush()
    expect(app.manager.state).toBe('starting')
  })

  it('sends the base url with backend requests', async () => {
    const { stubs, child } = await startConfiguredApp(dir)
    const state = await stubs.ipc.handlers['fde:getState']()
    stubs.ipc.handlers['fde:sendMessage']({ id: state.active.id, text: 'hi' })
    await flush()
    const startRequest = lastRequest(child)
    expect(startRequest.method).toBe('chat_start')
    expect(startRequest.params.base_url).toBe('https://openrouter.ai/api/v1')
  })

  it('fails the live streams and frees the conversation when the backend dies', async () => {
    const { stubs, child, conversationId } = await startConfiguredApp(dir)
    stubs.ipc.handlers['fde:sendMessage']({ id: conversationId, text: 'hi' })
    await flush()
    respond(child, lastRequest(child).id, { stream_id: 21 })
    await flush()
    // The backend dies while the stream is live.
    child.exitFn()
    await flush()
    const chatEvents = stubs.sent.filter((s) => s.channel === 'fde:chat-event')
    expect(chatEvents.at(-1).payload).toMatchObject({ conversationId, type: 'error' })
    // The conversation is no longer wedged: the next send is not refused as
    // an already-streaming one.
    const state = await stubs.ipc.handlers['fde:getState']()
    const again = stubs.ipc.handlers['fde:sendMessage']({ id: state.active.id, text: 'again' })
    expect(again.error).not.toBe('A reply is already streaming in this chat.')
  })

  it('prefills the repeated wizard with the stored masked key', async () => {
    const { stubs } = await startConfiguredApp(dir)
    await stubs.ipc.handlers['fde:repeatWizard']()
    const snap = stubs.ipc.handlers['fde:getWizardState']()
    expect(snap.state).toBe('key')
    expect(snap.keyMasked).toContain('••••')
  })

  it('focuses on a second instance and guards the double quit', async () => {
    const { stubs, app, child } = await startConfiguredApp(dir)
    const win = stubs.windows[0]
    const focus = vi.fn()
    win.focus = focus
    stubs.appEvents['second-instance']()
    expect(focus).toHaveBeenCalled()

    // The renderer gets the state once it finishes loading.
    const loadHandler = win.webContents.on.mock.calls.find(([name]) => name === 'did-finish-load')
    expect(loadHandler).toBeTruthy()
    const sentBefore = stubs.sent.length
    loadHandler[1]()
    expect(stubs.sent.length).toBeGreaterThan(sentBefore)

    // A second before-quit pass changes nothing.
    const quitEvent = { preventDefault: vi.fn() }
    stubs.appEvents['before-quit'](quitEvent)
    stubs.appEvents['before-quit'](quitEvent)
    expect(quitEvent.preventDefault).toHaveBeenCalledTimes(1)
    child.exitFn()
    await flush()
    expect(stubs.electron.app.quit).toHaveBeenCalled()
    expect(app.manager.state).toBe('stopped')
  })
})
