import path from 'node:path'

import { describe, expect, it } from 'vitest'

import {
  PROTOCOL_VERSION,
  backendCommand,
  pythonEnv,
  venvPythonPath,
} from '../../src/main/backend-command.mjs'

describe('venvPythonPath', () => {
  it('points to bin/python on POSIX', () => {
    expect(venvPythonPath('/repo/fde', 'darwin')).toBe('/repo/fde/.venv/bin/python')
  })

  it('points to Scripts/python.exe on Windows', () => {
    expect(venvPythonPath('C:\\repo\\fde', 'win32')).toBe(
      path.join('C:\\repo\\fde', '.venv', 'Scripts', 'python.exe'),
    )
  })
})

describe('pythonEnv', () => {
  it('joins module paths with the platform delimiter and cleans the environment', () => {
    const env = pythonEnv(['/r/pylibs', '/r/backend'], 'darwin', { PYTHONHOME: '/old', HOME: '/h' })
    expect(env.PYTHONPATH).toBe('/r/pylibs:/r/backend')
    expect(env.PYTHONHOME).toBeUndefined()
    expect(env.PYTHONNOUSERSITE).toBe('1')
    expect(env.HOME).toBe('/h')
  })

  it('uses a semicolon on Windows', () => {
    const env = pythonEnv(['C:\\a', 'C:\\b'], 'win32', {})
    expect(env.PYTHONPATH).toBe('C:\\a;C:\\b')
  })
})

describe('backendCommand', () => {
  const devOptions = {
    isPackaged: false,
    venvPython: '/repo/fde/.venv/bin/python',
    backendDir: '/repo/fde/backend',
  }

  it('runs the venv interpreter on the backend source in development', () => {
    const command = backendCommand({ ...devOptions, platform: 'darwin', base: {} })
    expect(command.command).toBe('/repo/fde/.venv/bin/python')
    expect(command.args).toEqual(['-m', 'backend'])
    // `-m backend` searches sys.path for the package, so the path entry is
    // the parent of backendDir; the child CWD must never matter.
    expect(command.env.PYTHONPATH).toBe('/repo/fde')
  })

  it('runs the embedded interpreter from the resources in a packaged mac app', () => {
    const command = backendCommand({
      isPackaged: true,
      resourcesPath: '/app/Resources',
      platform: 'darwin',
      base: {},
    })
    expect(command.command).toBe('/app/Resources/python/bin/python3')
    expect(command.args).toEqual(['-m', 'backend'])
    expect(command.env.PYTHONPATH).toBe('/app/Resources/pylibs:/app/Resources')
  })

  it('runs python.exe from the tree root in a packaged Windows app', () => {
    const command = backendCommand({
      isPackaged: true,
      resourcesPath: 'C:\\app\\resources',
      platform: 'win32',
      base: {},
    })
    // The per-OS CI job builds on Windows, so path.join produces the
    // host-native separators; the test asserts the same wiring on any host.
    expect(command.command).toBe(
      path.join('C:\\app\\resources', 'python', 'python.exe'),
    )
    expect(command.env.PYTHONPATH).toBe(
      [
        path.join('C:\\app\\resources', 'pylibs'),
        'C:\\app\\resources',
      ].join(';'),
    )
  })

  it('pins the protocol version', () => {
    expect(PROTOCOL_VERSION).toBe(1)
  })
})
