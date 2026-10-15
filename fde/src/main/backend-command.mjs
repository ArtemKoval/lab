// Chooses how the backend process runs in each mode. One helper owns the
// dev-versus-packaged selection; no other module branches on the run mode.
// The OpenRouter key never travels in the command or the environment.

import path from 'node:path'

export const PROTOCOL_VERSION = 1

export function pythonEnv(modulePaths, platform = process.platform, base = process.env) {
  const env = { ...base }
  delete env.PYTHONHOME
  env.PYTHONNOUSERSITE = '1'
  env.PYTHONPATH = modulePaths.join(platform === 'win32' ? ';' : ':')
  return env
}

export function backendCommand({
  isPackaged,
  resourcesPath,
  venvPython,
  backendDir,
  platform = process.platform,
  base = process.env,
}) {
  if (!isPackaged) {
    return {
      command: venvPython,
      args: ['-m', 'backend'],
      env: pythonEnv([backendDir], platform, base),
    }
  }
  const pythonBin = platform === 'win32'
    ? path.join(resourcesPath, 'python', 'python.exe')
    : path.join(resourcesPath, 'python', 'bin', 'python3')
  return {
    command: pythonBin,
    args: ['-m', 'backend'],
    env: pythonEnv(
      [path.join(resourcesPath, 'pylibs'), path.join(resourcesPath, 'backend')],
      platform,
      base,
    ),
  }
}
