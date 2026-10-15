"""OpenRouter HTTP client.

The client takes an injected `httpx.Client`, so tests run against
`httpx.MockTransport` and never touch the network. Every method raises
`ClientError` with one of the four kinds on failure. The chat stream is a
generator that yields `("chunk", text)` events and ends with exactly one
terminal event: `("done", {"text": ..., "stopped": bool})` or
`("error", ClientError)`.
"""

import json

import httpx

from .errors import ClientError, KIND_NETWORK, kind_for_status
from .sse import DONE_MARKER, parse_data_line

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
ANY_MODEL = "openrouter/auto"
CALL_TIMEOUT = 30.0
STREAM_TIMEOUT = httpx.Timeout(connect=30.0, read=30.0, write=30.0, pool=30.0)


def _auth_headers(key):
    return {"Authorization": f"Bearer {key}"}


def _api_error(response):
    """Build a ClientError from one non-2xx response. The message stays key-free."""
    kind = kind_for_status(response.status_code)
    try:
        body = response.json()
        detail = body["error"]["message"]
    except Exception:
        # None and "" are both falsy here, so the no-mutate line is equivalent.
        detail = None  # pragma: no mutate
    if not detail:
        detail = f"OpenRouter answered HTTP {response.status_code}"
    return ClientError(kind, detail)


def _network_error(exc):
    return ClientError(KIND_NETWORK, f"Connection to OpenRouter failed: {exc}")


class OpenRouterClient:
    def __init__(self, http_client, base_url=DEFAULT_BASE_URL):
        self._http = http_client
        self._base_url = base_url.rstrip("/")

    def _url(self, path):
        return self._base_url + path

    def validate_key(self, key):
        """Raise nothing when the key is valid; raise ClientError otherwise."""
        try:
            response = self._http.get(
                self._url("/key"), headers=_auth_headers(key), timeout=CALL_TIMEOUT
            )
        except httpx.HTTPError as exc:
            raise _network_error(exc) from exc
        if response.status_code == 200:
            return True
        raise _api_error(response)

    def list_models(self):
        """Return a list of {id, name} dicts; raise ClientError on failure."""
        try:
            response = self._http.get(self._url("/models"), timeout=CALL_TIMEOUT)
        except httpx.HTTPError as exc:
            raise _network_error(exc) from exc
        if response.status_code != 200:
            raise _api_error(response)
        body = response.json()
        return [
            {"id": item["id"], "name": item.get("name", item["id"])}
            for item in body.get("data", [])
        ]

    def chat_stream(self, key, model, messages, should_stop=None):
        """Yield one chat completion as events, per the module docstring.

        The model `any` maps to the OpenRouter auto router. `should_stop` is
        polled between chunks; a stop closes the upstream request and ends
        the stream with a terminal `stopped` event.
        """
        payload = {
            "model": ANY_MODEL if model == "any" else model,
            "messages": messages,
            "stream": True,
        }
        chunks = []
        response = None
        stopped = False
        try:
            response = self._http.post(
                self._url("/chat/completions"),
                headers=_auth_headers(key),
                json=payload,
                timeout=STREAM_TIMEOUT,
            )
            if response.status_code != 200:
                raise _api_error(response)
            for line in response.iter_lines():
                if should_stop is not None and should_stop():
                    stopped = True
                    break
                data = parse_data_line(line)
                if data is None:
                    continue
                if data == DONE_MARKER:
                    break
                text = _delta_text(data)
                if text:
                    chunks.append(text)
                    yield "chunk", text
        except ClientError as exc:
            yield "error", exc
            return
        except httpx.HTTPError as exc:
            yield "error", _network_error(exc)
            return
        finally:
            # The None path runs when post() itself raised; coverage.py cannot
            # attribute the arc across the generator resume after the except
            # yields, so the branch is excluded explicitly rather than loosened.
            if response is not None:  # pragma: no branch
                response.close()
        yield "done", {"text": "".join(chunks), "stopped": stopped}


def _delta_text(data_line):
    """Return the content delta of one SSE data payload, or an empty string."""
    try:
        event = json.loads(data_line)
        return event["choices"][0]["delta"].get("content") or ""
    except (json.JSONDecodeError, KeyError, IndexError, TypeError):
        return ""
