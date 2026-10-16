"""Exactness tests. Each test pins a full payload, message, or request detail,
so that literal-level mutants die instead of surviving loose assertions."""

import json
import urllib.request

import pytest

from conftest import TOKEN, FakeClock, FakeTransport
from zai_routing_audit import cli, core
from zai_routing_audit.cli import build_parser


def test_constants_are_pinned():
    assert core.ECHO_PROMPT == "ping"
    assert core.THROUGHPUT_PROMPT == "Write 300 words about the history of lighthouses."
    assert core.BURN_MARKER == "BURNTEST."
    assert core.BURN_WORDS == ("apple", "banana", "cherry", "date")
    assert core.MODEL_SLOTS == (
        "ANTHROPIC_DEFAULT_HAIKU_MODEL",
        "ANTHROPIC_DEFAULT_SONNET_MODEL",
        "ANTHROPIC_DEFAULT_OPUS_MODEL",
        "ANTHROPIC_DEFAULT_FABLE_MODE",
        "CLAUDE_CODE_SUBAGENT_MODEL",
    )
    assert core.QUOTA_PATH == "/api/monitor/usage/quota/limit"
    assert core.MODEL_USAGE_PATH == "/api/monitor/usage/model-usage"


def test_redact_exact():
    assert core.redact(None) == ""
    assert core.redact("") == ""
    assert core.redact("abcd") == "abcd..."
    assert core.redact("abcdefgh") == "abcd..."


def test_sanitize_exact():
    assert core.sanitize("aTOKENb", "TOKEN") == "aTOKE...b"
    assert core.sanitize("plain", "TOKEN") == "plain"
    assert core.sanitize("plain", "") == "plain"


def test_tolerant_json_error_prefix():
    with pytest.raises(ValueError) as excinfo:
        core.tolerant_json("definitely not json")
    assert str(excinfo.value).startswith("unparsable JSON: ")


def test_console_base_exact():
    assert core.console_base("https://api.z.ai/api/anthropic") == "https://api.z.ai"
    with pytest.raises(ValueError) as excinfo:
        core.console_base("api.z.ai/no-scheme")
    assert str(excinfo.value) == "not a usable base URL: api.z.ai/no-scheme"


def test_urls_exact():
    assert core.quota_url("https://api.z.ai/api/anthropic") == (
        "https://api.z.ai/api/monitor/usage/quota/limit"
    )
    assert core.model_usage_url("https://api.z.ai/api/anthropic", "2026-10-15 00:00:00", "2026-10-15 23:59:59") == (
        "https://api.z.ai/api/monitor/usage/model-usage"
        "?startTime=2026-10-15+00%3A00%3A00&endTime=2026-10-15+23%3A59%3A59"
    )


def test_build_message_payload_exact():
    assert core.build_message_payload("glm-5.3-flash", 16, "ping") == {
        "model": "glm-5.3-flash",
        "max_tokens": 16,
        "messages": [{"role": "user", "content": "ping"}],
    }


def test_echo_success_entry_is_exact():
    transport = FakeTransport(
        posts=[{"model": "glm-5.3-flash", "usage": {"input_tokens": 7, "output_tokens": 9}}]
    )
    results = core.echo_compare(transport, ["glm-5.3-flash"])
    assert results == [
        {
            "requested": "glm-5.3-flash",
            "echoed": "glm-5.3-flash",
            "input_tokens": 7,
            "output_tokens": 9,
            "error": None,
        }
    ]
    path, payload = transport.post_calls[0]
    assert path == "/v1/messages"
    assert payload == {"model": "glm-5.3-flash", "max_tokens": 32, "messages": [{"role": "user", "content": "ping"}]}


def test_echo_error_entry_is_exact():
    from zai_routing_audit.core import TransportError

    transport = FakeTransport(posts=[TransportError("HTTP 500: nope")])
    results = core.echo_compare(transport, ["glm-5.3-flash"])
    assert results == [
        {
            "requested": "glm-5.3-flash",
            "echoed": None,
            "input_tokens": None,
            "output_tokens": None,
            "tokens_per_second": None,
            "error": "HTTP 500: nope",
        }
    ]


def test_echo_shape_error_message_is_exact():
    transport = FakeTransport(posts=["just a string"])
    results = core.echo_compare(transport, ["glm-5.3-flash"])
    assert results[0]["error"] == "unexpected messages shape"


def test_throughput_success_entry_is_exact():
    transport = FakeTransport(posts=[{"model": "m", "usage": {"output_tokens": 1}}])
    results = core.throughput_compare(transport, ["m"], clock=FakeClock(step=3.0))
    assert results == [
        {
            "requested": "m",
            "echoed": "m",
            "output_tokens": 1,
            "seconds": 3.0,
            "tokens_per_second": 0.3,
            "error": None,
        }
    ]


def test_throughput_small_elapsed_still_rates():
    transport = FakeTransport(posts=[{"model": "m", "usage": {"output_tokens": 100}}])
    results = core.throughput_compare(transport, ["m"], clock=FakeClock(step=0.5))
    assert results[0]["seconds"] == 0.5
    assert results[0]["tokens_per_second"] == 200.0


def test_throughput_request_details():
    transport = FakeTransport(posts=[{"model": "m", "usage": {"output_tokens": 1}}])
    core.throughput_compare(transport, ["m"], clock=FakeClock())
    path, payload = transport.post_calls[0]
    assert path == "/v1/messages"
    assert payload["max_tokens"] == 1024
    assert payload["model"] == "m"
    assert payload["messages"][0]["content"] == core.THROUGHPUT_PROMPT


def test_padded_prompt_exact():
    assert core.padded_prompt("apple", 2) == "BURNTEST. Ignore all padding. apple apple"


def test_burn_plan_exact():
    assert core.burn_plan(["a", "b"]) == {
        "spend": False,
        "plan": {"names": ["a", "b"], "pad_words": 48000, "max_tokens": 1},
    }
    assert core.burn_compare(FakeTransport(), "https://api.z.ai", ["a"]) == {
        "spend": False,
        "plan": {"names": ["a"], "pad_words": 48000, "max_tokens": 1},
    }


def test_burn_spend_entries_are_exact(quota_step):
    transport = FakeTransport(
        posts=[{"usage": {"input_tokens": 48021}}, {"usage": {"input_tokens": 48021}}],
        gets=[quota_step(2600), quota_step(2613), quota_step(2630)],
    )
    sleeps = []
    payload = core.burn_compare(
        transport,
        "https://api.z.ai",
        ["glm-5.3-flash", "glm-5.3"],
        spend=True,
        sleep=sleeps.append,
    )
    assert payload["spend"] is True
    assert payload["results"][0]["requested"] == "glm-5.3-flash"
    assert payload["results"][0]["input_tokens"] == 48021
    assert payload["results"][0]["pools"] == [
        {"type": "CREDIT_LIMIT", "before": 2600, "after": 2613, "delta": 13},
        {"type": "CREDIT_LIMIT", "before": 2729, "after": 2742, "delta": 13},
    ]
    assert payload["results"][1]["pools"][0] == {
        "type": "CREDIT_LIMIT",
        "before": 2613,
        "after": 2630,
        "delta": 17,
    }
    assert payload["results"][1]["pools"][1] == {
        "type": "CREDIT_LIMIT",
        "before": 2742,
        "after": 2759,
        "delta": 17,
    }
    assert sleeps == [2.0, 2.0]
    path, first_payload = transport.post_calls[0]
    assert path == "/v1/messages"
    assert first_payload["model"] == "glm-5.3-flash"
    assert first_payload["max_tokens"] == 1
    assert first_payload["messages"][0]["content"] == core.padded_prompt("apple", 48000)
    assert transport.post_calls[1][1]["model"] == "glm-5.3"
    assert transport.post_calls[1][1]["messages"][0]["content"] == core.padded_prompt("banana", 48000)


def test_parse_model_usage_rows_exact(model_usage_payload):
    rows = core.parse_model_usage(model_usage_payload)
    assert rows == [
        {"model": "GLM-5.3", "total_tokens": 1026439},
        {"model": "GLM-5.3-Flash", "total_tokens": 952},
    ]


def test_parse_model_usage_float_total_and_bucket_filter():
    payload = {
        "data": {
            "modelDataList": [
                {"modelName": "A", "totalTokens": 1.5},
                {"modelName": "B", "tokensUsage": [1, "x", 2]},
            ]
        }
    }
    assert core.parse_model_usage(payload) == [
        {"model": "A", "total_tokens": 1.5},
        {"model": "B", "total_tokens": 3},
    ]


def test_parse_model_usage_breaks_only_on_junk_rows():
    payload = {"data": {"modelDataList": ["junk", {"modelName": "A", "totalTokens": 5}]}}
    assert core.parse_model_usage(payload) == [{"model": "A", "total_tokens": 5}]


def test_parse_model_usage_drift_message_exact():
    with pytest.raises(ValueError) as excinfo:
        core.parse_model_usage({"data": {}})
    assert str(excinfo.value) == "unexpected model-usage shape"
    with pytest.raises(ValueError) as excinfo:
        core.parse_model_usage("nope")
    assert str(excinfo.value) == "unexpected model-usage shape"
    with pytest.raises(ValueError) as excinfo:
        core.parse_model_usage({"data": {"modelDataList": 7}})
    assert str(excinfo.value) == "unexpected model-usage shape"


def test_parse_quota_exact(quota_payload, quota_payload_alt):
    assert core.parse_quota(quota_payload) == [
        {"type": "CREDIT_LIMIT", "consumed": 2263, "remaining": 25736},
        {"type": "CREDIT_LIMIT", "consumed": 2392, "remaining": 137607},
    ]
    assert core.parse_quota(quota_payload_alt) == [
        {"type": "CREDIT_LIMIT", "consumed": 2263, "remaining": 25736}
    ]
    with pytest.raises(ValueError) as excinfo:
        core.parse_quota({"weird": True})
    assert str(excinfo.value) == "unexpected quota shape"
    with pytest.raises(ValueError) as excinfo:
        core.parse_quota("nope")
    assert str(excinfo.value) == "unexpected quota shape"


def test_shape_message_exact():
    assert core._shape_message("quota", {"a": 1}, "") == 'unexpected quota shape; body starts: {"a": 1}'
    assert core._shape_message("quota", "raw body", "") == "unexpected quota shape; body starts: raw body"
    long_body = json.dumps({"fill": "y" * 300})
    expected = f"unexpected model-usage shape; body starts: {long_body[:200]}"
    assert core._shape_message("model-usage", {"fill": "y" * 300}, "") == expected


def test_fetch_drift_messages_exact():
    transport = FakeTransport(gets=[{"fill": "y" * 300}])
    with pytest.raises(ValueError) as excinfo:
        core.fetch_pools(transport, "https://api.z.ai", token=TOKEN)
    assert transport.get_calls == [core.quota_url("https://api.z.ai")]
    expected = f"unexpected quota shape; body starts: {core.sanitize(json.dumps({'fill': 'y' * 300})[:200], TOKEN)}"
    assert str(excinfo.value) == expected


def test_day_bounds_exact():
    moment = __import__("datetime").datetime(2026, 10, 15, 20, 30, 15, 123456)
    assert core.day_bounds(moment) == ("2026-10-15 00:00:00", "2026-10-15 23:59:59")


def test_routing_facts_exact(settings_file):
    settings = core.load_json_file(settings_file)
    assert core.routing_facts(settings, settings_file) == {
        "settings_path": str(settings_file),
        "base_url": "https://api.z.ai/api/anthropic",
        "token_redacted": core.redact(TOKEN),
        "model_slots": {
            "ANTHROPIC_DEFAULT_SONNET_MODEL": "glm-5.3-flash[1m]",
        },
    }


def test_scan_counts_repeated_requests(tmp_path):
    lines = [
        json.dumps({"type": "api-request", "params": {"model": "glm-5.3-flash"}}),
        json.dumps({"type": "api-request", "params": {"model": "glm-5.3-flash"}}),
    ]
    (tmp_path / "s.jsonl").write_text("\n".join(lines), encoding="utf-8")
    stats = core.scan_transcripts(tmp_path)
    assert stats["requested"] == {"glm-5.3-flash": 2}
    assert stats["echoed"] == {}


def test_scan_survives_invalid_utf8_bytes(tmp_path):
    (tmp_path / "bad.jsonl").write_bytes(b'{"type":"assistant","message":{"model":"m\xff"}}\n')
    stats = core.scan_transcripts(tmp_path)
    assert list(stats["echoed"]) == ["m\ufffd"]
    assert stats["skipped_lines"] == 0


def test_transport_headers_exact(local_server):
    transport = core.LiveTransport(f"http://127.0.0.1:{local_server.server_address[1]}", "tok")
    assert transport._headers() == {
        "Authorization": "Bearer tok",
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
        "Accept": "application/json",
    }
    assert transport.base_url == f"http://127.0.0.1:{local_server.server_address[1]}"
    assert transport.timeout == 120.0
    assert core.LiveTransport("https://x/", "t", timeout=5.0).base_url == "https://x"
    assert core.LiveTransport("https://x", "t", timeout=5.0).timeout == 5.0


def test_transport_passes_timeout_to_urlopen(monkeypatch):
    seen = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b'{"ok": 1}'

    def fake_urlopen(request, timeout=None):
        seen["request"] = request
        seen["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    transport = core.LiveTransport("https://api.z.ai/api/anthropic", "tok")
    body = transport.post_json("/v1/messages", {"a": 1})
    assert body == {"ok": 1}
    assert seen["timeout"] == 120.0
    assert seen["request"].get_method() == "POST"
    assert transport.get_json("https://api.z.ai/x") == {"ok": 1}


def test_transport_http_error_message_exact(local_server):
    local_server.response = (500, b"boom")
    transport = core.LiveTransport(f"http://127.0.0.1:{local_server.server_address[1]}", "tok")
    with pytest.raises(core.TransportError) as excinfo:
        transport.post_json("/v1/messages", {})
    assert str(excinfo.value) == "HTTP 500: boom"


def test_transport_wire_headers_exact(local_server):
    base = f"http://127.0.0.1:{local_server.server_address[1]}"
    transport = core.LiveTransport(base, "tok")
    transport.post_json("/v1/messages", {"a": 1})
    sent = _wire_headers(local_server)
    assert sent == {
        "Authorization": "Bearer tok",
        "Anthropic-Version": "2023-06-01",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    assert local_server.received_body == b'{"a": 1}'
    transport.get_json(f"{base}/x")
    assert _wire_headers(local_server) == sent


def _wire_headers(local_server):
    return {
        k: v
        for k, v in local_server.received_headers.items()
        if not k.startswith(("Host", "Accept-Encoding", "Connection", "Content-Length", "User"))
    }


def test_namespace_defaults_exact():
    assert cli.namespace().__dict__ == {
        "func": None,
        "json": False,
        "settings": None,
        "base_url": None,
        "directory": None,
        "names": None,
        "max_tokens": None,
        "pad_words": None,
        "spend_credits": False,
        "start": None,
        "end": None,
    }


def test_config_json_output_is_exact(settings_file, capsys):
    expected_payload = {
        "settings_path": str(settings_file),
        "base_url": "https://api.z.ai/api/anthropic",
        "token_redacted": core.redact(TOKEN),
        "model_slots": {"ANTHROPIC_DEFAULT_SONNET_MODEL": "glm-5.3-flash[1m]"},
    }
    code = cli.main(["--json", "config", "--settings", str(settings_file)])
    out = capsys.readouterr().out
    assert code == 0
    assert out == json.dumps(expected_payload, indent=2, sort_keys=True) + "\n"


def test_echo_payload_is_exact(settings_file, monkeypatch, capsys):
    fake = FakeTransport(posts=[{"model": "glm-5.3-flash", "usage": {"input_tokens": 3, "output_tokens": 4}}])
    fake.base_url = "https://api.z.ai/api/anthropic"
    monkeypatch.setattr(cli, "LiveTransport", lambda *args, **kwargs: fake)
    code = cli.main(["--json", "echo", "glm-5.3-flash", "--settings", str(settings_file)])
    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "ok": True,
        "results": [
            {
                "requested": "glm-5.3-flash",
                "echoed": "glm-5.3-flash",
                "input_tokens": 3,
                "output_tokens": 4,
                "error": None,
            }
        ],
    }
    assert code == 0
    path, body = fake.post_calls[0]
    assert path == "/v1/messages"
    assert body == {
        "model": "glm-5.3-flash",
        "max_tokens": 32,
        "messages": [{"role": "user", "content": "ping"}],
    }


def test_usage_payload_is_exact(settings_file, monkeypatch, capsys, model_usage_payload, quota_payload):
    fake = FakeTransport(gets=[model_usage_payload, quota_payload])
    fake.base_url = "https://api.z.ai/api/anthropic"
    monkeypatch.setattr(cli, "LiveTransport", lambda *args, **kwargs: fake)
    code = cli.main(["--json", "usage", "--settings", str(settings_file)])
    payload = json.loads(capsys.readouterr().out)
    start, end = core.day_bounds()
    assert payload == {
        "window": {"start": start, "end": end},
        "models": [
            {"model": "GLM-5.3", "total_tokens": 1026439},
            {"model": "GLM-5.3-Flash", "total_tokens": 952},
        ],
        "pools": [
            {"type": "CREDIT_LIMIT", "consumed": 2263, "remaining": 25736},
            {"type": "CREDIT_LIMIT", "consumed": 2392, "remaining": 137607},
        ],
    }
    assert code == 0


def test_throughput_payload_is_exact(settings_file, monkeypatch, capsys):
    fake = FakeTransport(posts=[{"model": "m", "usage": {"output_tokens": 100}}])
    fake.base_url = "https://api.z.ai/api/anthropic"
    monkeypatch.setattr(cli, "LiveTransport", lambda *args, **kwargs: fake)
    monkeypatch.setattr(core.time, "monotonic", FakeClock(step=5.0))
    code = cli.main(["--json", "throughput", "m", "--settings", str(settings_file)])
    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "results": [
            {
                "requested": "m",
                "echoed": "m",
                "output_tokens": 100,
                "seconds": 5.0,
                "tokens_per_second": 20.0,
                "error": None,
            }
        ]
    }
    assert code == 0
    path, body = fake.post_calls[0]
    assert path == "/v1/messages"
    assert body["max_tokens"] == 1024
    assert body["messages"][0]["content"] == core.THROUGHPUT_PROMPT


def test_burn_spend_honors_explicit_values(settings_file, monkeypatch, capsys, quota_step):
    fake = FakeTransport(
        posts=[{"usage": {"input_tokens": 67}}],
        gets=[quota_step(2600), quota_step(2613)],
    )
    fake.base_url = "https://api.z.ai/api/anthropic"
    monkeypatch.setattr(cli, "LiveTransport", lambda *args, **kwargs: fake)
    monkeypatch.setattr(core.time, "sleep", lambda seconds: None)
    code = cli.main(
        [
            "--json", "burn", "glm-5.3-flash", "--spend-credits",
            "--pad-words", "100", "--max-tokens", "5", "--settings", str(settings_file),
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["spend"] is True
    assert payload["results"][0]["input_tokens"] == 67
    path, body = fake.post_calls[0]
    assert path == "/v1/messages"
    assert body["model"] == "glm-5.3-flash"
    assert body["max_tokens"] == 5
    assert body["messages"][0]["content"] == core.padded_prompt("apple", 100)


def test_resolve_builds_transport_from_settings(settings_file, monkeypatch):
    captured = {}

    class RecordingTransport:
        def __init__(self, base_url, token, timeout=120.0):
            captured["base_url"] = base_url
            captured["token"] = token

    monkeypatch.setattr(cli, "LiveTransport", RecordingTransport)
    transport, token = cli._resolve(cli.namespace(settings=str(settings_file), base_url=None))
    assert captured == {"base_url": "https://api.z.ai/api/anthropic", "token": TOKEN}
    assert transport is not None
    assert token == TOKEN


def test_usage_pool_drift_message_on_stderr_is_exact(settings_file, monkeypatch, capsys, model_usage_payload):
    drift = {"surprise": f"bad key {TOKEN}"}
    fake = FakeTransport(gets=[model_usage_payload, drift])
    fake.base_url = "https://api.z.ai/api/anthropic"
    monkeypatch.setattr(cli, "LiveTransport", lambda *args, **kwargs: fake)
    code = cli.main(["--json", "usage", "--settings", str(settings_file)])
    captured = capsys.readouterr()
    expected = f"error: unexpected quota shape; body starts: {core.sanitize(json.dumps(drift)[:200], TOKEN)}"
    assert code == 2
    assert captured.err == expected + "\n"
    assert TOKEN not in captured.err


def test_parser_prog_description_and_choice_helps():
    parser = build_parser()
    assert parser.prog == "zai_routing_audit"
    assert parser.description == "Audit the z.ai GLM model routing behind Claude Code."
    command_action = None
    for action in parser._actions:
        if action.dest == "command":
            command_action = action
    helps = {pa.dest: pa.help for pa in command_action._choices_actions}
    assert helps == {
        "config": "read back the routing settings",
        "transcripts": "scan Claude Code transcripts",
        "echo": "compare requested and echoed model names",
        "usage": "read per-model usage rows and credit pools",
        "throughput": "time one generation per model name",
        "burn": "measure the credit cost per model name",
    }


def test_parser_option_strings_are_exact():
    parser = build_parser()
    found = {}

    def walk(current, prefix):
        for action in current._actions:
            if action.dest != "help":
                key = prefix + action.dest
                if action.option_strings:
                    found[key] = tuple(action.option_strings)
                if getattr(action, "choices", None) and action.dest == "command":
                    for name, sub in action.choices.items():
                        walk(sub, name + ":")

    walk(parser, "")
    assert found == {
        "json": ("--json",),
        "config:settings": ("--settings",),
        "transcripts:directory": ("--directory",),
        "echo:max_tokens": ("--max-tokens",),
        "echo:settings": ("--settings",),
        "echo:base_url": ("--base-url",),
        "usage:start": ("--start",),
        "usage:end": ("--end",),
        "usage:settings": ("--settings",),
        "usage:base_url": ("--base-url",),
        "throughput:max_tokens": ("--max-tokens",),
        "throughput:settings": ("--settings",),
        "throughput:base_url": ("--base-url",),
        "burn:pad_words": ("--pad-words",),
        "burn:max_tokens": ("--max-tokens",),
        "burn:spend_credits": ("--spend-credits",),
        "burn:settings": ("--settings",),
        "burn:base_url": ("--base-url",),
    }


def test_parser_int_types_convert():
    parser = build_parser()
    args = parser.parse_args(["echo", "m", "--max-tokens", "7"])
    assert args.max_tokens == 7
    assert isinstance(args.max_tokens, int)
    args = parser.parse_args(["throughput", "m", "--max-tokens", "9"])
    assert args.max_tokens == 9
    assert isinstance(args.max_tokens, int)
    args = parser.parse_args(["burn", "m", "--pad-words", "5"])
    assert args.pad_words == 5
    assert isinstance(args.pad_words, int)


def test_burn_payloads_are_exact(settings_file, monkeypatch, capsys, quota_step):
    fake = FakeTransport()
    fake.base_url = "https://api.z.ai/api/anthropic"
    monkeypatch.setattr(cli, "LiveTransport", lambda *args, **kwargs: fake)
    code = cli.main(["--json", "burn", "glm-5.3-flash", "--settings", str(settings_file)])
    payload = json.loads(capsys.readouterr().out)
    assert payload == {"spend": False, "plan": {"names": ["glm-5.3-flash"], "pad_words": 48000, "max_tokens": 1}}
    assert code == 0

    fake2 = FakeTransport(
        posts=[{"usage": {"input_tokens": 48021}}],
        gets=[quota_step(2600), quota_step(2613)],
    )
    fake2.base_url = "https://api.z.ai/api/anthropic"
    monkeypatch.setattr(cli, "LiveTransport", lambda *args, **kwargs: fake2)
    monkeypatch.setattr(core.time, "sleep", lambda seconds: None)
    code = cli.main(
        ["--json", "burn", "glm-5.3-flash", "--spend-credits", "--settings", str(settings_file)]
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["spend"] is True
    assert payload["results"][0]["pools"] == [
        {"type": "CREDIT_LIMIT", "before": 2600, "after": 2613, "delta": 13},
        {"type": "CREDIT_LIMIT", "before": 2729, "after": 2742, "delta": 13},
    ]
    assert code == 0


def test_print_text_output_is_exact(capsys):
    cli._print_text({"a": {"b": [1, "x"]}, "c": 2})
    assert capsys.readouterr().out == "a:\n  b:\n    1\n    x\nc: 2\n"


def test_print_text_leaf_scalar(capsys):
    cli._print_text("solo")
    assert capsys.readouterr().out == "solo\n"


def test_console_base_rejects_scheme_without_host():
    with pytest.raises(ValueError):
        core.console_base("https://")


def test_transport_keeps_trailing_capital_x():
    assert core.LiveTransport("https://host/X", "t").base_url == "https://host/X"


def test_transport_replaces_invalid_utf8_in_success_body(local_server):
    local_server.response = (200, b'{"model": "m\xff"}')
    transport = core.LiveTransport(f"http://127.0.0.1:{local_server.server_address[1]}", "tok")
    assert transport.get_json(f"{transport.base_url}/x") == {"model": "m�"}


def test_transport_http_error_decodes_and_truncates(local_server):
    body = b"\xff" + b"boom" + b"y" * 300
    local_server.response = (500, body)
    transport = core.LiveTransport(f"http://127.0.0.1:{local_server.server_address[1]}", "tok")
    with pytest.raises(core.TransportError) as excinfo:
        transport.post_json("/v1/messages", {})
    assert str(excinfo.value) == "HTTP 500: " + "�boom" + "y" * 195


def test_burn_plan_honors_explicit_values(settings_file, monkeypatch, capsys):
    fake = FakeTransport()
    fake.base_url = "https://api.z.ai/api/anthropic"
    monkeypatch.setattr(cli, "LiveTransport", lambda *args, **kwargs: fake)
    code = cli.main(
        ["--json", "burn", "glm-5.3-flash", "--pad-words", "100", "--max-tokens", "5", "--settings", str(settings_file)]
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload == {"spend": False, "plan": {"names": ["glm-5.3-flash"], "pad_words": 100, "max_tokens": 5}}
    assert code == 0
    assert core.burn_compare(FakeTransport(), "https://api.z.ai", ["a"], pad_words=7, max_tokens=3) == {
        "spend": False,
        "plan": {"names": ["a"], "pad_words": 7, "max_tokens": 3},
    }


def test_fetch_model_rows_drift_message_exact_with_token():
    payload = {"error": f"bad key {TOKEN} and padding padding padding"}
    transport = FakeTransport(gets=[payload])
    with pytest.raises(ValueError) as excinfo:
        core.fetch_model_rows(transport, "https://api.z.ai", "s", "e", token=TOKEN)
    expected = f"unexpected model-usage shape; body starts: {core.sanitize(json.dumps(payload)[:200], TOKEN)}"
    assert str(excinfo.value) == expected
    assert TOKEN not in str(excinfo.value)
    assert core.redact(TOKEN) in str(excinfo.value)


def test_usage_drift_message_on_stderr_is_exact(settings_file, monkeypatch, capsys):
    drift = {"error": f"bad key {TOKEN}"}
    fake = FakeTransport(gets=[drift])
    fake.base_url = "https://api.z.ai/api/anthropic"
    monkeypatch.setattr(cli, "LiveTransport", lambda *args, **kwargs: fake)
    code = cli.main(["--json", "usage", "--settings", str(settings_file)])
    captured = capsys.readouterr()
    expected = f"error: unexpected model-usage shape; body starts: {core.sanitize(json.dumps(drift)[:200], TOKEN)}"
    assert code == 2
    assert captured.err == expected + "\n"
    assert TOKEN not in captured.err


def test_throughput_rounding_digits():
    transport = FakeTransport(posts=[{"model": "m", "usage": {"output_tokens": 1}}])
    results = core.throughput_compare(transport, ["m"], clock=FakeClock(step=0.3333))
    assert results[0]["seconds"] == 0.333
    assert results[0]["tokens_per_second"] == 3.0


def test_burn_drift_redacts_token(quota_payload):
    transport = FakeTransport(gets=[{"surprise": f"bad key {TOKEN}"}])
    with pytest.raises(ValueError) as excinfo:
        core.burn_compare(
            transport, "https://api.z.ai", ["glm-5.3-flash"], spend=True, token=TOKEN
        )
    assert transport.post_calls == []
    assert TOKEN not in str(excinfo.value)
    assert core.redact(TOKEN) in str(excinfo.value)

    transport2 = FakeTransport(
        posts=[{"usage": {"input_tokens": 1}}],
        gets=[quota_payload, {"surprise": f"bad key {TOKEN}"}],
    )
    with pytest.raises(ValueError) as excinfo:
        core.burn_compare(
            transport2, "https://api.z.ai", ["glm-5.3-flash"], spend=True, token=TOKEN
        )
    assert TOKEN not in str(excinfo.value)
    assert core.redact(TOKEN) in str(excinfo.value)


def test_echo_honors_explicit_max_tokens(settings_file, monkeypatch, capsys):
    fake = FakeTransport(posts=[{"model": "m", "usage": {}}])
    fake.base_url = "https://api.z.ai/api/anthropic"
    monkeypatch.setattr(cli, "LiveTransport", lambda *args, **kwargs: fake)
    code = cli.main(["--json", "echo", "m", "--max-tokens", "64", "--settings", str(settings_file)])
    assert code == 0
    assert fake.post_calls[0][1]["max_tokens"] == 64


def test_throughput_honors_explicit_max_tokens(settings_file, monkeypatch, capsys):
    fake = FakeTransport(posts=[{"model": "m", "usage": {"output_tokens": 1}}])
    fake.base_url = "https://api.z.ai/api/anthropic"
    monkeypatch.setattr(cli, "LiveTransport", lambda *args, **kwargs: fake)
    monkeypatch.setattr(core.time, "monotonic", FakeClock(step=5.0))
    code = cli.main(["--json", "throughput", "m", "--max-tokens", "555", "--settings", str(settings_file)])
    assert code == 0
    assert fake.post_calls[0][1]["max_tokens"] == 555


def test_burn_drift_message_on_stderr_is_exact(settings_file, monkeypatch, capsys, quota_payload):
    drift = {"surprise": f"bad key {TOKEN}"}
    fake = FakeTransport(gets=[drift])
    fake.base_url = "https://api.z.ai/api/anthropic"
    monkeypatch.setattr(cli, "LiveTransport", lambda *args, **kwargs: fake)
    code = cli.main(["--json", "burn", "glm-5.3-flash", "--spend-credits", "--settings", str(settings_file)])
    captured = capsys.readouterr()
    expected = f"error: unexpected quota shape; body starts: {core.sanitize(json.dumps(drift)[:200], TOKEN)}"
    assert code == 2
    assert captured.err == expected + "\n"
    assert TOKEN not in captured.err
