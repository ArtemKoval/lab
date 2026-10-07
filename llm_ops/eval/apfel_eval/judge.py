"""A DeepEval judge model that uses a local apfel server."""

import asyncio
import threading
from typing import Any
from urllib.parse import urlparse

from deepeval.models import DeepEvalBaseLLM
from openai import DefaultHttpxClient, Omit, OpenAI
from pydantic import BaseModel

DEFAULT_MODEL = "apple-foundationmodel"
NO_TOKEN = "apfel-no-token"
TIMEOUT_SECONDS = 120
LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


def host_headers(base_url: str) -> dict[str, str]:
    """Return the Host header that the apfel Host guard accepts.

    apfel gives HTTP 403 to a Host name that is not a loopback name.
    """
    parsed = urlparse(base_url)
    if parsed.hostname in LOOPBACK_HOSTS:
        return {}
    port = f":{parsed.port}" if parsed.port is not None else ""
    return {"Host": f"localhost{port}"}


def inline_refs(schema: dict[str, Any]) -> dict[str, Any]:
    """Replace each `$ref` in a JSON schema with the definition that it names.

    apfel ignores `$ref` and `$defs`. The result has neither of them.
    """
    definitions = schema.get("$defs", {})
    root = {key: value for key, value in schema.items() if key != "$defs"}
    return _resolve(root, definitions, ())


def _resolve(node: Any, definitions: dict[str, Any], path: tuple[str, ...]) -> Any:
    if isinstance(node, list):
        return [_resolve(item, definitions, path) for item in node]
    if not isinstance(node, dict):
        return node
    others = {k: _resolve(v, definitions, path) for k, v in node.items() if k != "$ref"}
    if "$ref" not in node:
        return others
    name = node["$ref"].split("/")[-1]
    if name in path:
        raise ValueError(f"The schema is recursive: the definition {name} refers to itself.")
    if name not in definitions:
        raise ValueError(f"The schema refers to the definition {name}, which it does not have.")
    inlined = _resolve(definitions[name], definitions, (*path, name))
    return {**inlined, **others}


def _response_format(schema: type[BaseModel]) -> dict[str, Any]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": schema.__name__,
            "schema": inline_refs(schema.model_json_schema()),
        },
    }


class ApfelJudge(DeepEvalBaseLLM):
    """A DeepEval judge that sends each request to an apfel server."""

    def __init__(
        self,
        base_url: str,
        model: str = DEFAULT_MODEL,
        token: str | None = None,
        http_client: Any = None,
    ) -> None:
        # The base class calls load_model, so these values must exist first.
        self.base_url = base_url
        self.token = token
        self.http_client = http_client
        self._lock = threading.Lock()
        super().__init__(model)

    def load_model(self) -> OpenAI:
        # The client reads OPENAI_API_KEY, OPENAI_ORG_ID, and OPENAI_PROJECT_ID
        # if the code does not set them. The explicit values stop that.
        headers: dict[str, Any] = {
            "OpenAI-Organization": Omit(),
            "OpenAI-Project": Omit(),
            **host_headers(self.base_url),
        }
        # The default HTTP client reads HTTP_PROXY and similar variables. A proxy would get
        # the prompt and the token. This client sends each request straight to the base URL.
        http_client = self.http_client
        if http_client is None:
            http_client = DefaultHttpxClient(trust_env=False)
        return OpenAI(
            base_url=self.base_url,
            api_key=self.token or NO_TOKEN,
            default_headers=headers,
            max_retries=0,
            timeout=TIMEOUT_SECONDS,
            http_client=http_client,
        )

    def generate(self, prompt: str, schema: type[BaseModel] | None = None) -> Any:
        extra: dict[str, Any] = {}
        if schema is not None:
            extra["response_format"] = _response_format(schema)
        with self._lock:
            reply = self.model.chat.completions.create(
                model=self.name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                **extra,
            )
        # A TypeError here makes DeepEval send the request again without the schema.
        # A ValueError makes it stop, so the judge sends no hidden second request.
        choices = reply.choices
        text = choices[0].message.content if choices else None
        if not text:
            raise ValueError("The reply from the apfel server has no text.")
        if schema is None:
            return text
        return schema.model_validate_json(text)

    async def a_generate(self, prompt: str, schema: type[BaseModel] | None = None) -> Any:
        return await asyncio.to_thread(self.generate, prompt, schema)

    def ping(self) -> list[str]:
        """Return the model names of the server. This is one call to the server."""
        with self._lock:
            return [model.id for model in self.model.models.list()]

    def get_model_name(self) -> str:
        return self.name
