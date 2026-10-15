import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'

import { beforeEach, describe, expect, it } from 'vitest'

import { createRotatingLogWriter } from '../../src/main/log-writer.mjs'

let dir

beforeEach(() => {
  dir = fs.mkdtempSync(path.join(os.tmpdir(), 'fde-logs-'))
})

describe('createRotatingLogWriter', () => {
  it('appends lines to the file', () => {
    const file = path.join(dir, 'backend.log')
    const writer = createRotatingLogWriter({ file })
    writer.write('first line')
    writer.write('second line')
    expect(fs.readFileSync(file, 'utf8')).toBe('first line\nsecond line\n')
  })

  it('rotates at the size limit and keeps at most maxArchives', () => {
    const file = path.join(dir, 'backend.log')
    const writer = createRotatingLogWriter({ file, maxBytes: 20, maxArchives: 2 })
    for (let index = 0; index < 20; index += 1) {
      writer.write(`line-${String(index).padStart(2, '0')}-0123456789`)
    }
    expect(fs.existsSync(`${file}.1`)).toBe(true)
    expect(fs.existsSync(`${file}.2`)).toBe(true)
    expect(fs.existsSync(`${file}.3`)).toBe(false)
    const archiveTwo = fs.readFileSync(`${file}.2`, 'utf8')
    expect(archiveTwo).toContain('line-')
    // The oldest archive slot was deleted during rotation.
    const archiveOne = fs.readFileSync(`${file}.1`, 'utf8')
    expect(archiveOne.length).toBeGreaterThan(0)
  })
})
