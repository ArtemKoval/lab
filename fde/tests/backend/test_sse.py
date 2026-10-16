"""Tests for the SSE data-line reader."""

from backend.sse import DONE_MARKER, parse_data_line


def test_data_line_with_space():
    assert parse_data_line("data: hello") == "hello"


def test_data_line_without_space():
    assert parse_data_line("data:hello") == "hello"


def test_non_data_line_returns_none():
    assert parse_data_line(": comment") is None
    assert parse_data_line("event: message") is None


def test_empty_data_value_returns_none():
    assert parse_data_line("data:") is None
    assert parse_data_line("data: ") is None


def test_carriage_return_is_stripped():
    assert parse_data_line("data: x\r") == "x"


def test_trailing_space_before_the_carriage_return_is_kept():
    assert parse_data_line("data: x \r") == "x "


def test_trailing_x_before_the_carriage_return_is_kept():
    assert parse_data_line("data: hiX\r") == "hiX"


def test_done_marker_constant():
    assert DONE_MARKER == "[DONE]"
