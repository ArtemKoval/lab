import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'

import { beforeEach, describe, expect, it } from 'vitest'

import {
  DEFAULT_BASE_URL,
  DEFAULT_MODEL,
  createConfigStore,
  encryptionUsable,
  maskKey,
} from '../../src/main/config-store.mjs'

const KEY = 'sk-or-v1-1234567890abcdef'

function goodSafeStorage() {
  return {
    isEncryptionAvailable: () => true,
    encryptString: (text) => Buffer.from(`enc:${text}`, 'utf8'),
    decryptString: (buffer) => {
      const text = buffer.toString('utf8')
      if (!text.startsWith('enc:')) {
        throw new Error('cannot decrypt')
      }
      return text.slice(4)
    },
  }
}

let dir
let configFile

beforeEach(() => {
  dir = fs.mkdtempSync(path.join(os.tmpdir(), 'fde-config-'))
  configFile = path.join(dir, 'config.json')
})

describe('maskKey', () => {
  it('shows only the last four characters', () => {
    expect(maskKey(KEY)).toBe('••••cdef')
  })

  it('masks short keys fully', () => {
    expect(maskKey('abc')).toBe('••••')
    expect(maskKey('')).toBe('••••')
  })
})

describe('encryptionUsable', () => {
  it('accepts a working backend', () => {
    expect(encryptionUsable(goodSafeStorage())).toBe(true)
  })

  it('refuses when encryption is unavailable', () => {
    const safeStorage = { isEncryptionAvailable: () => false }
    expect(encryptionUsable(safeStorage)).toBe(false)
  })

  it('refuses a safeStorage without the availability probe', () => {
    expect(encryptionUsable({})).toBe(false)
  })

  it('refuses the basic_text fallback backend', () => {
    const safeStorage = {
      ...goodSafeStorage(),
      getSelectedStorageBackend: () => 'basic_text',
    }
    expect(encryptionUsable(safeStorage)).toBe(false)
  })

  it('accepts a real backend selected on Linux', () => {
    const safeStorage = {
      ...goodSafeStorage(),
      getSelectedStorageBackend: () => 'kwallet',
    }
    expect(encryptionUsable(safeStorage)).toBe(true)
  })
})

describe('createConfigStore', () => {
  it('starts with defaults when no file exists', () => {
    const store = createConfigStore({ configFile, safeStorage: goodSafeStorage() })
    expect(store.snapshot()).toEqual({
      setupDone: false,
      model: DEFAULT_MODEL,
      baseUrl: DEFAULT_BASE_URL,
      keyPlaintext: null,
      keyMasked: null,
    })
    expect(store.canSkipWizard()).toBe(false)
  })

  it('stores the key encrypted with the model and the setup mark', () => {
    const store = createConfigStore({ configFile, safeStorage: goodSafeStorage() })
    const result = store.storeSetup({ key: KEY, model: 'm1' })
    expect(result).toEqual({ persisted: true })
    const fileText = fs.readFileSync(configFile, 'utf8')
    expect(fileText).not.toContain(KEY)
    expect(JSON.parse(fileText).setupDone).toBe(true)

    const reloaded = createConfigStore({ configFile, safeStorage: goodSafeStorage() })
    expect(reloaded.snapshot().keyPlaintext).toBe(KEY)
    expect(reloaded.snapshot().keyMasked).toBe(maskKey(KEY))
    expect(reloaded.canSkipWizard()).toBe(true)
  })

  it('keeps the key session-only when encryption is unavailable', () => {
    const safeStorage = { isEncryptionAvailable: () => false }
    const store = createConfigStore({ configFile, safeStorage })
    const result = store.storeSetup({ key: KEY, model: 'any' })
    expect(result).toEqual({ persisted: false })
    expect(fs.existsSync(configFile)).toBe(false)
    expect(store.snapshot().keyMasked).toBe(maskKey(KEY))
    expect(store.canSkipWizard()).toBe(false)
  })

  it('keeps the key session-only on the basic_text backend', () => {
    const safeStorage = {
      ...goodSafeStorage(),
      getSelectedStorageBackend: () => 'basic_text',
    }
    const store = createConfigStore({ configFile, safeStorage })
    expect(store.storeSetup({ key: KEY, model: 'any' })).toEqual({ persisted: false })
    expect(fs.existsSync(configFile)).toBe(false)
  })

  it('treats an undecryptable key as absent and deletes the ciphertext', () => {
    fs.writeFileSync(configFile, JSON.stringify({
      keyCiphertext: Buffer.from('corrupted-junk', 'utf8').toString('base64'),
      model: 'm1',
      setupDone: true,
    }))
    const store = createConfigStore({ configFile, safeStorage: goodSafeStorage() })
    expect(store.snapshot().keyPlaintext).toBeNull()
    expect(store.canSkipWizard()).toBe(false)
    const onDisk = JSON.parse(fs.readFileSync(configFile, 'utf8'))
    expect(onDisk.keyCiphertext).toBeUndefined()
    expect(onDisk.model).toBe('m1')
  })

  it('persists a default model change at once', () => {
    const store = createConfigStore({ configFile, safeStorage: goodSafeStorage() })
    store.setDefaultModel('openai/gpt-4o-mini')
    expect(JSON.parse(fs.readFileSync(configFile, 'utf8')).model).toBe('openai/gpt-4o-mini')
    expect(store.snapshot().model).toBe('openai/gpt-4o-mini')
  })

  it('persists a base URL override at once', () => {
    const store = createConfigStore({ configFile, safeStorage: goodSafeStorage() })
    store.setBaseUrl('http://127.0.0.1:9/v1')
    expect(JSON.parse(fs.readFileSync(configFile, 'utf8')).baseUrl).toBe('http://127.0.0.1:9/v1')
    expect(store.load().baseUrl).toBe('http://127.0.0.1:9/v1')
  })

  it('falls back to defaults on a corrupt file', () => {
    fs.writeFileSync(configFile, '{broken json')
    const store = createConfigStore({ configFile, safeStorage: goodSafeStorage() })
    expect(store.snapshot().setupDone).toBe(false)
    expect(store.snapshot().baseUrl).toBe(DEFAULT_BASE_URL)
  })
})
