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

function userDataBase() {
  // The per-OS user data folder of the packaged app (productName FDE Chat).
  const home = process.env.HOME ?? process.env.USERPROFILE
  if (process.platform === 'darwin') {
    return path.join(home, 'Library', 'Application Support', 'FDE Chat')
  }
  if (process.platform === 'win32') {
    return path.join(process.env.APPDATA ?? path.join(home, 'AppData', 'Roaming'), 'FDE Chat')
  }
  return path.join(home, '.config', 'FDE Chat')
}

function appPaths() {
  const base = userDataBase()
  const dist = path.join(root, 'dist')
  // The unpacked macOS layout is mac-arm64 on an arm64 builder and mac on an
  // Intel builder; accept both.
  const macCandidates = [
    path.join(dist, 'mac-arm64', 'FDE Chat.app', 'Contents', 'MacOS', 'FDE Chat'),
    path.join(dist, 'mac', 'FDE Chat.app', 'Contents', 'MacOS', 'FDE Chat'),
  ]
  return {
    logFile: path.join(base, 'logs', 'main.log'),
    macBinary: macCandidates.find((candidate) => fs.existsSync(candidate)),
    winBinary: path.join(dist, 'win-unpacked', 'FDE Chat.exe'),
    linuxAppImage: firstMatch(dist, '.AppImage'),
    linuxUnpacked: null,
  }
}

function firstMatch(dir, suffix) {
  try {
    const hit = fs.readdirSync(dir).find((name) => name.endsWith(suffix))
    return hit ? path.join(dir, hit) : null
  } catch {
    return null
  }
}

// The unpacked Linux binary name follows the package name; the other files
// in linux-unpacked all carry an extension (.pak, .txt, .dat, .so).
function linuxUnpackedBinary() {
  const dir = path.join(root, 'dist', 'linux-unpacked')
  try {
    for (const name of fs.readdirSync(dir)) {
      const candidate = path.join(dir, name)
      if (!name.includes('.') && fs.statSync(candidate).isFile()) {
        return candidate
      }
    }
  } catch {
    // Missing directory handled by the caller.
  }
  return null
}

function startCommand() {
  const paths = appPaths()
  if (process.platform === 'darwin') {
    if (!paths.macBinary) {
      fail('no packaged macOS binary under dist/mac-arm64 or dist/mac')
    }
    return { cmd: paths.macBinary, args: [] }
  }
  if (process.platform === 'win32') {
    return { cmd: paths.winBinary, args: [] }
  }
  // Linux: the AppImage runs with the extract-and-run option under a virtual
  // display, because the runner has neither libfuse2 nor a display server.
  // The extracted AppImage loses the SUID sandbox helper bit, so the CI
  // harness starts Electron with --no-sandbox; shipped apps keep it.
  // A --dir build has no AppImage, so its unpacked binary runs instead.
  if (paths.linuxAppImage) {
    return {
      cmd: 'xvfb-run',
      args: ['-a', paths.linuxAppImage, '--appimage-extract-and-run', '--no-sandbox'],
    }
  }
  const unpacked = linuxUnpackedBinary()
  if (!unpacked) {
    fail('no AppImage and no linux-unpacked binary under dist/')
  }
  return { cmd: 'xvfb-run', args: ['-a', unpacked, '--no-sandbox'] }
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
  stdio: ['ignore', 'pipe', 'pipe'],
  detached: false,
})
const appOutput = []
for (const stream of [child.stdout, child.stderr]) {
  stream.on('data', (chunk) => appOutput.push(String(chunk)))
}

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
  console.error('--- last app output:')
  console.error(appOutput.join('').split('\n').slice(-20).join('\n'))
  fail(`no readiness line within ${TIMEOUT_MS / 1000} seconds`)
}
process.exit(0)
