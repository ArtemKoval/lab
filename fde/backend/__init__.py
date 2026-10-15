"""Python backend of the FDE chat app.

The package splits into a pure core (this side: OpenRouter client, SSE
reader, JSON-RPC codec) and a thin stdio shell (`backend.shell`) that the
Electron main process spawns. The core never touches stdin or stdout.
"""
