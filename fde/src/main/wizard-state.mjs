// The first-launch wizard state machine and the settings surface. The key
// stays in this module's memory between step 1 and the finish action; the
// store persists it only at the finish, together with the model and the
// setup-done mark, as one step.

export function createWizardState({ validateKey, listModels, finish, notify }) {
  let state = 'key'
  let keyInMemory = null
  let storedKeyMasked = null
  let storedModel = 'any'
  let models = []
  let modelError = null
  let error = null

  function publish() {
    notify(snapshot())
  }

  function snapshot() {
    return {
      state,
      keyMasked: storedKeyMasked,
      storedModel,
      models,
      modelError,
      error,
    }
  }

  async function submitKey(key) {
    if (!key) {
      error = 'Enter your OpenRouter API key'
      publish()
      return
    }
    error = null
    state = 'validating'
    publish()
    try {
      await validateKey(key)
    } catch (err) {
      state = 'key'
      error = err.message
      publish()
      return
    }
    keyInMemory = key
    state = 'models'
    publish()
    await loadModels()
  }

  async function loadModels() {
    models = []
    modelError = null
    state = 'models-loading'
    publish()
    try {
      models = await listModels()
      state = 'models'
    } catch (err) {
      modelError = err.message
      state = 'models-failed'
    }
    publish()
  }

  async function complete(model) {
    state = 'finishing'
    publish()
    await finish({ key: keyInMemory, model })
    keyInMemory = null
    state = 'done'
    publish()
  }

  function cancel() {
    state = 'cancelled'
    publish()
  }

  function reset(prefill = {}) {
    state = 'key'
    keyInMemory = null
    storedKeyMasked = prefill.keyMasked ?? null
    storedModel = prefill.model ?? 'any'
    models = []
    modelError = null
    error = null
    publish()
  }

  return { submitKey, loadModels, finish: complete, cancel, reset, snapshot }
}

// The settings panel state: every change persists at once through the store.
export function createSettingsState({ store, startWizard }) {
  function get() {
    const snap = store.snapshot()
    return {
      keyMasked: snap.keyMasked,
      hasStoredKey: snap.keyPlaintext !== null,
      model: snap.model,
      baseUrl: snap.baseUrl,
    }
  }

  function setDefaultModel(model) {
    store.setDefaultModel(model)
    return get()
  }

  function setBaseUrl(baseUrl) {
    store.setBaseUrl(baseUrl)
    return get()
  }

  return { get, setDefaultModel, setBaseUrl, startWizard }
}
