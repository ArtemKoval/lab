# Tech stack

- `backend/`: FastAPI and SQLite. Every API operation has an `operation_id`,
  a one-line docstring, and no optional inputs. Paying an award is a
  separate operation that takes the amount.
- `agent/`: LangChain's `create_agent` on OpenRouter, with one entry point
  that takes a case id and a thread id. The agent reaches cases and its
  instructions only through the backend's API. The harness runs the queue
  agent and one subagent per case on LangGraph.
- `dashboard/`: React, Vite, and TypeScript.
- `e2e/`: Playwright tests.
- `domains/`: one pack per domain. The pack manifest names the pack and
  carries the engine settings. `domains/loader.py` is the one seam.
- `port/`: the tool that ports the next upstream milestones.

Python 3.12 with uv, all in the root `pyproject.toml`. Node 22. The
OpenRouter key is `OPENROUTER_API_KEY` in `.env`.
