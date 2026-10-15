// Creates fde/.venv and installs the Python dev and gate tools into it.
// Cross platform: picks the right interpreter path inside the venv per OS.
import { spawnSync } from 'node:child_process'
import { existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const root = fileURLToPath(new URL('..', import.meta.url))
const venv = path.join(root, '.venv')
const isWindows = process.platform === 'win32'
const venvPython = path.join(venv, isWindows ? 'Scripts\\python.exe' : 'bin/python')
const requirements = path.join(root, 'backend', 'requirements-dev.txt')

function run(cmd, args) {
  const r = spawnSync(cmd, args, { stdio: 'inherit' })
  if (r.status !== 0) {
    console.error(`${cmd} ${args.join(' ')} failed with code ${r.status}`)
    process.exit(r.status ?? 1)
  }
}

if (!existsSync(venvPython)) {
  const launcher = isWindows ? 'py' : 'python3'
  run(launcher, ['-m', 'venv', venv])
}

run(venvPython, ['-m', 'pip', 'install', '--upgrade', 'pip'])
run(venvPython, ['-m', 'pip', 'install', '-r', requirements])
console.log(`Python dev environment ready at ${venv}`)
