"""Tests for the line-delimited JSON-RPC codec."""

from backend.codec import (
    APPLICATION_ERROR,
    PROTOCOL_VERSION,
    encode_error,
    encode_line,
    encode_notification,
    encode_request,
    encode_response,
    decode_line,
)


def test_protocol_version_is_pinned():
    assert PROTOCOL_VERSION == 1


def test_encode_line_is_compact_with_newline():
    assert encode_line({"a": 1, "b": "x"}) == '{"a":1,"b":"x"}\n'


def test_encode_request():
    assert encode_request(7, "list_models", {}) == {
        "jsonrpc": "2.0",
        "id": 7,
        "method": "list_models",
        "params": {},
    }


def test_encode_response():
    assert encode_response(7, {"ok": True}) == {
        "jsonrpc": "2.0",
        "id": 7,
        "result": {"ok": True},
    }


def test_encode_error_carries_kind_in_data():
    assert encode_error(3, "rate", "slow down") == {
        "jsonrpc": "2.0",
        "id": 3,
        "error": {
            "code": APPLICATION_ERROR,
            "message": "slow down",
            "data": {"kind": "rate"},
        },
    }


def test_encode_notification_has_no_id():
    assert encode_notification("chat/chunk", {"text": "x"}) == {
        "jsonrpc": "2.0",
        "method": "chat/chunk",
        "params": {"text": "x"},
    }


def test_decode_line_roundtrip():
    line = encode_line(encode_request(1, "list_models", {}))
    assert decode_line(line)["method"] == "list_models"


def test_decode_line_malformed_returns_none():
    assert decode_line("not json\n") is None
    assert decode_line("{broken") is None


def test_decode_line_non_object_returns_none():
    assert decode_line("[1, 2]\n") is None
    assert decode_line("42\n") is None
    assert decode_line('"text"\n') is None
