"""A fake apfel server. It is a request handler for an `httpx2` mock transport.

The module has no test code, so a subprocess probe can import it too.
"""

import json
import threading
import time
from collections.abc import Callable
from typing import Any

import httpx2

MODEL = "apple-foundationmodel"
ANSWERS = {
    "What is the capital of France?": "Paris",
    "How many days are in a leap year?": "366",
    "What is the chemical symbol for water?": "H2O",
    "Who wrote the play Romeo and Juliet?": "William Shakespeare",
}


def completion(content: str | None) -> httpx2.Response:
    message = {"role": "assistant", "content": content}
    return httpx2.Response(
        200,
        json={
            "id": "chatcmpl-1",
            "object": "chat.completion",
            "created": 1,
            "model": MODEL,
            "choices": [{"index": 0, "finish_reason": "stop", "message": message}],
        },
    )


def error(status: int, message: str = "fake apfel error") -> httpx2.Response:
    return httpx2.Response(status, json={"error": {"message": message, "type": "fake"}})


def models() -> httpx2.Response:
    entry = {"id": MODEL, "object": "model", "created": 1, "owned_by": "apple"}
    return httpx2.Response(200, json={"object": "list", "data": [entry]})


class FakeApfel:
    """Answer like apfel. Record every request and the most open requests at one time.

    `score` is the integer that the judge gives (0 to 10), or a function of the prompt.
    `fail_questions` are questions that get an HTTP 400 error.
    `status` is an HTTP status for every request.
    """

    def __init__(
        self,
        answers: dict[str, str] | None = None,
        score: int | Callable[[str], int] = 8,
        fail_questions: tuple[str, ...] = (),
        status: int | None = None,
        delay: float = 0.0,
    ) -> None:
        self.answers = dict(ANSWERS if answers is None else answers)
        self.score = score
        self.fail_questions = fail_questions
        self.status = status
        self.delay = delay
        self.requests: list[httpx2.Request] = []
        self.thread_ids: set[int] = set()
        self.max_open = 0
        self._open = 0
        self._lock = threading.Lock()

    @property
    def bodies(self) -> list[dict[str, Any]]:
        return [json.loads(request.content) for request in self.requests if request.content]

    def prompts(self, schema_name: str | None = None) -> list[str]:
        """Return the prompts of the chat calls with this schema name (None: no schema)."""
        found = []
        for body in self.bodies:
            name = body.get("response_format", {}).get("json_schema", {}).get("name")
            if name == schema_name:
                found.append(body["messages"][0]["content"])
        return found

    def __call__(self, request: httpx2.Request) -> httpx2.Response:
        with self._lock:
            self.requests.append(request)
            self.thread_ids.add(threading.get_ident())
            self._open += 1
            self.max_open = max(self.max_open, self._open)
        try:
            time.sleep(self.delay)
            return self._respond(request)
        finally:
            with self._lock:
                self._open -= 1

    def _respond(self, request: httpx2.Request) -> httpx2.Response:
        if self.status is not None:
            return error(self.status)
        if request.url.path.endswith("/models"):
            return models()
        body = json.loads(request.content)
        prompt = body["messages"][0]["content"]
        name = body.get("response_format", {}).get("json_schema", {}).get("name")
        if name == "Steps":
            return completion(json.dumps({"steps": ["Compare the two outputs."]}))
        if name == "ReasonScore":
            score = self.score(prompt) if callable(self.score) else self.score
            return completion(json.dumps({"reason": "fake reason", "score": score}))
        for question, answer in self.answers.items():
            if f"Question: {question}" in prompt:
                if question in self.fail_questions:
                    return error(400, "context window is full")
                return completion(answer)
        return completion("unknown")
