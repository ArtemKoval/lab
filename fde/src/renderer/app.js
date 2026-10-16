// The renderer entry. Thin DOM wiring over the pure logic modules and the
// window.fde bridge; no logic of its own beyond rendering.
import {
  applyChatEvent,
  applyUserMessage,
  bubbleList,
  deriveTitle,
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
const chatStates = new Map()

function chatStateFor(conversationId) {
  if (!chatStates.has(conversationId)) {
    chatStates.set(conversationId, emptyChatState())
  }
  return chatStates.get(conversationId)
}

function escapeText(text) {
  const div = document.createElement('div')
  div.textContent = String(text ?? '')
  return div.innerHTML
}

function render() {
  if (!appState) {
    app.innerHTML = '<p class="loading">Starting…</p>'
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
  app.innerHTML = `
    <div class="wizard">
      <h1>Choose a model</h1>
      <p>Step 2 of 2 — pick the default model. <b>Any</b> lets OpenRouter route for you.</p>
      ${view.modelError ? `<p class="error">${escapeText(view.modelError)} <button id="retry">Retry</button></p>` : ''}
      <select id="model-select" size="1">
        ${options.map((m) => `<option value="${escapeText(m.id)}">${escapeText(m.name)}</option>`).join('')}
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
  const state = active ? chatStateFor(active.id) : emptyChatState()
  const bubbles = bubbleList(state)
  app.innerHTML = `
    <div class="layout">
      <aside class="sidebar">
        <button id="new-chat">+ New chat</button>
        <button id="open-settings">⚙ Settings</button>
        <ul id="chat-list">
          ${sidebarModel(appState.conversations, active?.id).map((c) => `
            <li data-id="${c.id}" class="${c.active ? 'active' : ''}">${escapeText(c.title)}</li>`).join('')}
        </ul>
      </aside>
      <main class="chat">
        <header class="chat-header">
          <span>${escapeText(active?.title || 'New chat')}</span>
          <select id="model-badge">
            <option>model: ${escapeText(active?.model ?? '')}</option>
          </select>
        </header>
        <div class="messages" id="messages">
          ${bubbles.map((b) => `
            <div class="bubble ${b.role}">
              ${b.role === 'assistant' ? renderMarkdown(b.content, vendor) : escapeText(b.content)}
              ${b.streaming ? '<span class="cursor">▊</span>' : ''}
            </div>`).join('')}
          ${state.error ? `
            <div class="bubble error">${escapeText(state.error.message)}
              ${state.error.kind === 'auth' ? '<button id="rerun-setup">Run setup again</button>' : ''}
            </div>` : ''}
        </div>
        <footer class="composer">
          <textarea id="composer-input" rows="2" placeholder="Message…"></textarea>
          <button id="send">Send</button>
          <button id="stop" ${state.streaming === null ? 'disabled' : ''}>Stop</button>
        </footer>
        ${appState.backend !== 'ready' ? `<div class="banner">Backend ${escapeText(appState.backend)} — sending is paused.</div>` : ''}
      </main>
    </div>`
  wireChat()
}

function wireChat() {
  const active = appState.active
  app.querySelector('#new-chat').onclick = () => api.newChat()
  app.querySelector('#open-settings').onclick = () => renderSettings()
  for (const item of app.querySelectorAll('#chat-list li')) {
    item.onclick = () => api.openChat({ id: item.dataset.id })
  }
  app.querySelector('#send').onclick = () => sendCurrent()
  app.querySelector('#stop').onclick = () => api.stopStream({})
  app.querySelector('#rerun-setup')?.addEventListener('click', () => api.repeatWizard())
  const input = app.querySelector('#composer-input')
  input.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      sendCurrent()
    }
  })
  function sendCurrent() {
    const text = input.value
    input.value = ''
    if (active) {
      chatStates.set(active.id, applyUserMessage(chatStateFor(active.id), text))
    }
    api.sendMessage({ id: active?.id, text })
    render()
  }
  const messages = app.querySelector('#messages')
  messages.scrollTop = messages.scrollHeight
}

function renderSettings() {
  const view = settingsViewModel(appState.settings)
  app.innerHTML = `
    <div class="wizard">
      <h1>Settings</h1>
      <p>OpenRouter key: <code>${escapeText(view.keyMasked ?? 'not set')}</code> ${view.hasStoredKey ? '(stored)' : ''}</p>
      <label>Default model
        <input id="settings-model" value="${escapeText(view.model)}">
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
  app.querySelector('#back').onclick = () => api.getState().then((next) => {
    appState = next
    render()
  })
}

function applyChatPayload(payload) {
  if (payload.conversationId !== appState?.active?.id) {
    return
  }
  const state = chatStateFor(payload.conversationId)
  chatStates.set(payload.conversationId, applyChatEvent(state, payload))
}

async function refresh() {
  appState = await api.getState()
  wizardSnap = await api.getWizardState()
  render()
}

api.onChatEvent((payload) => {
  applyChatPayload(payload)
  render()
})
api.onAppState((next) => {
  appState = next
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
