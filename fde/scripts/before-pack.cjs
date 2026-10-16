// electron-builder beforePack hook: make sure the pinned runtime and the
// dependency tree exist before the app gets packed.
const { execFileSync } = require('node:child_process')
const path = require('node:path')

module.exports = async function beforePack() {
  const root = path.resolve(__dirname, '..')
  execFileSync(process.execPath, [path.join(root, 'scripts', 'fetch-python.mjs')], { stdio: 'inherit' })
  execFileSync(process.execPath, [path.join(root, 'scripts', 'install-pylibs.mjs')], { stdio: 'inherit' })
}
