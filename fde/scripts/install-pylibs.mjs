// Installs the runtime dependencies into build/pylibs with the fetched
// embedded interpreter itself, so wheel selection pins to its CPython
// version and no host Python takes part.
import { execFileSync } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const isWindows = process.platform === 'win32'
const python = path.join(root, 'build', 'python', isWindows ? 'python.exe' : path.join('bin', 'python3'))
const pylibs = path.join(root, 'build', 'pylibs')
const requirements = path.join(root, 'backend', 'requirements-runtime.lock')

if (!fs.existsSync(python)) {
  console.error('The embedded runtime is missing. Run `npm run fetch-python` first.')
  process.exit(2)
}

fs.rmSync(pylibs, { recursive: true, force: true })
fs.mkdirSync(pylibs, { recursive: true })
execFileSync(python, ['-m', 'pip', 'install', '--target', pylibs, '--require-hashes', '-r', requirements], {
  stdio: 'inherit',
})
console.log(`Dependencies installed to ${pylibs}`)
