// Pure chat window logic: title derivation, message list assembly, and the
// streaming state reducer. No DOM and no IPC here, so tests run in plain node.

export const TITLE_MAX_CHARS = 40

export function deriveTitle(text) {
  const firstLine = String(text ?? '').split('\n')[0].trimStart()
  if (!firstLine) {
    return ''
  }
  return firstLine.slice(0, TITLE_MAX_CHARS)
}

export function emptyChatState() {
  return { messages: [], streaming: null, error: null }
}

export function applyUserMessage(state, text) {
  return {
    ...state,
    messages: [...state.messages, { role: 'user', content: text }],
    error: null,
  }
}

export function applyChatEvent(state, event) {
  if (event.type === 'chunk') {
    return { ...state, streaming: (state.streaming ?? '') + event.text }
  }
  if (event.type === 'done') {
    // A stopped stream lands here too, with the partial text.
    const messages = [...state.messages, { role: 'assistant', content: event.text }]
    return { messages, streaming: null, error: null }
  }
  // event.type === 'error': the user message stays, no assistant reply lands.
  return {
    ...state,
    streaming: null,
    error: { kind: event.kind, message: event.message },
  }
}

export function bubbleList(state) {
  const bubbles = state.messages.map((message) => ({ ...message, streaming: false }))
  if (state.streaming !== null) {
    bubbles.push({ role: 'assistant', content: state.streaming, streaming: true })
  }
  return bubbles
}

// The markdown pipeline: untrusted model output goes through the renderer
// and the sanitizer before it may touch the page.
export function renderMarkdown(text, vendor) {
  const html = vendor.marked.parse(String(text ?? ''))
  return vendor.DOMPurify.sanitize(html)
}

export function sidebarModel(conversations, activeId) {
  return conversations.map((conversation) => ({
    id: conversation.id,
    title: conversation.title || 'New chat',
    active: conversation.id === activeId,
  }))
}
