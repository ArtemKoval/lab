// Conversation history: one JSON file per conversation in the user data
// folder. Every write replaces the whole file through a temp file and a
// rename, so the file on disk always holds the old or the new content and
// never a partial mix.

import fsSync from 'node:fs'
import crypto from 'node:crypto'
import path from 'node:path'

function safeId(id) {
  return typeof id === 'string' && /^[0-9a-f-]{36}$/.test(id)
}

export function createHistoryStore({
  chatsDir,
  fs = fsSync,
  now = () => new Date().toISOString(),
  idFactory = () => crypto.randomUUID(),
}) {
  fs.mkdirSync(chatsDir, { recursive: true })
  const fileFor = (id) => path.join(chatsDir, `${id}.json`)

  function writeConversation(conversation) {
    const tmp = fileFor(conversation.id) + '.tmp'
    fs.writeFileSync(tmp, JSON.stringify(conversation, null, 2))
    fs.renameSync(tmp, fileFor(conversation.id))
  }

  function create(defaultModel) {
    const stamp = now()
    const conversation = {
      id: idFactory(),
      title: '',
      model: defaultModel,
      messages: [],
      createdAt: stamp,
      updatedAt: stamp,
    }
    writeConversation(conversation)
    return conversation
  }

  function list() {
    let entries
    try {
      entries = fs.readdirSync(chatsDir).filter((name) => name.endsWith('.json'))
    } catch {
      // The folder can disappear under a running app (removed user data);
      // an empty list is the honest answer, never a crash.
      return []
    }
    const conversations = []
    for (const name of entries) {
      try {
        const data = JSON.parse(fs.readFileSync(path.join(chatsDir, name), 'utf8'))
        conversations.push({
          id: data.id,
          title: data.title,
          model: data.model,
          createdAt: data.createdAt,
          updatedAt: data.updatedAt,
        })
      } catch {
        // A file another process is mid-rename can vanish under the read;
        // a conversation that cannot be parsed is skipped, never fatal.
      }
    }
    return conversations.sort((a, b) => {
      if (a.updatedAt > b.updatedAt) {
        return -1
      }
      if (a.updatedAt < b.updatedAt) {
        return 1
      }
      return 0
    })
  }

  function get(id) {
    if (!safeId(id)) {
      return null
    }
    try {
      return JSON.parse(fs.readFileSync(fileFor(id), 'utf8'))
    } catch {
      return null
    }
  }

  function save(conversation) {
    const stamped = { ...conversation, updatedAt: now() }
    writeConversation(stamped)
    return stamped
  }

  function remove(id) {
    if (!safeId(id)) {
      return
    }
    try {
      fs.rmSync(fileFor(id))
    } catch {
      // Already gone is fine.
    }
  }

  return { create, list, get, save, remove }
}
