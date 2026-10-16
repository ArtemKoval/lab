"""Entry point for `python -m backend`. Spawns nothing; it IS the backend."""

import sys

import httpx

from .openrouter_client import OpenRouterClient
from .shell import serve

serve(sys.stdin, sys.stdout, OpenRouterClient(httpx.Client()), sys.executable)
