import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'

import { beforeEach, describe, expect, it } from 'vitest'

import { createHistoryStore } from '../../src/main/history-store.mjs'

let dir
let chatsDir

beforeEach(() => {
  dir = fs.mkdtempSync(path.join(os.tmpdir(), 'fde-chats-'))
  chatsDir = path.join(dir, 'chats')
})

describe('createHistoryStore', () => {
  it('creates a conversation file with the default model', () => {
    const store = createHistoryStore({ chatsDir })
    const conversation = store.create('any')
    expect(conversation.model).toBe('any')
    expect(conversation.messages).toEqual([])
    expect(conversation.id).toMatch(/^[0-9a-f-]{36}$/)
    const onDisk = JSON.parse(fs.readFileSync(path.join(chatsDir, `${conversation.id}.json`), 'utf8'))
    expect(onDisk.id).toBe(conversation.id)
  })

  it('lists conversations newest first and skips a corrupt file', () => {
    let ticks = 0
    const store = createHistoryStore({
      chatsDir,
      now: () => new Date(2026, 9, 15, 12, 0, ticks++).toISOString(),
    })
    const first = store.create('any')
    const second = store.create('any')
    const third = store.create('any')
    fs.writeFileSync(path.join(chatsDir, 'not-a-conversation.json'), '{broken')
    const listed = store.list()
    expect(listed.map((c) => c.id)).toEqual([third.id, second.id, first.id])
    expect(listed[0]).not.toHaveProperty('messages')
  })

  it('sorts a newest-first directory back under the oldest first', () => {
    let ticks = 0
    const store = createHistoryStore({
      chatsDir,
      now: () => new Date(2026, 9, 15, 12, 0, ticks++).toISOString(),
    })
    const older = store.create('any')
    const newer = store.create('any')
    // Seed the directory newest first, so the sort has work to do.
    fs.writeFileSync(path.join(chatsDir, `${newer.id}.json`), JSON.stringify(newer))
    fs.writeFileSync(path.join(chatsDir, `${older.id}.json`), JSON.stringify(older))
    expect(store.list().map((c) => c.id)).toEqual([newer.id, older.id])
  })

  it('keeps the directory order for equal timestamps', () => {
    const store = createHistoryStore({ chatsDir, now: () => '2026-10-15T09:00:00.000Z' })
    store.create('any')
    store.create('any')
    // readdir order is filesystem-dependent; a stable sort must keep it.
    const rawOrder = fs.readdirSync(chatsDir)
      .filter((name) => name.endsWith('.json'))
      .map((name) => name.replace('.json', ''))
    expect(store.list().map((c) => c.id)).toEqual(rawOrder)
  })

  it('lists an empty set when the chats folder is gone', () => {
    const store = createHistoryStore({ chatsDir })
    fs.rmSync(chatsDir, { recursive: true, force: true })
    expect(store.list()).toEqual([])
  })

  it('gets a conversation by id and refuses unsafe ids', () => {
    const store = createHistoryStore({ chatsDir })
    const conversation = store.create('any')
    expect(store.get(conversation.id).id).toBe(conversation.id)
    expect(store.get('../../etc/passwd')).toBeNull()
    expect(store.get('no-such-id')).toBeNull()
  })

  it('saves with a fresh update stamp', () => {
    let ticks = 0
    const store = createHistoryStore({
      chatsDir,
      now: () => new Date(2026, 9, 15, 12, 0, ticks++).toISOString(),
    })
    const conversation = store.create('any')
    conversation.messages.push({ role: 'user', content: 'hello' })
    const saved = store.save(conversation)
    expect(saved.updatedAt).not.toBe(conversation.createdAt)
    expect(store.get(conversation.id).messages).toHaveLength(1)
    expect(store.get(conversation.id).updatedAt).toBe(saved.updatedAt)
  })

  it('leaves the old content on disk when the temp write fails', () => {
    const store = createHistoryStore({ chatsDir })
    const conversation = store.create('any')
    const before = fs.readFileSync(path.join(chatsDir, `${conversation.id}.json`), 'utf8')

    const failing = createHistoryStore({
      chatsDir,
      fs: {
        ...fs,
        writeFileSync: () => {
          throw new Error('disk full')
        },
      },
    })
    expect(() => failing.save(conversation)).toThrow('disk full')
    expect(fs.readFileSync(path.join(chatsDir, `${conversation.id}.json`), 'utf8')).toBe(before)
  })

  it('leaves the old content on disk when the rename fails', () => {
    const store = createHistoryStore({ chatsDir })
    const conversation = store.create('any')
    const before = fs.readFileSync(path.join(chatsDir, `${conversation.id}.json`), 'utf8')

    const failing = createHistoryStore({
      chatsDir,
      fs: {
        ...fs,
        renameSync: () => {
          throw new Error('rename failed')
        },
      },
    })
    expect(() => failing.save(conversation)).toThrow('rename failed')
    expect(fs.readFileSync(path.join(chatsDir, `${conversation.id}.json`), 'utf8')).toBe(before)
  })

  it('removes the file and tolerates a missing one', () => {
    const store = createHistoryStore({ chatsDir })
    const conversation = store.create('any')
    store.remove(conversation.id)
    expect(store.get(conversation.id)).toBeNull()
    expect(() => store.remove(conversation.id)).not.toThrow()
    expect(() => store.remove('../escape')).not.toThrow()
  })
})
