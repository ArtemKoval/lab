"""Error kinds shared by the OpenRouter client and the protocol layer.

The four kinds match the fde/openrouter-client spec: `auth` for rejected
keys, `rate` for rate limits, `api` for other API answers, and `network`
for connection failures and timeouts.
"""

KIND_AUTH = "auth"
KIND_RATE = "rate"
KIND_API = "api"
KIND_NETWORK = "network"

_STATUS_KINDS = {401: KIND_AUTH, 429: KIND_RATE}


def kind_for_status(status):
    """Map one HTTP status to its protocol error kind."""
    return _STATUS_KINDS.get(status, KIND_API)


class ClientError(Exception):
    """One API failure with a protocol kind and a key-free message."""

    def __init__(self, kind, message):
        super().__init__(message)
        self.kind = kind
        self.message = message
