"""Tests for the OpenRouter client over httpx.MockTransport (hermetic)."""

import json

import httpx
import pytest

from backend.errors import KIND_API, KIND_AUTH, KIND_NETWORK, KIND_RATE, ClientError
from backend.openrouter_client import (
    ANY_MODEL,
    CALL_TIMEOUT,
    DEFAULT_BASE_URL,
    STREAM_TIMEOUT,
    OpenRouterClient,
)

KEY = "sk-test-key"


class RecordingHttp:
    """Captures every call so tests assert exact request construction."""

    def __init__(self, response):
        self._response = response
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append(("get", url, kwargs))
        return self._response

    def post(self, url, **kwargs):
        self.calls.append(("post", url, kwargs))
        return self._response


def make_client(handler, base_url=DEFAULT_BASE_URL):
    transport = httpx.MockTransport(handler)
    return OpenRouterClient(httpx.Client(transport=transport), base_url=base_url)


def sse_response(lines):
    content = ("\n".join(lines) + "\n").encode("utf-8")
    return httpx.Response(200, content=content)


def chunk_line(text):
    payload = {"choices": [{"delta": {"content": text}}]}
    return "data: " + json.dumps(payload)


def collect(generator):
    return list(generator)


class TestValidateKey:
    def test_valid_key_returns_true(self):
        seen = {}

        def handler(request):
            seen["url"] = str(request.url)
            seen["auth"] = request.headers.get("Authorization")
            return httpx.Response(200, json={"data": {}})

        assert make_client(handler).validate_key(KEY) is True
        assert seen["url"] == DEFAULT_BASE_URL + "/key"
        assert seen["auth"] == f"Bearer {KEY}"

    def test_rejected_key_maps_to_auth(self):
        def handler(request):
            return httpx.Response(401, json={"error": {"message": "Invalid key"}})

        with pytest.raises(ClientError) as excinfo:
            make_client(handler).validate_key(KEY)
        assert excinfo.value.kind == KIND_AUTH
        assert excinfo.value.message == "Invalid key"
        assert str(excinfo.value) == "Invalid key"

    def test_validate_key_sends_exact_header_url_and_timeout(self):
        http_stub = RecordingHttp(httpx.Response(200, json={"data": {}}))
        OpenRouterClient(http_stub).validate_key(KEY)
        assert http_stub.calls == [
            (
                "get",
                DEFAULT_BASE_URL + "/key",
                {"headers": {"Authorization": f"Bearer {KEY}"}, "timeout": CALL_TIMEOUT},
            )
        ]

    def test_base_url_keeps_a_trailing_x(self):
        seen = {}

        def capture(request):
            seen["url"] = str(request.url)
            return httpx.Response(200, json={"data": {}})

        make_client(capture, base_url="http://h/v1X").validate_key(KEY)
        assert seen["url"] == "http://h/v1X/key"

    def test_server_error_without_body_message(self):
        def handler(request):
            return httpx.Response(500, text="boom")

        with pytest.raises(ClientError) as excinfo:
            make_client(handler).validate_key(KEY)
        assert excinfo.value.kind == KIND_API
        assert excinfo.value.message == "OpenRouter answered HTTP 500"

    def test_connection_failure_maps_to_network(self):
        def handler(request):
            raise httpx.ConnectError("no route")

        with pytest.raises(ClientError) as excinfo:
            make_client(handler).validate_key(KEY)
        assert excinfo.value.kind == KIND_NETWORK
        assert "no route" in excinfo.value.message

    def test_base_url_override(self):
        seen = {}

        def handler(request):
            seen["url"] = str(request.url)
            return httpx.Response(200, json={"data": {}})

        make_client(handler, base_url="http://127.0.0.1:9/v1/").validate_key(KEY)
        assert seen["url"] == "http://127.0.0.1:9/v1/key"


class TestListModels:
    def test_models_return_id_and_name(self):
        def handler(request):
            assert str(request.url) == DEFAULT_BASE_URL + "/models"
            body = {"data": [{"id": "m1", "name": "Model One"}, {"id": "m2"}]}
            return httpx.Response(200, json=body)

        models = make_client(handler).list_models()
        assert models == [
            {"id": "m1", "name": "Model One"},
            {"id": "m2", "name": "m2"},
        ]

    def test_rate_limited_models_call(self):
        def handler(request):
            return httpx.Response(429, json={"error": {"message": "slow down"}})

        with pytest.raises(ClientError) as excinfo:
            make_client(handler).list_models()
        assert excinfo.value.kind == KIND_RATE

    def test_network_failure_on_models_call(self):
        def handler(request):
            raise httpx.ReadTimeout("t")

        with pytest.raises(ClientError) as excinfo:
            make_client(handler).list_models()
        assert excinfo.value.kind == KIND_NETWORK

    def test_network_failure_message_carries_the_reason(self):
        def handler(request):
            raise httpx.ConnectError("no route")

        with pytest.raises(ClientError) as excinfo:
            make_client(handler).list_models()
        assert "no route" in excinfo.value.message

    def test_models_call_sends_exact_url_and_timeout(self):
        http_stub = RecordingHttp(httpx.Response(200, json={"data": []}))
        OpenRouterClient(http_stub).list_models()
        assert http_stub.calls == [("get", DEFAULT_BASE_URL + "/models", {"timeout": CALL_TIMEOUT})]

    def test_missing_data_key_yields_empty_model_list(self):
        def handler(request):
            return httpx.Response(200, json={})

        assert make_client(handler).list_models() == []


class TestChatStream:
    def _handler_ok(self, lines, seen):
        def handler(request):
            seen["url"] = str(request.url)
            seen["auth"] = request.headers.get("Authorization")
            seen["body"] = json.loads(request.content)
            return sse_response(lines)

        return handler

    def test_chunks_arrive_in_order_with_joined_final_text(self):
        lines = [chunk_line("Hello"), chunk_line(" world"), "data: [DONE]"]
        events = collect(make_client(self._handler_ok(lines, {})).chat_stream(
            KEY, "m1", [{"role": "user", "content": "hi"}]
        ))
        assert events == [
            ("chunk", "Hello"),
            ("chunk", " world"),
            ("done", {"text": "Hello world", "stopped": False}),
        ]

    def test_request_carries_bearer_stream_and_messages(self):
        seen = {}
        messages = [{"role": "user", "content": "hi"}]
        list(make_client(self._handler_ok(["data: [DONE]"], seen)).chat_stream(
            KEY, "m1", messages
        ))
        assert seen["auth"] == f"Bearer {KEY}"
        assert seen["body"] == {
            "model": "m1",
            "messages": messages,
            "stream": True,
        }

    def test_any_model_maps_to_auto_router(self):
        seen = {}
        list(make_client(self._handler_ok(["data: [DONE]"], seen)).chat_stream(
            KEY, "any", []
        ))
        assert seen["body"]["model"] == ANY_MODEL

    def test_rate_limited_chat_yields_single_error_event(self):
        def handler(request):
            return httpx.Response(429, json={"error": {"message": "limit"}})

        events = collect(make_client(handler).chat_stream(KEY, "m1", []))
        assert len(events) == 1
        kind, error = events[0]
        assert kind == "error"
        assert error.kind == KIND_RATE

    def test_error_message_holds_no_key(self):
        def handler(request):
            return httpx.Response(401, json={"error": {"message": "bad key"}})

        events = collect(make_client(handler).chat_stream(KEY, "m1", []))
        _, error = events[0]
        assert KEY not in error.message
        assert KEY not in str(events)

    def test_stop_ends_stream_with_stopped_terminal(self):
        lines = [chunk_line("Hello"), chunk_line(" world"), "data: [DONE]"]
        polls = iter([False, True])
        events = collect(
            make_client(self._handler_ok(lines, {})).chat_stream(
                KEY, "m1", [], should_stop=lambda: next(polls)
            )
        )
        assert events == [
            ("chunk", "Hello"),
            ("done", {"text": "Hello", "stopped": True}),
        ]

    def test_stream_end_without_done_marker_still_completes(self):
        lines = [chunk_line("A"), chunk_line("B")]
        events = collect(make_client(self._handler_ok(lines, {})).chat_stream(
            KEY, "m1", []
        ))
        assert events[-1] == ("done", {"text": "AB", "stopped": False})

    def test_stalled_stream_yields_network_error(self):
        class StubResponse:
            status_code = 200

            def __init__(self):
                self.closed = False

            def iter_lines(self):
                yield chunk_line("Hi")
                raise httpx.ReadTimeout("stalled")

            def close(self):
                self.closed = True

        class StubHttp:
            def __init__(self, response):
                self._response = response

            def post(self, *args, **kwargs):
                return self._response

        stub = StubResponse()
        client = OpenRouterClient(StubHttp(stub))
        events = collect(client.chat_stream(KEY, "m1", []))
        assert len(events) == 2
        assert events[0] == ("chunk", "Hi")
        kind, error = events[1]
        assert kind == "error"
        assert error.kind == KIND_NETWORK
        assert "stalled" in error.message
        assert stub.closed is True

    def test_connection_failure_at_chat_start_yields_network_error(self):
        class StubHttp:
            def post(self, *args, **kwargs):
                raise httpx.ConnectError("no route")

        events = collect(OpenRouterClient(StubHttp()).chat_stream(KEY, "m1", []))
        assert len(events) == 1
        kind, error = events[0]
        assert kind == "error"
        assert error.kind == KIND_NETWORK

    def test_chat_start_sends_exact_request(self):
        http_stub = RecordingHttp(sse_response(["data: [DONE]"]))
        messages = [{"role": "user", "content": "hi"}]
        list(OpenRouterClient(http_stub).chat_stream(KEY, "m1", messages))
        method, url, kwargs = http_stub.calls[0]
        assert method == "post"
        assert url == DEFAULT_BASE_URL + "/chat/completions"
        assert kwargs["headers"] == {"Authorization": f"Bearer {KEY}"}
        assert kwargs["json"] == {"model": "m1", "messages": messages, "stream": True}
        assert kwargs["timeout"] == STREAM_TIMEOUT

    def test_malformed_and_comment_lines_are_skipped(self):
        lines = [
            ": keep-alive",
            "data: not-json",
            chunk_line("ok"),
            "data: [DONE]",
        ]
        events = collect(make_client(self._handler_ok(lines, {})).chat_stream(
            KEY, "m1", []
        ))
        assert events == [
            ("chunk", "ok"),
            ("done", {"text": "ok", "stopped": False}),
        ]

    def test_role_chunk_without_content_is_skipped(self):
        role_payload = "data: " + json.dumps({"choices": [{"delta": {"role": "assistant"}}]})
        lines = [role_payload, chunk_line("x"), "data: [DONE]"]
        events = collect(make_client(self._handler_ok(lines, {})).chat_stream(
            KEY, "m1", []
        ))
        assert events == [
            ("chunk", "x"),
            ("done", {"text": "x", "stopped": False}),
        ]
