// The renderer entry. Thin DOM wiring over the pure logic modules and the
// window.fde bridge; no logic of its own beyond rendering.
import {
  applyChatEvent,
  applyUserMessage,
  bubbleList,
  emptyChatState,
  renderMarkdown,
  sidebarModel,
} from './logic/chat-logic.mjs'
import { settingsViewModel, wizardViewModel } from './logic/wizard-view.mjs'

const vendor = globalThis.fdeVendor
const api = globalThis.fde

const app = document.getElementById('app')
let appState = null
let wizardSnap = null
let models = []
let settingsOpen = false
const chatStates = new Map()
const liveStreams = new Map()

function escapeText(text) {
  const div = document.createElement('div')
  div.textContent = String(text ?? '')
  return div.innerHTML
}

function chatStateFor(conversation) {
  if (!conversation) {
    return emptyChatState()
  }
  if (!chatStates.has(conversation.id)) {
    // Hydrate from the persisted history; streaming state starts empty.
    chatStates.set(conversation.id, { messages: conversation.messages.map((m) => ({ ...m })), streaming: null, error: null })
  }
  return chatStates.get(conversation.id)
}

async function refresh() {
  appState = await api.getState()
  wizardSnap = await api.getWizardState()
  if (appState.settings.hasStoredKey) {
    try {
      await api.listModels()
      wizardSnap = await api.getWizardState()
      models = wizardSnap.models
    } catch {
      models = wizardSnap.models ?? []
    }
  }
  render()
}

function render() {
  if (!appState) {
    app.innerHTML = '<p class="loading">Starting…</p>'
    return
  }
  if (settingsOpen) {
    renderSettings()
    return
  }
  if (appState.view === 'wizard') {
    renderWizard()
    return
  }
  renderChat()
}

function renderWizard() {
  const view = wizardViewModel(wizardSnap ?? { state: 'key', error: null, models: [], modelError: null })
  if (view.step === 1) {
    app.innerHTML = `
      <div class="wizard">
        <h1>Welcome to FDE Chat</h1>
        <p>Step 1 of 2 — paste your OpenRouter API key.</p>
        <input id="key-input" type="password" placeholder="sk-or-v1-…" autocomplete="off">
        <button id="key-continue">Continue</button>
        <p class="error" id="wizard-error"></p>
      </div>`
    app.querySelector('#key-continue').onclick = () => {
      const key = app.querySelector('#key-input').value
      api.validateKey({ key })
    }
    app.querySelector('#wizard-error').textContent = view.error ?? ''
    return
  }
  const options = [{ id: 'any', name: 'Any (auto router)' }, ...view.models.filter((m) => m.id !== 'any')]
  const preselected = wizardSnap?.storedModel ?? 'any'
  app.innerHTML = `
    <div class="wizard">
      <h1>Choose a model</h1>
      <p>Step 2 of 2 — pick the default model. <b>Any</b> lets OpenRouter route for you.</p>
      ${view.modelError ? `<p class="error">${escapeText(view.modelError)} <button id="retry">Retry</button></p>` : ''}
      <select id="model-select" size="1">
        ${options.map((m) => `<option value="${escapeText(m.id)}" ${m.id === preselected ? 'selected' : ''}>${escapeText(m.name)}</option>`).join('')}
      </select>
      <button id="wizard-finish" ${view.busy ? 'disabled' : ''}>Finish</button>
    </div>`
  app.querySelector('#retry')?.addEventListener('click', () => api.listModels())
  app.querySelector('#wizard-finish').onclick = () => {
    api.finishWizard({ model: app.querySelector('#model-select').value })
  }
}

function renderChat() {
  const active = appState.active
  const state = chatStateFor(active)
  const activeStreamId = liveStreams.get(active?.id)
  app.innerHTML = `
    <div class="layout">
      <aside class="sidebar">
        <button id="new-chat">+ New chat</button>
        <button id="open-settings">⚙ Settings</button>
        <ul id="chat-list">
          ${sidebarModel(appState.conversations, active?.id).map((c) => `
            <li data-id="${escapeText(c.id)}" class="${c.active ? 'active' : ''}">
              <span class="chat-title">${escapeText(c.title)}</span>
              <button class="chat-rename" data-id="${escapeText(c.id)}" title="Rename">✎</button>
              <button class="chat-delete" data-id="${escapeText(c.id)}" title="Delete">✕</button>
            </li>`).join('')}
        </ul>
      </aside>
      <main class="chat">
        <header class="chat-header">
          <span>${escapeText(active?.title || 'New chat')}</span>
          <select id="model-picker">
            ${models.length ? models.map((m) => `<option value="${escapeText(m.id)}" ${m.id === active?.model ? 'selected' : ''}>${escapeText(m.id)}</option>`).join('') : `<option>model: ${escapeText(active?.model ?? '')}</option>`}
          </select>
        </header>
        <div class="messages" id="messages"></div>
        <footer class="composer">
          <textarea id="composer-input" rows="2" placeholder="Message…"></textarea>
          <button id="send">Send</button>
          <button id="stop" ${activeStreamId === undefined ? 'disabled' : ''}>Stop</button>
        </footer>
        ${appState.notice ? `<div class="banner">${escapeText(appState.notice)}</div>` : ''}
        ${appState.backend !== 'ready' ? `<div class="banner">Backend ${escapeText(appState.backend)} — sending is paused.</div>` : ''}
      </main>
    </div>`
  wireChat()
  renderMessages()
}

// Updates only the message list, so the composer keeps its draft and focus
// while a reply streams in.
function renderMessages() {
  const container = app.querySelector('#messages')
  if (!container) {
    return
  }
  const active = appState.active
  const state = chatStateFor(active)
  const bubbles = bubbleList(state)
  container.innerHTML = bubbles.map((b) => `
    <div class="bubble ${b.role}">
      ${b.role === 'assistant' ? renderMarkdown(b.content, vendor) : escapeText(b.content)}
      ${b.streaming ? '<span class="cursor">▊</span>' : ''}
    </div>`).join('') + (state.error ? `
    <div class="bubble error">${escapeText(state.error.message)}
      ${state.error.kind === 'auth' ? '<button id="rerun-setup">Run setup again</button>' : ''}
    </div>` : '')
  const stop = app.querySelector('#stop')
  if (stop) {
    stop.disabled = appState?.active ? !liveStreams.has(appState.active.id) : true
  }
  const rerun = container.querySelector('#rerun-setup')
  rerun?.addEventListener('click', () => api.repeatWizard())
  container.scrollTop = container.scrollHeight
}

function wireChat() {
  const active = appState.active
  app.querySelector('#new-chat').onclick = () => api.newChat()
  app.querySelector('#open-settings').onclick = () => {
    settingsOpen = true
    render()
  }
  for (const item of app.querySelectorAll('#chat-list li')) {
    item.onclick = (event) => {
      if (event.target.tagName === 'BUTTON') {
        return
      }
      chatStates.delete(item.dataset.id)
      api.openChat({ id: item.dataset.id })
    }
  }
  for (const button of app.querySelectorAll('.chat-rename')) {
    button.onclick = (event) => {
      event.stopPropagation()
      const id = event.target.dataset.id
      const title = window.prompt('Rename chat', '')
      if (title) {
        api.renameChat({ id, title })
      }
    }
  }
  for (const button of app.querySelectorAll('.chat-delete')) {
    button.onclick = (event) => {
      event.stopPropagation()
      const id = event.target.dataset.id
      if (window.confirm('Delete this conversation?')) {
        chatStates.delete(id)
        api.deleteChat({ id })
      }
    }
  }
  app.querySelector('#model-picker')?.addEventListener('change', (event) => {
    if (active) {
      api.changeModel({ id: active.id, model: event.target.value })
    }
  })
  app.querySelector('#send').onclick = () => sendCurrent()
  app.querySelector('#stop').onclick = () => {
    const streamId = liveStreams.get(active?.id)
    if (streamId !== undefined) {
      api.stopStream({ streamId })
    }
  }
  const input = app.querySelector('#composer-input')
  input.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      sendCurrent()
    }
  })
  const messages = app.querySelector('#messages')
  messages.scrollTop = messages.scrollHeight

  function sendCurrent() {
    const text = input.value
    if (!text.trim()) {
      return
    }
    input.value = ''
    if (active) {
      chatStates.set(active.id, applyUserMessage(chatStateFor(active), text))
      renderMessages()
    }
    const result = api.sendMessage({ id: active?.id, text })
    if (result && result.error) {
      chatStates.set(active.id, applyChatEvent(chatStateFor(active), { type: 'error', kind: 'api', message: result.error }))
      renderMessages()
    }
  }
}

function renderSettings() {
  const view = settingsViewModel(appState.settings)
  const modelOptions = models.length ? models : [{ id: view.model, name: view.model }]
  app.innerHTML = `
    <div class="wizard">
      <h1>Settings</h1>
      <p>OpenRouter key: <code>${escapeText(view.keyMasked ?? 'not set')}</code> ${view.hasStoredKey ? '(stored)' : ''}</p>
      ${appState.notice ? `<p class="error">${escapeText(appState.notice)}</p>` : ''}
      <label>Default model
        <select id="settings-model">
          ${modelOptions.map((m) => `<option value="${escapeText(m.id)}" ${m.id === view.model ? 'selected' : ''}>${escapeText(m.name)}</option>`).join('')}
        </select>
      </label>
      <label>API base URL (advanced)
        <input id="settings-url" value="${escapeText(view.baseUrl)}">
      </label>
      <button id="rerun-wizard">Run setup again</button>
      <button id="back">Back to chat</button>
    </div>`
  app.querySelector('#settings-model').addEventListener('change', (event) => {
    api.setDefaultModel({ model: event.target.value })
  })
  app.querySelector('#settings-url').addEventListener('change', (event) => {
    api.setBaseUrl({ baseUrl: event.target.value })
  })
  app.querySelector('#rerun-wizard').onclick = () => api.repeatWizard()
  app.querySelector('#back').onclick = () => {
    settingsOpen = false
    refresh()
  }
}

function applyChatPayload(payload) {
  if (payload.streamId !== undefined) {
    liveStreams.set(payload.conversationId, payload.streamId)
  }
  if (payload.type !== 'chunk') {
    liveStreams.delete(payload.conversationId)
  }
  if (payload.conversationId !== appState?.active?.id) {
    return
  }
  const state = chatStateFor(appState.active)
  chatStates.set(payload.conversationId, applyChatEvent(state, payload))
}

api.onChatEvent((payload) => {
  applyChatPayload(payload)
  renderMessages()
})
api.onAppState((next) => {
  appState = next
  settingsOpen = false
  render()
})
api.onWizardState((snap) => {
  wizardSnap = snap
  if (snap.state === 'done') {
    refresh()
    return
  }
  render()
})

refresh()
