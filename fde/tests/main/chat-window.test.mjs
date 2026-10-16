import { describe, expect, it, vi } from 'vitest'

import {
  CONTENT_SECURITY_POLICY,
  createChatWindow,
  isWebUrl,
} from '../../src/main/chat-window.mjs'

function makeStubs() {
  const handlers = {}
  const headersReceived = { handler: null }
  const openExternal = vi.fn()
  const webContents = {
    setWindowOpenHandler: (handler) => {
      handlers.windowOpen = handler
    },
    on: (event, handler) => {
      handlers[event] = handler
    },
  }
  class StubWindow {
    constructor(options) {
      StubWindow.lastOptions = options
      this.options = options
      this.webContents = webContents
      this.loaded = null
      this.shown = false
    }

    once(event, fn) {
      handlers[event] = fn
    }

    loadFile(file) {
      this.loaded = file
    }

    show() {
      this.shown = true
    }
  }
  const session = {
    webRequest: {
      onHeadersReceived: (handler) => {
        headersReceived.handler = handler
      },
    },
  }
  return { StubWindow, session, webContents, handlers, headersReceived, openExternal }
}

describe('createChatWindow', () => {
  it('creates the window sandboxed with no Node access and the preload', () => {
    const stubs = makeStubs()
    createChatWindow({
      BrowserWindow: stubs.StubWindow,
      session: stubs.session,
      preloadPath: '/app/preload.cjs',
      rendererFile: '/app/index.html',
      openExternal: stubs.openExternal,
    })
    const prefs = stubs.StubWindow.lastOptions.webPreferences
    expect(prefs.sandbox).toBe(true)
    expect(prefs.contextIsolation).toBe(true)
    expect(prefs.nodeIntegration).toBe(false)
    expect(prefs.preload).toBe('/app/preload.cjs')
  })

  it('loads the renderer and shows on ready', () => {
    const stubs = makeStubs()
    const win = createChatWindow({
      BrowserWindow: stubs.StubWindow,
      session: stubs.session,
      preloadPath: '/app/preload.cjs',
      rendererFile: '/app/index.html',
      openExternal: stubs.openExternal,
    })
    expect(win.loaded).toBe('/app/index.html')
    stubs.handlers['ready-to-show']()
    expect(win.shown).toBe(true)
  })

  it('denies popups and opens web URLs outside', () => {
    const stubs = makeStubs()
    createChatWindow({
      BrowserWindow: stubs.StubWindow,
      session: stubs.session,
      preloadPath: '/app/preload.cjs',
      rendererFile: '/app/index.html',
      openExternal: stubs.openExternal,
    })
    const decision = stubs.handlers.windowOpen({ url: 'https://example.com' })
    expect(decision).toEqual({ action: 'deny' })
    expect(stubs.openExternal).toHaveBeenCalledWith('https://example.com')
    const fileDecision = stubs.handlers.windowOpen({ url: 'file:///etc/passwd' })
    expect(fileDecision).toEqual({ action: 'deny' })
    expect(stubs.openExternal).toHaveBeenCalledTimes(1)
  })

  it('blocks navigation in the window and sends web URLs outside', () => {
    const stubs = makeStubs()
    createChatWindow({
      BrowserWindow: stubs.StubWindow,
      session: stubs.session,
      preloadPath: '/app/preload.cjs',
      rendererFile: '/app/index.html',
      openExternal: stubs.openExternal,
    })
    const event = { prevented: false, preventDefault() { this.prevented = true } }
    stubs.handlers['will-navigate'](event, 'https://example.com')
    expect(event.prevented).toBe(true)
    expect(stubs.openExternal).toHaveBeenCalledWith('https://example.com')
    const second = { prevented: false, preventDefault() { this.prevented = true } }
    stubs.handlers['will-navigate'](second, 'file:///etc/passwd')
    expect(second.prevented).toBe(true)
    expect(stubs.openExternal).toHaveBeenCalledTimes(1)
  })

  it('injects the content security policy header', () => {
    const stubs = makeStubs()
    createChatWindow({
      BrowserWindow: stubs.StubWindow,
      session: stubs.session,
      preloadPath: '/app/preload.cjs',
      rendererFile: '/app/index.html',
      openExternal: stubs.openExternal,
    })
    let sent = null
    stubs.headersReceived.handler(
      { responseHeaders: { 'content-type': ['text/html'] } },
      (result) => {
        sent = result
      },
    )
    expect(sent.responseHeaders['Content-Security-Policy']).toEqual([CONTENT_SECURITY_POLICY])
    expect(CONTENT_SECURITY_POLICY).toContain("script-src 'self'")
  })

  it('classifies web URLs', () => {
    expect(isWebUrl('https://x')).toBe(true)
    expect(isWebUrl('http://x')).toBe(true)
    expect(isWebUrl('file:///x')).toBe(false)
    expect(isWebUrl('javascript:alert(1)')).toBe(false)
  })
})
