"""Tests for the cache-first parser resolution: a cached language
resolves offline, and an uncached one falls back to the download."""

import pytest

from crapper.languages.treesitter import parser_for


class _Sentinel:
    pass


@pytest.fixture()
def clear_cache():
    parser_for.cache_clear()
    yield
    parser_for.cache_clear()


def test_parser_for_uses_the_cached_parser_first(monkeypatch, clear_cache):
    import tree_sitter_language_pack as pack

    sentinel = _Sentinel()

    def _boom(*args, **kwargs):
        raise AssertionError("download must not run for a cached language")

    monkeypatch.setattr(pack, "get_parser", lambda language: sentinel)
    monkeypatch.setattr(pack, "download", _boom)
    assert parser_for("python") is sentinel


def test_parser_for_downloads_when_the_cache_misses(
    monkeypatch, clear_cache
):
    import tree_sitter_language_pack as pack

    sentinel = _Sentinel()
    calls = {"get_parser": 0, "download": 0}

    def _get_parser(language):
        calls["get_parser"] += 1
        if calls["get_parser"] == 1:
            raise KeyError(language)
        return sentinel

    def _download(names):
        calls["download"] += 1
        return len(names)

    monkeypatch.setattr(pack, "get_parser", _get_parser)
    monkeypatch.setattr(pack, "download", _download)
    assert parser_for("python") is sentinel
    assert calls == {"get_parser": 2, "download": 1}
