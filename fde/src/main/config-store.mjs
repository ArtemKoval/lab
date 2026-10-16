// The encrypted configuration: API key ciphertext, default model, base URL,
// and the setup-done mark, in one file in the user data folder. Decryption
// and encryption stay in the main process; the renderer only ever sees a
// masked key. Weak or unavailable OS storage keeps the key out of the file.

import fsSync from 'node:fs'
import path from 'node:path'

export const DEFAULT_BASE_URL = 'https://openrouter.ai/api/v1'
export const DEFAULT_MODEL = 'any'
const MASK = '••••'

export function maskKey(key) {
  if (!key || key.length <= 4) {
    return MASK
  }
  return MASK + key.slice(-4)
}

export function encryptionUsable(safeStorage) {
  if (typeof safeStorage.isEncryptionAvailable !== 'function') {
    return false
  }
  if (!safeStorage.isEncryptionAvailable()) {
    return false
  }
  if (typeof safeStorage.getSelectedStorageBackend === 'function') {
    if (safeStorage.getSelectedStorageBackend() === 'basic_text') {
      return false
    }
  }
  return true
}

function writeAtomically(fs, file, payload) {
  const tmp = file + '.tmp'
  fs.writeFileSync(tmp, JSON.stringify(payload, null, 2))
  fs.renameSync(tmp, file)
}

export function createConfigStore({ configFile, safeStorage, fs = fsSync }) {
  let state = {
    setupDone: false,
    model: DEFAULT_MODEL,
    baseUrl: DEFAULT_BASE_URL,
    keyPlaintext: null,
    keyMasked: null,
  }

  function raw() {
    try {
      return JSON.parse(fs.readFileSync(configFile, 'utf8'))
    } catch {
      return {}
    }
  }

  function persist(rawData) {
    fs.mkdirSync(path.dirname(configFile), { recursive: true })
    writeAtomically(fs, configFile, rawData)
  }

  function decryptedKey(data) {
    if (!data.keyCiphertext || !encryptionUsable(safeStorage)) {
      return null
    }
    try {
      return safeStorage.decryptString(Buffer.from(data.keyCiphertext, 'base64'))
    } catch {
      // A keychain reset or a reinstall makes old ciphertext unreadable.
      const cleaned = { ...data }
      delete cleaned.keyCiphertext
      persist(cleaned)
      return null
    }
  }

  function load() {
    const data = raw()
    const keyPlaintext = decryptedKey(data)
    state = {
      setupDone: data.setupDone === true,
      model: data.model || DEFAULT_MODEL,
      baseUrl: data.baseUrl || DEFAULT_BASE_URL,
      keyPlaintext,
      keyMasked: keyPlaintext ? maskKey(keyPlaintext) : null,
    }
    return { ...state }
  }

  function snapshot() {
    return { ...state }
  }

  function canSkipWizard() {
    return state.setupDone && state.keyPlaintext !== null
  }

  function currentRaw() {
    const data = raw()
    return {
      keyCiphertext: data.keyCiphertext,
      model: state.model,
      baseUrl: state.baseUrl,
      setupDone: state.setupDone,
    }
  }

  function storeSetup({ key, model }) {
    if (!encryptionUsable(safeStorage)) {
      // Session-only key: nothing is written, the next launch shows the wizard.
      state.keyPlaintext = key
      state.keyMasked = maskKey(key)
      state.model = model
      return { persisted: false }
    }
    const ciphertext = safeStorage.encryptString(key).toString('base64')
    state.model = model
    state.setupDone = true
    state.keyPlaintext = key
    state.keyMasked = maskKey(key)
    persist({ ...currentRaw(), keyCiphertext: ciphertext, setupDone: true })
    return { persisted: true }
  }

  function setDefaultModel(model) {
    state.model = model
    persist(currentRaw())
    return snapshot()
  }

  function setBaseUrl(baseUrl) {
    state.baseUrl = baseUrl
    persist(currentRaw())
    return snapshot()
  }

  load()
  return { load, snapshot, canSkipWizard, storeSetup, setDefaultModel, setBaseUrl }
}
