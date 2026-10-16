// Downloads the pinned python-build-standalone runtime for this platform,
// verifies its sha256 against runtime-lock.json, and unpacks it to
// build/python. A checksum mismatch stops the build.
import { createHash } from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { execFileSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const lockPath = path.join(root, 'runtime-lock.json')
const runtimeDir = path.join(root, 'build', 'runtime')
const pythonDir = path.join(root, 'build', 'python')

const lock = JSON.parse(fs.readFileSync(lockPath, 'utf8'))

function tripleFor(platform, arch) {
  if (platform === 'darwin') {
    return arch === 'arm64' ? 'aarch64-apple-darwin' : 'x86_64-apple-darwin'
  }
  if (platform === 'win32') {
    return arch === 'arm64' ? 'aarch64-pc-windows-msvc' : 'x86_64-pc-windows-msvc'
  }
  return 'x86_64-unknown-linux-gnu'
}

function sha256(file) {
  return createHash('sha256').update(fs.readFileSync(file)).digest('hex')
}

const triple = tripleFor(process.platform, process.arch)
const entry = lock.triples[triple]
if (!entry) {
  console.error(`No runtime pinned for ${triple}`)
  process.exit(2)
}

const archive = path.join(runtimeDir, entry.asset)
fs.mkdirSync(runtimeDir, { recursive: true })
if (!fs.existsSync(archive) || sha256(archive) !== entry.sha256) {
  console.log(`Downloading ${entry.asset} …`)
  execFileSync('curl', ['-sL', '-o', archive, entry.url], { stdio: 'inherit' })
}
const actual = sha256(archive)
if (actual !== entry.sha256) {
  console.error(`Checksum mismatch for ${entry.asset}: ${actual} != ${entry.sha256}`)
  process.exit(2)
}
console.log(`Checksum ok: ${triple}`)

fs.rmSync(pythonDir, { recursive: true, force: true })
fs.mkdirSync(pythonDir, { recursive: true })
execFileSync('tar', ['-xzf', archive, '-C', pythonDir])
// The tarball unpacks to a python/ folder; flatten it into build/python.
const inner = path.join(pythonDir, 'python')
for (const name of fs.readdirSync(inner)) {
  fs.renameSync(path.join(inner, name), path.join(pythonDir, name))
}
fs.rmdirSync(inner)
console.log(`Runtime unpacked to ${pythonDir}`)
