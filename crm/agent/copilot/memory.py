"""AgentCore Memory, the Copilot's notes on each worker: the store a turn keeps
them in when CRM_COPILOT_MEMORY_ID is set, a search of one worker's
memories, and the save of a worker's message and the Copilot's answer, and
nothing else."""

import os

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.store.base import BaseStore

from agent.agentcore_memory import store_at

MEMORY_ID = "CRM_COPILOT_MEMORY_ID"
# Every memory of a worker is under /workers/<worker>, its preferences under
# /workers/<worker>/preferences/ and the facts they told the Copilot under
# /workers/<worker>/facts/.
WORKERS = "workers"
MOST_FOUND = 5


def memory_store() -> BaseStore | None:
    """AgentCore Memory at CRM_COPILOT_MEMORY_ID, read now, or None when it
    isn't set."""
    memory_id = os.getenv(MEMORY_ID)
    return store_at(memory_id) if memory_id else None


def recall(store: BaseStore, worker_id: str, query: str) -> list[str]:
    """Search one worker's memories for what bears on their message, and return
    each one's text."""
    found = store.search((WORKERS, worker_id), query=query, limit=MOST_FOUND)
    return [item.value["content"] for item in found]


def remember(
    store: BaseStore, worker_id: str, conversation_id: str, message: str, answer: str
) -> None:
    """Save a worker's message and the Copilot's answer, with the worker as the
    actor and the conversation as the session."""
    actor_and_session = (worker_id, conversation_id)
    store.put(actor_and_session, "message", {"message": HumanMessage(message)})
    store.put(actor_and_session, "answer", {"message": AIMessage(answer)})
