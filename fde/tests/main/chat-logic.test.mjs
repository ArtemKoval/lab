// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import DOMPurify from 'dompurify'
import { marked } from 'marked'

import {
  TITLE_MAX_CHARS,
  applyChatEvent,
  applyUserMessage,
  bubbleList,
  deriveTitle,
  emptyChatState,
  renderMarkdown,
  sidebarModel,
} from '../../src/renderer/logic/chat-logic.mjs'

const vendor = { marked, DOMPurify }

describe('deriveTitle', () => {
  it('takes the first line cut to 40 characters', () => {
    const long = 'x'.repeat(100)
    expect(deriveTitle(long)).toBe('x'.repeat(TITLE_MAX_CHARS))
    expect(TITLE_MAX_CHARS).toBe(40)
  })

  it('keeps only the first line', () => {
    expect(deriveTitle('Explain streams in Rust\nmore text')).toBe('Explain streams in Rust')
  })

  it('gives an empty string for empty input', () => {
    expect(deriveTitle('')).toBe('')
    expect(deriveTitle('\n\n')).toBe('')
    expect(deriveTitle(null)).toBe('')
    expect(deriveTitle(undefined)).toBe('')
  })
})

describe('applyUserMessage and applyChatEvent', () => {
  it('appends the user message and clears the error', () => {
    const state = applyUserMessage({ ...emptyChatState(), error: { kind: 'api', message: 'x' } }, 'hi')
    expect(state.messages).toEqual([{ role: 'user', content: 'hi' }])
    expect(state.error).toBeNull()
  })

  it('grows the streaming text with each chunk', () => {
    let state = emptyChatState()
    state = applyChatEvent(state, { type: 'chunk', text: 'Hello' })
    state = applyChatEvent(state, { type: 'chunk', text: ' world' })
    expect(state.streaming).toBe('Hello world')
    expect(state.messages).toEqual([])
  })

  it('lands the streamed text as the assistant message on done', () => {
    let state = applyChatEvent(emptyChatState(), { type: 'chunk', text: 'Hi' })
    state = applyChatEvent(state, { type: 'done', text: 'Hi there', stopped: false })
    expect(state.messages).toEqual([{ role: 'assistant', content: 'Hi there' }])
    expect(state.streaming).toBeNull()
  })

  it('keeps partial text when a stream stops', () => {
    let state = applyChatEvent(emptyChatState(), { type: 'chunk', text: 'partial' })
    state = applyChatEvent(state, { type: 'done', text: 'partial', stopped: true })
    expect(state.messages).toEqual([{ role: 'assistant', content: 'partial' }])
  })

  it('keeps the user message and shows the error on failure', () => {
    let state = applyUserMessage(emptyChatState(), 'hi')
    state = applyChatEvent(state, { type: 'error', kind: 'rate', message: 'slow down' })
    expect(state.messages).toEqual([{ role: 'user', content: 'hi' }])
    expect(state.error).toEqual({ kind: 'rate', message: 'slow down' })
    expect(state.streaming).toBeNull()
  })
})

describe('bubbleList', () => {
  it('marks the streaming bubble and hides the null stream', () => {
    let state = applyUserMessage(emptyChatState(), 'hi')
    expect(bubbleList(state)).toEqual([{ role: 'user', content: 'hi', streaming: false }])
    state = applyChatEvent(state, { type: 'chunk', text: 'He' })
    expect(bubbleList(state)).toEqual([
      { role: 'user', content: 'hi', streaming: false },
      { role: 'assistant', content: 'He', streaming: true },
    ])
  })
})

describe('renderMarkdown', () => {
  it('renders a fenced code block as a code element', () => {
    const html = renderMarkdown('```rust\nfn x() {}\n```', vendor)
    expect(html).toContain('<code')
  })

  it('removes a script element from the reply', () => {
    const html = renderMarkdown('hello <script>alert(1)</script>', vendor)
    expect(html).not.toContain('<script')
    expect(html).toContain('hello')
  })

  it('removes an inline event handler from the reply', () => {
    const html = renderMarkdown('<img src="x.png" onclick="alert(1)">', vendor)
    expect(html).not.toContain('onclick')
  })

  it('removes a javascript URL from the reply', () => {
    const html = renderMarkdown('[click](javascript:alert(1))', vendor)
    expect(html).not.toContain('javascript:')
  })

  it('renders empty output for absent text', () => {
    expect(renderMarkdown(undefined, vendor)).toBe('')
  })
})

describe('sidebarModel', () => {
  it('lists conversations and marks the active one, defaulting empty titles', () => {
    const conversations = [
      { id: 'a', title: '' },
      { id: 'b', title: 'Rust' },
    ]
    expect(sidebarModel(conversations, 'b')).toEqual([
      { id: 'a', title: 'New chat', active: false },
      { id: 'b', title: 'Rust', active: true },
    ])
  })
})
