// The sandboxed preload. Sandboxed preloads are CommonJS, so this file stays
// standalone: one narrow whitelist of invoke methods, two event streams, and
// nothing else. The renderer never sees ipcRenderer itself.

const INVOKE_METHODS = [
  'getState',
  'getWizardState',
  'validateKey',
  'listModels',
  'finishWizard',
  'cancelWizard',
  'getSettings',
  'setDefaultModel',
  'setBaseUrl',
  'newChat',
  'listChats',
  'openChat',
  'renameChat',
  'deleteChat',
  'changeModel',
  'sendMessage',
  'stopStream',
]

const EVENTS = ['fde:chat-event', 'fde:app-state', 'fde:wizard-state']

function createFdeApi(electron) {
  const { contextBridge, ipcRenderer } = electron
  const api = {}
  for (const method of INVOKE_METHODS) {
    api[method] = (payload) => ipcRenderer.invoke(`fde:${method}`, payload)
  }
  for (const event of EVENTS) {
    const camel = event.slice(4).replace(/-([a-z])/g, (m, c) => c.toUpperCase())
    const methodName = 'on' + camel[0].toUpperCase() + camel.slice(1)
    api[methodName] = (callback) => {
      const listener = (_event, data) => callback(data)
      ipcRenderer.on(event, listener)
      return () => ipcRenderer.removeListener(event, listener)
    }
  }
  contextBridge.exposeInMainWorld('fde', api)
  return api
}

module.exports = { createFdeApi, INVOKE_METHODS, EVENTS }

// Auto-run only inside a real Electron preload, never under the test runner.
/* v8 ignore next 3 -- process.versions.electron exists only in the real
   preload context; the factory above is the tested surface. */
if (typeof process !== 'undefined' && process.versions && process.versions.electron) {
  createFdeApi(require('electron'))
}
