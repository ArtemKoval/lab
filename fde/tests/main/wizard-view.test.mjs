import { describe, expect, it } from 'vitest'

import { settingsViewModel, wizardViewModel } from '../../src/renderer/logic/wizard-view.mjs'

describe('wizardViewModel', () => {
  it('shows step 1 while the key is asked or validated', () => {
    expect(wizardViewModel({ state: 'key', error: null, models: [], modelError: null })).toMatchObject({
      step: 1,
      busy: false,
      canFinish: false,
    })
    expect(wizardViewModel({ state: 'validating', error: null, models: [], modelError: null })).toMatchObject({
      step: 1,
      busy: true,
    })
  })

  it('shows step 2 with the list, default any, and finish enabled', () => {
    const view = wizardViewModel({
      state: 'models',
      error: null,
      modelError: null,
      models: [{ id: 'any', name: 'Any (auto router)' }],
    })
    expect(view).toMatchObject({
      step: 2,
      busy: false,
      canFinish: true,
      canRetryList: false,
      defaultModel: 'any',
      models: [{ id: 'any', name: 'Any (auto router)' }],
    })
  })

  it('keeps finish available with a retry when the list failed', () => {
    const view = wizardViewModel({
      state: 'models-failed',
      error: null,
      modelError: 'no route',
      models: [],
    })
    expect(view.canRetryList).toBe(true)
    expect(view.canFinish).toBe(true)
    expect(view.modelError).toBe('no route')
  })

  it('marks loading and finishing as busy', () => {
    expect(wizardViewModel({ state: 'models-loading', error: null, models: [], modelError: null }).busy).toBe(true)
    expect(wizardViewModel({ state: 'finishing', error: null, models: [], modelError: null }).busy).toBe(true)
  })
})

describe('settingsViewModel', () => {
  it('maps the store snapshot to the panel fields', () => {
    expect(settingsViewModel({
      keyMasked: '••••cdef',
      hasStoredKey: true,
      model: 'm1',
      baseUrl: 'https://openrouter.ai/api/v1',
    })).toEqual({
      keyMasked: '••••cdef',
      hasStoredKey: true,
      model: 'm1',
      baseUrl: 'https://openrouter.ai/api/v1',
    })
    expect(settingsViewModel({ keyMasked: null, hasStoredKey: false, model: 'any', baseUrl: '' })).toEqual({
      keyMasked: null,
      hasStoredKey: false,
      model: 'any',
      baseUrl: '',
    })
  })
})
