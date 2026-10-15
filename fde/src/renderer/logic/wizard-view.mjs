// Pure view models for the wizard and the settings panel, derived from the
// main-process state snapshots.

export function wizardViewModel(snap) {
  const step = snap.state === 'key' || snap.state === 'validating' ? 1 : 2
  return {
    step,
    busy: snap.state === 'validating' || snap.state === 'models-loading' || snap.state === 'finishing',
    error: snap.error,
    modelError: snap.modelError,
    models: snap.models,
    defaultModel: 'any',
    canRetryList: snap.state === 'models-failed',
    canFinish: snap.state === 'models' || snap.state === 'models-failed',
  }
}

export function settingsViewModel(settings) {
  return {
    keyMasked: settings.keyMasked,
    hasStoredKey: settings.hasStoredKey,
    model: settings.model,
    baseUrl: settings.baseUrl,
  }
}
