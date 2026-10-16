import { describe, expect, it, vi } from 'vitest'

import { createSettingsState, createWizardState } from '../../src/main/wizard-state.mjs'

function flush() {
  return new Promise((resolve) => setImmediate(resolve))
}

function makeWizard({ validateError = null, modelsError = null } = {}) {
  const events = []
  const finished = []
  const validateKey = vi.fn(async () => {
    if (validateError) {
      throw new Error(validateError)
    }
  })
  const listModels = vi.fn(async () => {
    if (modelsError) {
      throw new Error(modelsError)
    }
    return [
      { id: 'any', name: 'Any (auto router)' },
      { id: 'm1', name: 'Model One' },
    ]
  })
  const finish = vi.fn(async ({ key, model }) => {
    finished.push({ key, model })
  })
  const wizard = createWizardState({
    validateKey,
    listModels,
    finish,
    notify: (snap) => events.push(snap),
  })
  return { wizard, events, validateKey, listModels, finish, finished }
}

describe('createWizardState', () => {
  it('rejects an empty key without a validation call', async () => {
    const { wizard, validateKey } = makeWizard()
    await wizard.submitKey('')
    expect(wizard.snapshot().error).toBe('Enter your OpenRouter API key')
    expect(wizard.snapshot().state).toBe('key')
    expect(validateKey).not.toHaveBeenCalled()
  })

  it('moves to the model step and loads the list for a valid key', async () => {
    const { wizard, events } = makeWizard()
    await wizard.submitKey('sk-key')
    expect(wizard.snapshot().state).toBe('models')
    expect(wizard.snapshot().models).toHaveLength(2)
    expect(events.map((e) => e.state)).toEqual(['validating', 'models', 'models-loading', 'models'])
  })

  it('returns to the key step with the API error for a rejected key', async () => {
    const { wizard } = makeWizard({ validateError: 'Invalid key' })
    await wizard.submitKey('sk-bad')
    expect(wizard.snapshot().state).toBe('key')
    expect(wizard.snapshot().error).toBe('Invalid key')
  })

  it('lands on models-failed with the reason and still finishes with any', async () => {
    const { wizard, finished } = makeWizard({ modelsError: 'no route' })
    await wizard.submitKey('sk-key')
    expect(wizard.snapshot().state).toBe('models-failed')
    expect(wizard.snapshot().modelError).toBe('no route')
    await wizard.finish('any')
    expect(wizard.snapshot().state).toBe('done')
    expect(finished).toEqual([{ key: 'sk-key', model: 'any' }])
  })

  it('gives the held key to the finish action', async () => {
    const { wizard, finished } = makeWizard()
    await wizard.submitKey('sk-key')
    await wizard.finish('m1')
    expect(finished).toEqual([{ key: 'sk-key', model: 'm1' }])
    expect(wizard.snapshot().state).toBe('done')
  })

  it('retries the model list on demand', async () => {
    const { wizard, listModels } = makeWizard({ modelsError: 'no route' })
    await wizard.submitKey('sk-key')
    expect(wizard.snapshot().state).toBe('models-failed')
    // The API recovers; the retry then lands on the model list.
    listModels.mockImplementation(async () => [{ id: 'any', name: 'Any (auto router)' }])
    await wizard.loadModels()
    expect(wizard.snapshot().state).toBe('models')
    expect(wizard.snapshot().models).toHaveLength(1)
    expect(listModels).toHaveBeenCalledTimes(2)
  })

  it('ends cancelled on cancel', async () => {
    const { wizard } = makeWizard()
    wizard.cancel()
    expect(wizard.snapshot().state).toBe('cancelled')
  })

  it('resets to a clean key step after a completed run', async () => {
    const { wizard } = makeWizard()
    await wizard.submitKey('sk-key')
    await wizard.finish('any')
    expect(wizard.snapshot().state).toBe('done')
    wizard.reset()
    const snap = wizard.snapshot()
    expect(snap).toEqual({
      state: 'key',
      keyMasked: null,
      storedModel: 'any',
      models: [],
      modelError: null,
      error: null,
    })
  })

  it('fills the repeat wizard with the stored masked key and model', async () => {
    const { wizard } = makeWizard()
    wizard.reset({ keyMasked: '••••cdef', model: 'm1' })
    const snap = wizard.snapshot()
    expect(snap.state).toBe('key')
    expect(snap.keyMasked).toBe('••••cdef')
    expect(snap.storedModel).toBe('m1')
  })
})

describe('createSettingsState', () => {
  function makeStore() {
    const state = {
      setupDone: true,
      model: 'any',
      baseUrl: 'https://openrouter.ai/api/v1',
      keyPlaintext: 'sk-or-v1-1234567890abcd',
      keyMasked: '••••abcd',
    }
    return {
      snapshot: () => ({ ...state }),
      setDefaultModel: (model) => {
        state.model = model
      },
      setBaseUrl: (baseUrl) => {
        state.baseUrl = baseUrl
      },
    }
  }

  it('exposes the masked key, model, and base URL', () => {
    const settings = createSettingsState({ store: makeStore(), startWizard: () => {} })
    expect(settings.get()).toEqual({
      keyMasked: '••••abcd',
      hasStoredKey: true,
      model: 'any',
      baseUrl: 'https://openrouter.ai/api/v1',
    })
  })

  it('persists each change at once', () => {
    const store = makeStore()
    const settings = createSettingsState({ store, startWizard: () => {} })
    expect(settings.setDefaultModel('m2').model).toBe('m2')
    expect(store.snapshot().model).toBe('m2')
    expect(settings.setBaseUrl('http://127.0.0.1:9/v1').baseUrl).toBe('http://127.0.0.1:9/v1')
    expect(store.snapshot().baseUrl).toBe('http://127.0.0.1:9/v1')
  })

  it('starts the wizard again on demand', () => {
    const started = []
    const settings = createSettingsState({ store: makeStore(), startWizard: () => started.push(true) })
    settings.startWizard()
    expect(started).toEqual([true])
  })
})
