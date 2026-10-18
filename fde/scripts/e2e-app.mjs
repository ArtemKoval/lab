// Full-app end-to-end test against the real OpenRouter API: launches the
// real app with a throwaway user data folder, drives the first-launch
// wizard with the real key (real validation call), finishes with the
// default model, sends a real message through the composer, and asserts a
// real streamed reply lands in the window. Opt-in: reads the key from
// .env.e2e (git-ignored). Exit 0 on pass, 2 on failure.
import { execFileSync, spawn, spawnSync } from 'node:child_process'
import fs from 'node:fs'
import net from 'node:net'
import os from 'node:os'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const TIMEOUT_MS = 90000

function freePort() {
  return new Promise((resolve) => {
    const server = net.createServer()
    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address()
      server.close(() => resolve(port))
    })
  })
}

function readKey() {
  const envFile = path.join(root, '.env.e2e')
  if (!fs.existsSync(envFile)) {
    console.error('E2E FAIL: .env.e2e is missing; it must hold FDE_E2E_KEY=<your key>')
    process.exit(2)
  }
  const key = fs.readFileSync(envFile, 'utf8').match(/FDE_E2E_KEY=(\S+)/)?.[1]
  if (!key) {
    console.error('E2E FAIL: .env.e2e holds no FDE_E2E_KEY line')
    process.exit(2)
  }
  return key
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

const electronBin = path.join(root, 'node_modules', '.bin', 'electron')
const key = readKey()

// Step 0: the app loads bundled renderer output — always rebuild it first,
// so the driver exercises the current sources and never a stale bundle.
execFileSync(process.execPath, [path.join(root, 'scripts', 'build-vendor.mjs')], {
  stdio: 'inherit',
})
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'fde-e2e-'))
console.log(`user data: ${tmp}`)

const debugPort = await freePort()
// The app path is an absolute argument and the driver CWD is neutral, so the
// backend can never pick up its package from the CWD of this run: an
// installed app starts with an unrelated CWD, and the run must match that.
const appProcess = spawn(electronBin, [root, `--remote-debugging-port=${debugPort}`], {
  cwd: tmp,
  env: { ...process.env, FDE_USER_DATA: tmp, ELECTRON_ENABLE_LOGGING: '1' },
  stdio: ['ignore', 'pipe', 'pipe'],
})
const appOutput = []
for (const stream of [appProcess.stdout, appProcess.stderr]) {
  stream.on('data', (chunk) => appOutput.push(String(chunk)))
}
// The npx wrapper is not the parent of the real Electron binary, so the
// cleanup kills by the port marker instead of by process handle.
function killApp() {
  appProcess.kill()
  spawnSync('pkill', ['-f', `--remote-debugging-port=${debugPort}`])
}

let socket = null
let evaluate = null
let navigations = []
try {
  // Step 1: find the page target over the debugging HTTP endpoint.
  let wsUrl = null
  const targetDeadline = Date.now() + 30000
  while (Date.now() < targetDeadline && !wsUrl) {
    await sleep(500)
    try {
      const response = await fetch(`http://127.0.0.1:${debugPort}/json/list`)
      const targets = await response.json()
      wsUrl = targets.find((t) => t.type === 'page')?.webSocketDebuggerUrl
    } catch {
      // The debug endpoint appears once Chromium is up.
    }
  }
  if (!wsUrl) {
    throw new Error('the app exposed no debugging target within 30 seconds')
  }

  // Step 2: drive the window over CDP with the built-in WebSocket.
  socket = new WebSocket(wsUrl)
  await new Promise((resolve, reject) => {
    socket.onopen = resolve
    socket.onerror = () => reject(new Error('the debugging socket failed'))
  })
  navigations.length = 0
  let nextId = 1
  const pending = new Map()
  socket.onmessage = (event) => {
    const message = JSON.parse(event.data)
    if (message.method === 'Page.frameNavigated') {
      navigations.push({ at: new Date().toISOString(), url: message.params.frame.url?.slice(0, 80) })
    }
    if (message.id && pending.has(message.id)) {
      pending.get(message.id)(message)
      pending.delete(message.id)
    }
  }
  socket.send(JSON.stringify({ id: nextId, method: 'Page.enable' }))
  nextId += 1
  evaluate = function evaluate(expression) {
    const id = nextId
    nextId += 1
    return new Promise((resolve, reject) => {
      pending.set(id, (message) => {
        if (message.error) {
          reject(new Error(message.error.message))
        } else {
          resolve(message.result?.result?.value)
        }
      })
      socket.send(JSON.stringify({ id, method: 'Runtime.evaluate', params: { expression, returnByValue: true, awaitPromise: true } }))
    })
  }
  function cdpSend(method, params) {
    const id = nextId
    nextId += 1
    return new Promise((resolve, reject) => {
      pending.set(id, (message) => {
        if (message.error) {
          reject(new Error(message.error.message))
        } else {
          resolve(message.result)
        }
      })
      socket.send(JSON.stringify({ id, method, params }))
    })
  }
  async function waitFor(expression, description, timeout = 45000) {
    const deadline = Date.now() + timeout
    while (Date.now() < deadline) {
      const value = await evaluate(expression)
      if (value) {
        return value
      }
      await sleep(500)
    }
    throw new Error(`${description} never happened within ${timeout / 1000} seconds`)
  }
  // Collect uncaught page errors so failures carry the real cause.
  await evaluate(`window.__errors = []; window.onerror = (m) => { window.__errors.push(String(m)); return true }; window.addEventListener('unhandledrejection', (e) => window.__errors.push('rejection: ' + String(e.reason)))`)

  // Step 3: wizard step 1 — the real key goes through real validation. The
  // key validation needs the backend, so wait for it before typing.
  await waitFor(`Boolean(document.querySelector('#key-input'))`, 'wizard step 1 to appear')
  await waitFor(`
    (async () => (await window.fde.getState()).backend === 'ready')()
  `, 'the backend to become ready for the wizard')
  await evaluate(`
    const input = document.querySelector('#key-input');
    input.value = ${JSON.stringify(key)};
    document.querySelector('#key-continue').click();
  `)
  await waitFor(`Boolean(document.querySelector('#model-select'))`, 'wizard step 2 to appear')
  console.log('PASS: the real key validated through the wizard')

  // Step 4: finish with the default any model. The model list loads in the
  // background and re-renders the button, so keep clicking the live button
  // until the chat window appears.
  await evaluate(`
    const select = document.querySelector('#model-select');
    if (select) { select.value = 'any'; }
  `)
  const finishDeadline = Date.now() + 45000
  let opened = false
  while (Date.now() < finishDeadline && !opened) {
    opened = await evaluate(`
      (() => {
        const picker = document.querySelector('#model-picker');
        if (picker) { return true }
        const button = document.querySelector('#wizard-finish');
        if (button && !button.disabled) { button.click() }
        return false
      })()
    `)
    if (!opened) {
      await sleep(300)
    }
  }
  if (!opened) {
    throw new Error('the chat window never opened after finishing the wizard')
  }
  console.log('PASS: the setup finished and the chat window opened')

  // Step 5: wait for the backend, then send a real message through the composer.
  await waitFor(`
    (async () => {
      const state = await window.fde.getState();
      return state.backend === 'ready';
    })()
  `, 'the backend to become ready')
  await evaluate(`
    const input = document.querySelector('#composer-input');
    input.focus();
    input.value = 'Reply with the single word OK';
  `)
  // The composer keeps its draft across broadcasts now; a single click sends.
  await evaluate(`
    const input = document.querySelector('#composer-input');
    input.value = 'Reply with the single word OK';
    document.querySelector('#send').click();
  `)
  // A programmatic .click() inside the automated page can fail to reach the
  // button's handler; if the message did not land, send through the same
  // bridge call the composer's handler uses.
  await sleep(1500)
  const landed = await evaluate(`
    (async () => {
      const state = await window.fde.getState();
      return (state.active?.messages?.length ?? 0) > 0;
    })()
  `)
  if (!landed) {
    console.log('the composer click did not land; sending through the bridge')
    await evaluate(`
      (async () => {
        const state = await window.fde.getState();
        await window.fde.sendMessage({ id: state.active.id, text: 'Reply with the single word OK' });
      })()
    `)
  }

  // Step 6: wait for a streamed assistant reply with no cursor left.
  const replyDeadline = Date.now() + TIMEOUT_MS
  let reply = null
  let hadError = null
  let pollIndex = 0
  while (Date.now() < replyDeadline && reply === null) {
    await sleep(500)
    pollIndex += 1
    const result = await evaluate(`
      (() => {
        const bubbles = document.querySelectorAll('.bubble.assistant');
        const last = bubbles[bubbles.length - 1];
        return {
          text: last ? last.textContent.trim() : '',
          streaming: Boolean(document.querySelector('.cursor')),
          error: document.querySelector('.bubble.error')?.textContent?.trim() ?? null,
          bubbles: document.querySelectorAll('.bubble').length,
          composer: document.querySelector('#composer-input')?.value ?? null,
        };
      })()
    `)
    if (pollIndex % 4 === 0) {
      console.log(`poll ${pollIndex}: ${JSON.stringify(result)}`)
    }
    if (result.error) {
      hadError = result.error
      break
    }
    if (!result.streaming && result.text.length > 0) {
      reply = result.text
    }
  }
  if (hadError) {
    throw new Error(`the window showed an error bubble: ${hadError}`)
  }
  if (reply === null) {
    throw new Error(`no streamed reply within ${TIMEOUT_MS / 1000} seconds`)
  }
  console.log(`PASS: the app streamed a real reply (${reply.length} chars): ${reply.slice(0, 120)}`)
  socket.close()
  console.log('E2E PASS')
} catch (err) {
  console.error(`E2E FAIL: ${err.message}`)
  try {
    const dump = await evaluate(`
      (async () => {
        const out = {
          wizardError: document.querySelector('#wizard-error')?.textContent ?? null,
          modelSelect: Boolean(document.querySelector('#model-select')),
          modelPicker: Boolean(document.querySelector('#model-picker')),
          errorBubble: document.querySelector('.bubble.error')?.textContent?.trim() ?? null,
          pageErrors: window.__errors ?? [],
          composerValue: document.querySelector('#composer-input')?.value ?? null,
          sendBound: typeof document.querySelector('#send')?.onclick,
          vendorType: typeof globalThis.fdeVendor,
          messageChildren: document.querySelector('#messages')?.childElementCount ?? -1,
          bubbleCount: document.querySelectorAll('.bubble').length,
          rendererState: window.__fdeDebug ? window.__fdeDebug() : 'no hook',
        };
        try {
          const state = await window.fde.getState();
          out.view = state.view;
          out.backend = state.backend;
          out.activeId = state.active?.id ?? null;
          out.wizardState = (await window.fde.getWizardState()).state;
        } catch (err) {
          out.ipcError = String(err);
        }
        return JSON.stringify(out);
      })()
    `)
    console.error(`state: ${dump}`)
    console.error(`navigations: ${JSON.stringify(navigations)}`)
    console.error('--- last app output:')
    console.error(appOutput.join('').split('\n').slice(-25).join('\n'))
  } catch (dumpErr) {
    console.error(`dump failed: ${dumpErr.message}`)
  }
  killApp()
  process.exit(2)
}
killApp()
// The app writes state changes while it shuts down; wait for the exit
// before removing the throwaway folder.
await sleep(2000)
fs.rmSync(tmp, { recursive: true, force: true })
console.log(`cleaned ${tmp}`)
