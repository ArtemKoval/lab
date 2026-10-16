// Launch smoke test of the packaged app. Starts the packaged binary the way
// each operating system needs, with a PATH that holds no python entry, and
// waits for the readiness result line that the main process writes to its
// log file in the user data folder. Exits 0 on `ready`, 2 on failure.
import { spawn } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const TIMEOUT_MS = 60000

function appPaths() {
  const home = process.env.HOME ?? process.env.USERPROFILE
  const base = path.join(home, 'Library', 'Application Support', 'FDE Chat')
  return {
    logFile: path.join(base, 'logs', 'main.log'),
    macBinary: path.join(root, 'dist', 'mac-arm64', 'FDE Chat.app', 'Contents', 'MacOS', 'FDE Chat'),
    winBinary: path.join(root, 'dist', 'win-unpacked', 'FDE Chat.exe'),
    linuxBinary: path.join(root, 'dist', 'FDE Chat.AppImage'),
  }
}

function startCommand() {
  if (process.platform === 'darwin') {
    return { cmd: appPaths().macBinary, args: [], pre: (argv) => argv }
  }
  if (process.platform === 'win32') {
    return { cmd: appPaths().winBinary, args: [], pre: (argv) => argv }
  }
  // Linux: the AppImage runs with the extract-and-run option under a virtual
  // display, because the runner has neither libfuse2 nor a display server.
  return {
    cmd: 'xvfb-run',
    args: ['-a', appPaths().linuxBinary, '--appimage-extract-and-run'],
    pre: (argv) => argv,
  }
}

// A PATH with no python entry, so a system Python could never satisfy the
// spawn: only the embedded tree can.
function pythonFreePath() {
  const entries = (process.env.PATH ?? '').split(path.delimiter)
  return entries.filter((entry) => !/python/i.test(entry)).join(path.delimiter)
}

function fail(message) {
  console.error(`SMOKE FAIL: ${message}`)
  process.exit(2)
}

const paths = appPaths()
fs.mkdirSync(path.dirname(paths.logFile), { recursive: true })
fs.rmSync(paths.logFile, { force: true })

const { cmd, args } = startCommand()
if (!fs.existsSync(cmd) && cmd !== 'xvfb-run') {
  fail(`packaged binary not found at ${cmd} — run electron-builder first`)
}

const child = spawn(cmd, args, {
  env: { ...process.env, PATH: pythonFreePath() },
  stdio: 'ignore',
  detached: false,
})

const started = Date.now()
let done = false
while (Date.now() - started < TIMEOUT_MS && !done) {
  await new Promise((resolve) => setTimeout(resolve, 500))
  try {
    const text = fs.readFileSync(paths.logFile, 'utf8')
    const readiness = text.split('\n').find((line) => line.includes('backend-readiness'))
    if (readiness) {
      done = true
      const outcome = readiness.includes('"outcome":"ready"') ? 'ready' : readiness
      if (!readiness.includes('"outcome":"ready"')) {
        fail(`readiness line reports a start failure: ${outcome}`)
      }
      console.log(`SMOKE OK: backend ready in ${(Date.now() - started) / 1000}s`)
    }
  } catch {
    // The log file appears when the app first writes; keep waiting.
  }
}

child.kill()
if (!done) {
  fail(`no readiness line within ${TIMEOUT_MS / 1000} seconds`)
}
process.exit(0)
