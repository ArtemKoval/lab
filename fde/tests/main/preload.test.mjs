import { describe, expect, it, vi } from 'vitest'

import { EVENTS, INVOKE_METHODS, createFdeApi } from '../../src/preload/preload.cjs'

function makeElectron() {
  const exposed = {}
  const contextBridge = { exposeInMainWorld: (name, api) => { exposed[name] = api } }
  const ipcRenderer = {
    invoke: vi.fn(async (channel, payload) => ({ channel, payload })),
    on: vi.fn(),
    removeListener: vi.fn(),
  }
  return { electron: { contextBridge, ipcRenderer }, exposed, ipcRenderer }
}

describe('createFdeApi', () => {
  it('exposes one narrow api object named fde', () => {
    const { electron, exposed } = makeElectron()
    createFdeApi(electron)
    expect(Object.keys(exposed)).toEqual(['fde'])
  })

  it('offers exactly the whitelisted invoke methods', () => {
    const { electron, exposed } = makeElectron()
    const api = createFdeApi(electron)
    expect(Object.keys(api).filter((key) => !key.startsWith('on'))).toEqual(INVOKE_METHODS)
  })

  it('routes each method to its fde-prefixed channel', async () => {
    const { electron, exposed, ipcRenderer } = makeElectron()
    const api = createFdeApi(electron)
    const result = await api.validateKey({ key: 'sk-key' })
    expect(ipcRenderer.invoke).toHaveBeenCalledWith('fde:validateKey', { key: 'sk-key' })
    expect(result.channel).toBe('fde:validateKey')
  })

  it('subscribes to the event streams and unsubscribes', () => {
    const { electron, exposed, ipcRenderer } = makeElectron()
    const api = createFdeApi(electron)
    expect(api.onChatEvent).toBeTypeOf('function')
    expect(api.onAppState).toBeTypeOf('function')
    expect(api.onWizardState).toBeTypeOf('function')
    const seen = []
    const unsubscribe = api.onChatEvent((data) => seen.push(data))
    const [event, listener] = ipcRenderer.on.mock.calls[0]
    expect(event).toBe('fde:chat-event')
    listener(undefined, { type: 'chunk', text: 'a' })
    expect(seen).toEqual([{ type: 'chunk', text: 'a' }])
    unsubscribe()
    expect(ipcRenderer.removeListener).toHaveBeenCalledWith('fde:chat-event', listener)
  })

  it('declares exactly the three event streams', () => {
    expect(EVENTS).toEqual(['fde:chat-event', 'fde:app-state', 'fde:wizard-state'])
  })
})
