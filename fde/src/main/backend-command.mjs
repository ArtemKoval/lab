// Chooses how the backend process runs in each mode. One helper owns the
// dev-versus-packaged selection; no other module branches on the run mode.
// The OpenRouter key never travels in the command or the environment.

import path from 'node:path'

export const PROTOCOL_VERSION = 1

export function venvPythonPath(appDir, platform = process.platform) {
  return platform === 'win32'
    ? path.join(appDir, '.venv', 'Scripts', 'python.exe')
    : path.join(appDir, '.venv', 'bin', 'python')
}

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
      // `python -m backend` searches sys.path for a `backend` package, so
      // PYTHONPATH must hold the parent of the package directory. The child
      // CWD is not a contract: an installed app launches from Finder.
      env: pythonEnv([path.dirname(backendDir)], platform, base),
    }
  }
  const pythonBin = platform === 'win32'
    ? path.join(resourcesPath, 'python', 'python.exe')
    : path.join(resourcesPath, 'python', 'bin', 'python3')
  return {
    command: pythonBin,
    args: ['-m', 'backend'],
    // Same parent rule as in dev: `backend` is a package under resourcesPath,
    // so resourcesPath itself exposes it; pylibs holds the dependencies.
    env: pythonEnv(
      [path.join(resourcesPath, 'pylibs'), resourcesPath],
      platform,
      base,
    ),
  }
}
