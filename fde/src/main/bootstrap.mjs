// The application wiring. Every Electron surface arrives as a parameter, so
// the integration tests run the whole app over stubs with a stub backend
// child and never launch a real Electron process.

import { spawn as nodeSpawn } from 'node:child_process'
import path from 'node:path'

import { backendCommand, venvPythonPath } from './backend-command.mjs'
import { createBackendManager } from './backend-manager.mjs'
import { createChatWindow } from './chat-window.mjs'
import { createConfigStore } from './config-store.mjs'
import { createHistoryStore } from './history-store.mjs'
import { createRotatingLogWriter } from './log-writer.mjs'
import { createSettingsState, createWizardState } from './wizard-state.mjs'
import { deriveTitle } from '../renderer/logic/chat-logic.mjs'

/* v8 ignore next 3 -- this shells out to the Windows-only taskkill; the
   manager's kill ladder is covered with an injected killTree stub. */
function killTree(pid) {
  nodeSpawn('taskkill', ['/PID', String(pid), '/T', '/F'])
}

export async function bootstrap(electron, overrides = {}) {
  const {
    app,
    BrowserWindow,
    ipcMain,
    safeStorage,
    session,
    shell,
  } = electron

  /* v8 ignore next 2 -- the override exists for the e2e driver, which runs
     the real app against a throwaway user data folder. It must come before
     the single-instance lock, so a test instance never collides with the
     lock of the user's real installation. */
  if (process.env.FDE_USER_DATA) {
    app.setPath('userData', process.env.FDE_USER_DATA)
  }

  if (!app.requestSingleInstanceLock()) {
    app.quit()
    return null
  }

  const userData = app.getPath('userData')
  const appDir = app.getAppPath()
  const paths = {
    configFile: path.join(userData, 'config.json'),
    chatsDir: path.join(userData, 'chats'),
    mainLog: path.join(userData, 'logs', 'main.log'),
    backendLog: path.join(userData, 'logs', 'backend.log'),
  }
  const mainLog = createRotatingLogWriter({ file: paths.mainLog })
  const backendLog = createRotatingLogWriter({ file: paths.backendLog })

  let win = null
  let activeId = null
  let quitting = false
  let wizardDone = false
  let readinessWritten = false
  let sessionKeyNotice = null
  // Both stores bind after the ready event (safeStorage needs it); the
  // closures below read them at call time.
  let config
  let history
  const streams = new Map()
  const streamByConversation = new Map()

  function sendToRenderer(channel, payload) {
    if (win && !win.isDestroyed?.()) {
      win.webContents.send(channel, payload)
    }
  }

  function broadcastAppState() {
    sendToRenderer('fde:app-state', appState())
  }

  function writeReadiness(outcome) {
    if (readinessWritten) {
      return
    }
    readinessWritten = true
    mainLog.write(JSON.stringify({ event: 'backend-readiness', outcome }))
  }

  const manager = createBackendManager({
    options: {
      isPackaged: app.isPackaged,
      resourcesPath: process.resourcesPath,
      venvPython: venvPythonPath(appDir, process.platform),
      backendDir: path.join(appDir, 'backend'),
    },
    /* v8 ignore next 1 -- every test injects the stub spawn; the node
       default binds only in the real app. */
    spawn: overrides.spawn ?? nodeSpawn,
    killTree: overrides.killTree ?? killTree,
    platform: process.platform,
    arm: overrides.arm,
    onLog: (line, source) => {
      if (source === 'backend') {
        backendLog.write(line)
      }
      mainLog.write(`[${source}] ${line}`)
    },
    onNotification: (method, params) => routeNotification(method, params),
    onStateChange: (state) => {
      if (state === 'ready') {
        writeReadiness('ready')
      }
      if (state === 'error') {
        writeReadiness('start-failed')
      }
      if (state === 'restarting' || state === 'error') {
        failLiveStreams()
      }
      broadcastAppState()
    },
  })

  const wizard = createWizardState({
    validateKey: (key) => manager.request('validate_key', { key, base_url: config.snapshot().baseUrl }),
    listModels: () =>
      manager.request('list_models', { base_url: config.snapshot().baseUrl }).then((r) => r.models),
    finish: ({ key, model }) => {
      const result = config.storeSetup({ key, model })
      wizardDone = true
      if (!result.persisted) {
        sessionKeyNotice =
          'Encryption is not available here, so the key is kept for this session only. You will be asked again at the next launch.'
      }
      ensureActiveConversation()
      return result
    },
    notify: (snap) => sendToRenderer('fde:wizard-state', snap),
  })

  function ensureActiveConversation() {
    if (activeId && history.get(activeId)) {
      return history.get(activeId)
    }
    const conversation = history.create(config.snapshot().model)
    activeId = conversation.id
    return conversation
  }

  function failLiveStreams() {
    // The backend died with streams in flight: end each one with an error so
    // no conversation stays wedged in a "reply already streaming" state.
    for (const [streamId, conversationId] of [...streams]) {
      releaseStream(streamId)
      pushChatEvent(conversationId, {
        type: 'error',
        kind: 'api',
        message: 'The backend stopped. Send the message again.',
      })
    }
  }

  function appState() {
    return {
      view: config.canSkipWizard() || wizardDone ? 'chat' : 'wizard',
      backend: manager.state,
      settings: settings.get(),
      conversations: history.list(),
      notice: sessionKeyNotice,
      /* v8 ignore next 1 -- every broadcast runs after a conversation exists;
         the null branch covers a same-tick delete-and-broadcast race only. */
      active: activeId ? history.get(activeId) : null,
    }
  }

  function routeNotification(method, params) {
    if (!method.startsWith('chat/')) {
      return
    }
    const conversationId = streams.get(params.stream_id)
    if (conversationId === undefined) {
      // Events for a stream this app no longer tracks are dropped.
      return
    }
    const type = method.slice(5)
    if (type === 'chunk') {
      pushChatEvent(conversationId, { type: 'chunk', streamId: params.stream_id, text: params.text })
      return
    }
    if (type === 'error') {
      releaseStream(params.stream_id)
      pushChatEvent(conversationId, { type: 'error', kind: params.kind, message: params.message })
      return
    }
    const conversation = history.get(conversationId)
    if (conversation) {
      conversation.messages.push({ role: 'assistant', content: params.text })
      history.save(conversation)
    }
    releaseStream(params.stream_id)
    pushChatEvent(conversationId, { type: 'done', text: params.text, stopped: params.stopped })
  }

  function releaseStream(streamId) {
    const conversationId = streams.get(streamId)
    streams.delete(streamId)
    /* v8 ignore next 2 -- the mapping is only replaced through this function,
       so a mismatch needs a same-tick double release that cannot occur. */
    if (streamByConversation.get(conversationId) === streamId) {
      streamByConversation.delete(conversationId)
    }
  }

  function pushChatEvent(conversationId, event) {
    sendToRenderer('fde:chat-event', { conversationId, ...event })
  }

  function sendMessage(conversationId, text) {
    mainLog.write(`[app] send requested for ${conversationId} (${text.length} chars)`)
    if (manager.state !== 'ready') {
      return { error: 'The backend is starting. Try again in a moment.' }
    }
    if (!text) {
      return { error: 'Type a message first.' }
    }
    const conversation = history.get(conversationId)
    if (!conversation) {
      return { error: 'No such conversation.' }
    }
    if (streamByConversation.has(conversationId)) {
      return { error: 'A reply is already streaming in this chat.' }
    }
    conversation.messages.push({ role: 'user', content: text })
    if (!conversation.title) {
      conversation.title = deriveTitle(text)
    }
    history.save(conversation)
    const key = config.snapshot().keyPlaintext
    const base_url = config.snapshot().baseUrl
    manager.request('chat_start', { key, model: conversation.model, messages: conversation.messages, base_url })
      .then(({ stream_id }) => {
        streams.set(stream_id, conversationId)
        streamByConversation.set(conversationId, stream_id)
      })
      .catch((err) => {
        /* v8 ignore next 1 -- every rejection this sees is a BackendError with
           a kind; the fallback covers a plain Error from the ready guard. */
        pushChatEvent(conversationId, { type: 'error', kind: err.kind ?? 'api', message: err.message })
      })
    return { ok: true }
  }

  function deleteChat(conversationId) {
    history.remove(conversationId)
    if (activeId === conversationId) {
      activeId = null
      ensureActiveConversation()
    }
    broadcastAppState()
    return { ok: true }
  }

  function renameChat(conversationId, title) {
    const conversation = history.get(conversationId)
    if (!conversation) {
      return { error: 'No such conversation.' }
    }
    conversation.title = title
    history.save(conversation)
    broadcastAppState()
    return { ok: true }
  }

  function changeModel(conversationId, model) {
    const conversation = history.get(conversationId)
    if (!conversation) {
      return { error: 'No such conversation.' }
    }
    conversation.model = model
    history.save(conversation)
    broadcastAppState()
    return { ok: true }
  }

  const handlers = {
    getState: () => appState(),
    validateKey: (payload) => wizard.submitKey(payload?.key),
    listModels: () => wizard.loadModels(),
    finishWizard: (payload) => wizard.finish(payload?.model ?? 'any'),
    cancelWizard: () => wizard.cancel(),
    repeatWizard: () => settings.startWizard(),
    getSettings: () => settings.get(),
    setDefaultModel: (payload) => settings.setDefaultModel(payload?.model),
    setBaseUrl: (payload) => settings.setBaseUrl(payload?.baseUrl),
    newChat: () => {
      const conversation = history.create(config.snapshot().model)
      activeId = conversation.id
      broadcastAppState()
      return conversation
    },
    listChats: () => history.list(),
    openChat: (payload) => {
      const conversation = history.get(payload?.id)
      if (conversation) {
        activeId = conversation.id
      }
      return conversation
    },
    renameChat: (payload) => renameChat(payload?.id, payload?.title ?? ''),
    deleteChat: (payload) => deleteChat(payload?.id),
    changeModel: (payload) => changeModel(payload?.id, payload?.model),
    sendMessage: (payload) => sendMessage(payload?.id, payload?.text ?? ''),
    stopStream: (payload) => manager.request('chat_stop', { stream_id: payload?.streamId }),
    getWizardState: () => wizard.snapshot(),
  }

  for (const [name, handler] of Object.entries(handlers)) {
    ipcMain.handle(`fde:${name}`, (_event, payload) => {
      if (name === 'sendMessage') {
        mainLog.write(`[ipc] sendMessage received`)
      }
      return handler(payload)
    })
  }

  app.on('second-instance', () => {
    /* v8 ignore next 2 -- the window exists from whenReady on, so the null
       guard only covers a second-instance signal during boot. */
    if (win) {
      win.focus()
    }
  })

  app.on('before-quit', (event) => {
    if (quitting) {
      return
    }
    quitting = true
    event.preventDefault()
    manager.stop().then(() => app.quit())
  })

  await app.whenReady()

  config = createConfigStore({ configFile: paths.configFile, safeStorage })
  history = createHistoryStore({ chatsDir: paths.chatsDir })
  const settings = createSettingsState({
    store: config,
    startWizard: () =>
      wizard.reset({ keyMasked: config.snapshot().keyMasked, model: config.snapshot().model }),
  })

  ensureActiveConversation()
  manager.start()
  win = createChatWindow({
    BrowserWindow,
    session: session.defaultSession ?? session,
    preloadPath: path.join(appDir, 'src', 'preload', 'preload.cjs'),
    rendererFile: path.join(appDir, 'src', 'renderer', 'index.html'),
    openExternal: (url) => shell.openExternal(url),
  })
  win.webContents.on('did-finish-load', () => {
    sendToRenderer('fde:app-state', appState())
    sendToRenderer('fde:wizard-state', wizard.snapshot())
  })

  return {
    manager,
    config,
    history,
    wizard,
    settings,
    appState,
    paths,
  }
}
