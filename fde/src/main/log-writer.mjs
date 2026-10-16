// Rotating log file writer for the backend stderr stream and the readiness
// result line the smoke harness reads. Keeps maxArchives numbered archives
// of at most maxBytes each and deletes the oldest on rotation.

import fsSync from 'node:fs'
import path from 'node:path'

export function createRotatingLogWriter({
  file,
  maxBytes = 5 * 1024 * 1024,
  maxArchives = 5,
  fs = fsSync,
}) {
  const dir = path.dirname(file)

  function sizeOf(candidate) {
    try {
      return fs.statSync(candidate).size
    } catch {
      return 0
    }
  }

  function rotate() {
    const oldest = `${file}.${maxArchives}`
    try {
      fs.rmSync(oldest)
    } catch {
      // No archive at that slot yet.
    }
    for (let target = maxArchives; target >= 2; target -= 1) {
      try {
        fs.renameSync(`${file}.${target - 1}`, `${file}.${target}`)
      } catch {
        // Missing source slot is fine.
      }
    }
    try {
      fs.renameSync(file, `${file}.1`)
    } catch {
      // Nothing to rotate yet.
    }
  }

  function write(line) {
    fs.mkdirSync(dir, { recursive: true })
    if (sizeOf(file) + line.length + 1 > maxBytes) {
      rotate()
    }
    fs.appendFileSync(file, line + '\n')
  }

  return { write }
}
