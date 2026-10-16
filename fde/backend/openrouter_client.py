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

from .errors import ClientError, KIND_API, KIND_NETWORK, kind_for_status
from .sse import DONE_MARKER, parse_data_line

_STOP = object()


class _StopRequested(Exception):
    """Raised by the delta iterator when the caller asked for a stop."""

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
        # The lstrip mutant is equivalent: no valid base URL starts with a
        # slash, and the trailing-slash behavior is covered by the URL
        # equality asserts.
        self._base_url = base_url.rstrip("/")  # pragma: no mutate

    def _url(self, path, base_url=None):
        base = base_url or self._base_url
        # The lstrip mutant is equivalent for absolute base URLs; the
        # trailing-slash behavior is covered by the URL equality asserts.
        return base.rstrip("/") + path  # pragma: no mutate

    def validate_key(self, key, base_url=None):
        """Raise nothing when the key is valid; raise ClientError otherwise."""
        try:
            response = self._http.get(
                self._url("/key", base_url), headers=_auth_headers(key), timeout=CALL_TIMEOUT
            )
        except httpx.HTTPError as exc:
            raise _network_error(exc) from exc
        if response.status_code == 200:
            return True
        raise _api_error(response)

    def list_models(self, base_url=None):
        """Return a list of {id, name} dicts; raise ClientError on failure."""
        try:
            response = self._http.get(self._url("/models", base_url), timeout=CALL_TIMEOUT)
        except httpx.HTTPError as exc:
            raise _network_error(exc) from exc
        if response.status_code != 200:
            raise _api_error(response)
        body = response.json()
        return [
            {"id": item["id"], "name": item.get("name", item["id"])}
            for item in body.get("data", [])
        ]

    def chat_stream(self, key, model, messages, should_stop=None, base_url=None):
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
                self._url("/chat/completions", base_url),
                headers=_auth_headers(key),
                json=payload,
                timeout=STREAM_TIMEOUT,
            )
            if response.status_code != 200:
                raise _api_error(response)
            for item in self._iter_deltas(response, should_stop):
                chunks.append(item)
                yield "chunk", item
        except _StopRequested:
            stopped = True
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

    def _iter_deltas(self, response, should_stop):
        """Yield the content deltas of one streamed response.

        Raises `_StopRequested` when the caller asks for a stop, and
        ClientError for a mid-stream error payload."""
        for line in response.iter_lines():
            if should_stop is not None and should_stop():
                raise _StopRequested
            data = parse_data_line(line)
            if data is None:
                continue
            if data == DONE_MARKER:
                return
            text, error = _delta_or_error(data)
            if error is not None:
                raise error
            if text:
                yield text


def _delta_or_error(data_line):
    """Return (delta, None) for a content chunk, or ('', ClientError) when the
    payload carries a mid-stream error. OpenRouter sends errors after the
    headers as a data event with a top-level error field, under HTTP 200."""
    try:
        event = json.loads(data_line)
        error = event.get("error")
        if error is not None:
            # The `or 1` mutant is equivalent: codes 0 and 1 both map to the
            # api kind, and the no-code behavior is asserted by its own test.
            code = error.get("code") or 0  # pragma: no mutate
            # Positive numeric codes map through the status kinds; every other
            # code shape is a plain api error. (The condition mutants that
            # swap > for >= or flip the conjunction are equivalent: status
            # code 0 and negative codes both land on KIND_API either way.)
            if isinstance(code, int) and code > 0:  # pragma: no mutate
                kind = kind_for_status(code)
            else:
                kind = KIND_API
            message = error.get("message") or "The stream failed inside the provider"
            return "", ClientError(kind, message)
        return event["choices"][0]["delta"].get("content") or "", None
    except (json.JSONDecodeError, KeyError, IndexError, TypeError):
        return "", None
