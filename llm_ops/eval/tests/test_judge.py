import asyncio
import http.server
import json
import threading

import httpx2
import openai
import pytest
from fake_apfel import FakeApfel, completion, error
from pydantic import BaseModel, ValidationError

from apfel_eval.judge import ApfelJudge


class Score(BaseModel):
    score: int
    reason: str


class Item(BaseModel):
    name: str


class Nested(BaseModel):
    items: list[Item]


class Node(BaseModel):
    children: list["Node"]


def recording(reply):
    """Return a handler that records the requests and gives one reply."""
    requests = []

    def handler(request):
        requests.append(request)
        return reply(request) if callable(reply) else reply

    handler.requests = requests
    return handler


def body_of(request):
    return json.loads(request.content)


@pytest.fixture
def proxy():
    """A loopback server that records each request. It stands for a proxy."""
    seen = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            seen.append((self.command, self.path, self.headers.get("authorization")))
            self.send_response(502)
            self.send_header("Content-Length", "0")
            self.end_headers()

        do_GET = do_POST

        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield server.server_port, seen
    server.shutdown()
    server.server_close()


# --- the request


def test_request_goes_to_the_base_url_and_names_the_model(make_judge):
    handler = recording(completion("Paris"))
    judge = make_judge(handler, "http://127.0.0.1:11434/v1", model="model-1")
    judge.generate("What is the capital of France?")
    (request,) = handler.requests
    assert request.method == "POST"
    assert str(request.url) == "http://127.0.0.1:11434/v1/chat/completions"
    assert body_of(request)["model"] == "model-1"
    assert body_of(request)["messages"] == [
        {"role": "user", "content": "What is the capital of France?"}
    ]


def test_default_model_is_the_apple_model(make_judge):
    handler = recording(completion("x"))
    judge = make_judge(handler)
    judge.generate("hi")
    assert body_of(handler.requests[0])["model"] == "apple-foundationmodel"
    assert judge.get_model_name() == "apple-foundationmodel"


@pytest.mark.parametrize(
    ("base_url", "host"),
    [
        ("http://host.docker.internal:11434/v1", "localhost:11434"),
        ("http://127.0.0.1:11434/v1", "127.0.0.1:11434"),
        ("http://host.docker.internal/v1", "localhost"),
    ],
)
def test_host_header(make_judge, base_url, host):
    handler = recording(completion("x"))
    make_judge(handler, base_url).generate("hi")
    assert handler.requests[0].headers["host"] == host


# --- the reply


def test_text_reply_has_temperature_zero_and_no_response_format(make_judge):
    handler = recording(completion("Paris"))
    assert make_judge(handler).generate("q") == "Paris"
    body = body_of(handler.requests[0])
    assert body["temperature"] == 0
    assert "response_format" not in body


def test_schema_reply_is_an_object_of_the_schema(make_judge):
    handler = recording(completion('{"score": 8, "reason": "ok"}'))
    result = make_judge(handler).generate("q", Score)
    assert isinstance(result, Score)
    assert (result.score, result.reason) == (8, "ok")
    assert body_of(handler.requests[0])["response_format"] == {
        "type": "json_schema",
        "json_schema": {
            "name": "Score",
            "schema": {
                "properties": {
                    "score": {"title": "Score", "type": "integer"},
                    "reason": {"title": "Reason", "type": "string"},
                },
                "required": ["score", "reason"],
                "title": "Score",
                "type": "object",
            },
        },
    }


def test_reply_with_the_wrong_type_raises(make_judge):
    judge = make_judge(recording(completion('{"score": "high", "reason": "x"}')))
    with pytest.raises(ValidationError):
        judge.generate("q", Score)


def test_reply_that_is_not_json_raises(make_judge):
    judge = make_judge(recording(completion("not json")))
    with pytest.raises(ValidationError):
        judge.generate("q", Score)


@pytest.mark.parametrize("content", ["", None])
@pytest.mark.parametrize("schema", [None, Score])
def test_reply_without_text_raises(make_judge, content, schema):
    judge = make_judge(recording(completion(content)))
    with pytest.raises(ValueError, match="no text"):
        judge.generate("q", schema)


BASE_REPLY = {"id": "x", "object": "chat.completion", "created": 1, "model": "m"}


@pytest.mark.parametrize("extra", [{}, {"choices": None}, {"choices": []}])
@pytest.mark.parametrize("schema", [None, Score])
def test_reply_without_choices_raises_a_value_error(make_judge, extra, schema):
    handler = recording(httpx2.Response(200, json={**BASE_REPLY, **extra}))
    with pytest.raises(ValueError, match="no text"):
        make_judge(handler).generate("q", schema)
    assert len(handler.requests) == 1


# --- the schema


def test_nested_schema_is_sent_without_references(make_judge):
    handler = recording(completion('{"items": [{"name": "a"}]}'))
    result = make_judge(handler).generate("q", Nested)
    assert result.items[0].name == "a"
    schema = body_of(handler.requests[0])["response_format"]["json_schema"]["schema"]
    assert "$ref" not in json.dumps(schema)
    assert "$defs" not in schema
    assert schema["properties"]["items"]["items"]["title"] == "Item"


def test_recursive_schema_raises_before_any_request(make_judge):
    handler = recording(completion("{}"))
    with pytest.raises(ValueError, match="recursive"):
        make_judge(handler).generate("q", Node)
    assert handler.requests == []


def test_async_call_with_a_recursive_schema_raises_before_any_request(make_judge):
    handler = recording(completion("{}"))
    with pytest.raises(ValueError, match="recursive"):
        asyncio.run(make_judge(handler).a_generate("q", Node))
    assert handler.requests == []


# --- the token and the OpenAI variables


def test_token_is_the_bearer_token(make_judge):
    handler = recording(completion("x"))
    make_judge(handler, token="secret").generate("hi")
    assert handler.requests[0].headers["authorization"] == "Bearer secret"


def test_no_token_and_no_openai_key_uses_the_placeholder(make_judge):
    handler = recording(completion("x"))
    make_judge(handler).generate("hi")
    assert handler.requests[0].headers["authorization"] == "Bearer apfel-no-token"


def test_empty_token_uses_the_placeholder(make_judge):
    handler = recording(completion("x"))
    make_judge(handler, token="").generate("hi")
    assert handler.requests[0].headers["authorization"] == "Bearer apfel-no-token"


def test_openai_key_in_the_environment_is_never_sent(make_judge, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-secret")
    handler = recording(completion("x"))
    make_judge(handler).generate("hi")
    request = handler.requests[0]
    assert request.headers["authorization"] == "Bearer apfel-no-token"
    assert "sk-secret" not in str(dict(request.headers)) + request.content.decode()


def test_openai_organization_and_project_are_never_sent(make_judge, monkeypatch):
    monkeypatch.setenv("OPENAI_ORG_ID", "org-secret")
    monkeypatch.setenv("OPENAI_PROJECT_ID", "proj-secret")
    handler = recording(completion("x"))
    make_judge(handler).generate("hi")
    headers = handler.requests[0].headers
    assert "openai-organization" not in headers
    assert "openai-project" not in headers
    assert "secret" not in str(dict(headers))


# --- one request at a time


def test_two_threads_never_have_two_open_requests(make_judge):
    fake = FakeApfel(delay=0.05)
    judge = make_judge(fake)
    start = threading.Barrier(2)

    def call():
        start.wait()
        judge.generate("hi")

    threads = [threading.Thread(target=call) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(fake.requests) == 2
    assert fake.max_open == 1


def test_ping_and_a_call_never_have_two_open_requests(make_judge):
    fake = FakeApfel(delay=0.05)
    judge = make_judge(fake)
    start = threading.Barrier(2)

    def call(action):
        start.wait()
        action()

    threads = [
        threading.Thread(target=call, args=(judge.ping,)),
        threading.Thread(target=call, args=(lambda: judge.generate("hi"),)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(fake.requests) == 2
    assert fake.max_open == 1


def test_async_call_runs_in_a_worker_thread(make_judge):
    fake = FakeApfel()
    asyncio.run(make_judge(fake).a_generate("hi"))
    assert fake.thread_ids
    assert threading.get_ident() not in fake.thread_ids


def test_two_async_calls_never_have_two_open_requests(make_judge):
    fake = FakeApfel(delay=0.05)
    judge = make_judge(fake)

    async def both():
        return await asyncio.gather(judge.a_generate("a"), judge.a_generate("b"))

    asyncio.run(both())
    assert len(fake.requests) == 2
    assert fake.max_open == 1


# --- errors, no retry, and the time limit


def test_error_status_raises_after_one_request(make_judge):
    handler = recording(error(500))
    with pytest.raises(openai.APIStatusError):
        make_judge(handler).generate("hi")
    assert len(handler.requests) == 1


def test_connection_error_raises_after_one_attempt(make_judge):
    def refuse(request):
        raise httpx2.ConnectError("refused", request=request)

    handler = recording(refuse)
    with pytest.raises(openai.APIConnectionError):
        make_judge(handler).generate("hi")
    assert len(handler.requests) == 1


def test_timeout_raises_after_one_attempt(make_judge):
    def stall(request):
        raise httpx2.ReadTimeout("no reply", request=request)

    handler = recording(stall)
    with pytest.raises(openai.APITimeoutError):
        make_judge(handler).generate("hi")
    assert len(handler.requests) == 1


def test_request_time_limit_is_120_seconds(make_judge):
    handler = recording(completion("x"))
    make_judge(handler).generate("hi")
    assert set(handler.requests[0].extensions["timeout"].values()) == {120.0}


def test_judge_with_no_http_client_fails_when_nothing_listens():
    judge = ApfelJudge("http://127.0.0.1:1/v1")
    with pytest.raises(openai.APIConnectionError):
        judge.generate("hi")


def test_default_http_client_does_not_read_the_environment():
    # None and False both mean "ignore the environment" for httpx, so the test names the value.
    assert ApfelJudge("http://127.0.0.1:1/v1").model._client.trust_env is False


@pytest.mark.parametrize("name", ["HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy"])
def test_proxy_variable_is_ignored(monkeypatch, proxy, name):
    port, seen = proxy
    monkeypatch.setenv(name, f"http://127.0.0.1:{port}")
    judge = ApfelJudge("http://127.0.0.1:1/v1", token="s3cret")
    with pytest.raises(openai.APIConnectionError):
        judge.generate("a private prompt")
    assert seen == []


# --- async and ping


def test_async_text_reply_equals_the_sync_reply(make_judge):
    judge = make_judge(recording(completion("Paris")))
    assert asyncio.run(judge.a_generate("q")) == judge.generate("q") == "Paris"


def test_async_schema_reply_equals_the_sync_reply(make_judge):
    judge = make_judge(recording(completion('{"score": 3, "reason": "r"}')))
    assert asyncio.run(judge.a_generate("q", Score)) == judge.generate("q", Score)


def test_async_call_raises_the_same_error(make_judge):
    judge = make_judge(recording(error(500)))
    with pytest.raises(openai.APIStatusError):
        asyncio.run(judge.a_generate("q"))


def test_ping_lists_the_model_names(make_judge):
    fake = FakeApfel()
    assert make_judge(fake).ping() == ["apple-foundationmodel"]
    (request,) = fake.requests
    assert (request.method, str(request.url)) == ("GET", "http://127.0.0.1:11434/v1/models")


def test_ping_raises_an_error_status(make_judge):
    with pytest.raises(openai.PermissionDeniedError, match="403"):
        make_judge(FakeApfel(status=403)).ping()
