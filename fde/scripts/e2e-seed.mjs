// Seeds a throwaway user data folder with the encrypted OpenRouter key, so
// the e2e driver can start the real app straight on the chat window.
import { app, safeStorage } from 'electron'
import path from 'node:path'

app.setPath('userData', process.env.FDE_USER_DATA)

app.whenReady().then(async () => {
  const { createConfigStore } = await import('../src/main/config-store.mjs')
  const store = createConfigStore({
    configFile: path.join(process.env.FDE_USER_DATA, 'config.json'),
    safeStorage,
  })
  const result = store.storeSetup({ key: process.env.FDE_E2E_KEY, model: 'any' })
  console.log(`seeded: ${JSON.stringify(result)}`)
  app.quit()
})
