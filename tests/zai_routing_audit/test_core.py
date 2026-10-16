"""Unit tests for the core audit logic."""

import json

import pytest

from zai_routing_audit import core
from zai_routing_audit.core import TransportError

from conftest import TOKEN, FakeClock, FakeTransport


def test_redact_empty():
    assert core.redact("") == ""


def test_redact_none():
    assert core.redact(None) == ""


def test_redact_short_secret():
    assert core.redact("abc") == "abc..."


def test_redact_long_secret():
    assert core.redact(TOKEN) == TOKEN[:4] + "..."


def test_sanitize_replaces_token():
    text = f"Bearer {TOKEN} ok"
    assert core.sanitize(text, TOKEN) == f"Bearer {core.redact(TOKEN)} ok"


def test_sanitize_without_token():
    assert core.sanitize("plain", "") == "plain"


def test_sanitize_leaves_other_text():
    assert core.sanitize("no secret here", TOKEN) == "no secret here"


def test_load_json_file(tmp_path):
    path = tmp_path / "x.json"
    path.write_text('{"a": 1}', encoding="utf-8")
    assert core.load_json_file(path) == {"a": 1}


def test_load_json_file_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        core.load_json_file(tmp_path / "nope.json")


def test_routing_facts_full(settings_file):
    settings = core.load_json_file(settings_file)
    facts = core.routing_facts(settings, settings_file)
    assert facts["base_url"] == "https://api.z.ai/api/anthropic"
    assert facts["token_redacted"] == core.redact(TOKEN)
    assert facts["model_slots"]["ANTHROPIC_DEFAULT_SONNET_MODEL"] == "glm-5.3-flash[1m]"
    assert facts["settings_path"] == str(settings_file)


def test_routing_facts_empty_env():
    facts = core.routing_facts({}, "x")
    assert facts["base_url"] is None
    assert facts["model_slots"] == {}
    assert facts["token_redacted"] == ""


def test_settings_token_present_and_absent():
    assert core.settings_token({"env": {"ANTHROPIC_AUTH_TOKEN": "t"}}) == "t"
    assert core.settings_token({}) == ""


def test_tolerant_json_strict():
    assert core.tolerant_json('{"a": 1}') == {"a": 1}


def test_tolerant_json_control_characters():
    assert core.tolerant_json('{"a": "g\x01lm"}') == {"a": "g\x01lm"}


def test_tolerant_json_garbage():
    with pytest.raises(ValueError):
        core.tolerant_json("not json at all")


def test_console_base_ok():
    assert core.console_base("https://api.z.ai/api/anthropic") == "https://api.z.ai"


def test_console_base_rejects_bad_url():
    with pytest.raises(ValueError):
        core.console_base("api.z.ai/no-scheme")


def test_model_usage_url_encodes_window():
    url = core.model_usage_url("https://api.z.ai/api/anthropic", "2026-10-15 00:00:00", "2026-10-15 23:59:59")
    assert url.startswith("https://api.z.ai/api/monitor/usage/model-usage?")
    assert "startTime=2026-10-15+00%3A00%3A00" in url
    assert "endTime=2026-10-15+23%3A59%3A59" in url


def test_quota_url():
    assert core.quota_url("https://api.z.ai/api/anthropic") == "https://api.z.ai/api/monitor/usage/quota/limit"


def test_build_message_payload():
    payload = core.build_message_payload("glm-5.3-flash", 16, "ping")
    assert payload["model"] == "glm-5.3-flash"
    assert payload["max_tokens"] == 16
    assert payload["messages"] == [{"role": "user", "content": "ping"}]


def test_echo_compare_matches():
    transport = FakeTransport(posts=[{"model": "glm-5.3-flash", "usage": {"input_tokens": 1, "output_tokens": 2}}])
    results = core.echo_compare(transport, ["glm-5.3-flash"])
    assert results[0]["echoed"] == "glm-5.3-flash"
    assert results[0]["error"] is None
    assert core.echo_ok(results)
    path, payload = transport.post_calls[0]
    assert path == "/v1/messages"
    assert payload["model"] == "glm-5.3-flash"


def test_echo_compare_mismatch():
    transport = FakeTransport(posts=[{"model": "glm-5.3"}])
    results = core.echo_compare(transport, ["glm-5.3-flash"])
    assert not core.echo_ok(results)


def test_echo_compare_transport_error():
    transport = FakeTransport(posts=[TransportError("HTTP 500")])
    results = core.echo_compare(transport, ["glm-5.3-flash"])
    assert results[0]["error"] == "HTTP 500"
    assert not core.echo_ok(results)


def test_echo_compare_non_dict_body():
    transport = FakeTransport(posts=["just a string"])
    results = core.echo_compare(transport, ["glm-5.3-flash"])
    assert "shape" in results[0]["error"]
    assert not core.echo_ok(results)


def test_throughput_entry_math():
    transport = FakeTransport(posts=[{"model": "m", "usage": {"output_tokens": 100}}])
    results = core.throughput_compare(transport, ["m"], clock=FakeClock(step=5.0))
    assert results[0]["seconds"] == 5.0
    assert results[0]["tokens_per_second"] == 20.0


def test_throughput_zero_elapsed_gives_no_rate():
    clock = FakeClock(step=0.0)
    transport = FakeTransport(posts=[{"model": "m", "usage": {"output_tokens": 10}}])
    results = core.throughput_compare(transport, ["m"], clock=clock)
    assert results[0]["tokens_per_second"] is None


def test_throughput_transport_error():
    transport = FakeTransport(posts=[TransportError("down")])
    results = core.throughput_compare(transport, ["m"], clock=FakeClock())
    assert results == [
        {
            "requested": "m",
            "echoed": None,
            "input_tokens": None,
            "output_tokens": None,
            "tokens_per_second": None,
            "error": "down",
        }
    ]


def test_throughput_non_dict_body():
    transport = FakeTransport(posts=["nope"])
    results = core.throughput_compare(transport, ["m"], clock=FakeClock())
    assert results[0]["error"] == "unexpected messages shape"


def test_padded_prompt_word_count():
    prompt = core.padded_prompt("apple", 400)
    assert prompt.startswith(core.BURN_MARKER)
    assert prompt.count("apple") == 400


def test_burn_plan_sends_nothing():
    transport = FakeTransport()
    payload = core.burn_compare(transport, "https://api.z.ai", ["glm-5.3-flash"])
    assert payload["spend"] is False
    assert payload["plan"]["names"] == ["glm-5.3-flash"]
    assert transport.post_calls == []
    assert transport.get_calls == []


def test_burn_spend_measures_deltas(quota_step):
    posts = [
        {"usage": {"input_tokens": 48021}},
        {"usage": {"input_tokens": 48021}},
    ]
    gets = [quota_step(2600), quota_step(2613), quota_step(2630)]
    transport = FakeTransport(posts=posts, gets=gets)
    payload = core.burn_compare(
        transport,
        "https://api.z.ai",
        ["glm-5.3-flash", "glm-5.3"],
        spend=True,
        sleep=lambda seconds: None,
        token="",
    )
    assert payload["spend"] is True
    first, second = payload["results"]
    assert first["input_tokens"] == 48021
    assert first["pools"][0]["delta"] == 13
    assert second["pools"][0]["delta"] == 17
    assert second["pools"][0]["before"] == 2613


def test_burn_rotates_padding_words(quota_step):
    transport = FakeTransport(
        posts=[{"usage": {"input_tokens": 1}}, {"usage": {"input_tokens": 1}}],
        gets=[quota_step(1), quota_step(1), quota_step(1)],
    )
    core.burn_compare(
        transport,
        "https://api.z.ai",
        ["a", "b"],
        pad_words=1,
        spend=True,
        sleep=lambda seconds: None,
        token="",
    )
    first_prompt = transport.post_calls[0][1]["messages"][0]["content"]
    second_prompt = transport.post_calls[1][1]["messages"][0]["content"]
    assert first_prompt != second_prompt


def test_pool_delta_beyond_snapshot_is_none(quota_payload):
    before = core.parse_quota(quota_payload)
    after = before + [{"type": "NEW_LIMIT", "consumed": 5, "remaining": 5}]
    deltas = core._pool_deltas(before, after)
    assert deltas[0]["delta"] == 0
    assert deltas[1]["delta"] == 0
    assert deltas[2]["delta"] is None
    assert deltas[2]["before"] is None


def test_parse_model_usage_totals(quota_step, model_usage_payload):
    rows = core.parse_model_usage(model_usage_payload)
    assert rows[0] == {"model": "GLM-5.3", "total_tokens": 1026439}
    assert rows[1] == {"model": "GLM-5.3-Flash", "total_tokens": 952}


def test_parse_model_usage_skips_non_dict_rows(model_usage_payload):
    model_usage_payload["data"]["modelDataList"].append("junk")
    rows = core.parse_model_usage(model_usage_payload)
    assert len(rows) == 2


def test_row_total_unknown_when_no_token_fields():
    assert core._row_total({"modelName": "x"}) is None


def test_parse_model_usage_drift():
    with pytest.raises(ValueError):
        core.parse_model_usage({"data": {}})
    with pytest.raises(ValueError):
        core.parse_model_usage("nope")
    with pytest.raises(ValueError):
        core.parse_model_usage({"data": {"modelDataList": 7}})


def test_parse_quota_documented_envelope(quota_payload):
    pools = core.parse_quota(quota_payload)
    assert pools[0] == {"type": "CREDIT_LIMIT", "consumed": 2263, "remaining": 25736}
    assert len(pools) == 2


def test_parse_quota_alternate_envelope(quota_payload_alt):
    pools = core.parse_quota(quota_payload_alt)
    assert pools[0]["consumed"] == 2263


def test_parse_quota_skips_non_dict_limits(quota_payload_alt):
    quota_payload_alt["limits"].append("junk")
    assert len(core.parse_quota(quota_payload_alt)) == 1


def test_parse_quota_drift():
    with pytest.raises(ValueError):
        core.parse_quota({"weird": True})
    with pytest.raises(ValueError):
        core.parse_quota("nope")


def test_fetch_pools_drift_excerpt_redacts_token():
    transport = FakeTransport(gets=[{"error": f"bad key {TOKEN}"}])
    with pytest.raises(ValueError) as excinfo:
        core.fetch_pools(transport, "https://api.z.ai", token=TOKEN)
    message = str(excinfo.value)
    assert "unexpected quota shape" in message
    assert "body starts:" in message
    assert TOKEN not in message
    assert core.redact(TOKEN) in message


def test_fetch_model_rows_drift_excerpt_redacts_token():
    transport = FakeTransport(gets=[{"surprise": True}])
    with pytest.raises(ValueError) as excinfo:
        core.fetch_model_rows(transport, "https://api.z.ai", "s", "e", token=TOKEN)
    message = str(excinfo.value)
    assert "unexpected model-usage shape" in message
    assert TOKEN not in message


def test_day_bounds_known_moment():
    moment = __import__("datetime").datetime(2026, 10, 15, 20, 30, 15)
    start, end = core.day_bounds(moment)
    assert start == "2026-10-15 00:00:00"
    assert end == "2026-10-15 23:59:59"


def test_scan_transcripts_counts_both_directions(transcript_dir):
    stats = core.scan_transcripts(transcript_dir)
    assert stats["files"] == 3
    assert stats["requested"] == {"glm-5.3-flash": 1}
    assert stats["echoed"]["glm-5.3-flash"] == 2
    assert stats["echoed"]["glm-5.3"] == 1


def test_scan_transcripts_sums_usage(transcript_dir):
    stats = core.scan_transcripts(transcript_dir)
    usage = stats["usage"]["glm-5.3-flash"]
    assert usage == {"input": 13, "cache_write": 0, "cache_read": 5, "output": 16}


def test_scan_transcripts_accumulates_usage_across_records(tmp_path):
    lines = [
        json.dumps(
            {
                "type": "assistant",
                "message": {
                    "model": "m",
                    "usage": {"input_tokens": 5, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0, "output_tokens": 1},
                },
            }
        ),
        json.dumps(
            {
                "type": "assistant",
                "message": {
                    "model": "m",
                    "usage": {"input_tokens": 7, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0, "output_tokens": 2},
                },
            }
        ),
    ]
    (tmp_path / "s.jsonl").write_text("\n".join(lines), encoding="utf-8")
    stats = core.scan_transcripts(tmp_path)
    assert stats["usage"]["m"] == {"input": 12, "cache_write": 0, "cache_read": 0, "output": 3}


def test_scan_transcripts_skips_hostile_lines(transcript_dir):
    stats = core.scan_transcripts(transcript_dir)
    assert stats["skipped_lines"] == 4
    assert "g\x01lm" in stats["echoed"]


def test_scan_transcripts_empty_directory(tmp_path):
    stats = core.scan_transcripts(tmp_path)
    assert stats == {"files": 0, "skipped_lines": 0, "requested": {}, "echoed": {}, "usage": {}}


def test_parse_line_unknown_and_non_dict():
    assert core._parse_line('{"type": "other"}') == (None, None, None)
    assert core._parse_line("[1]") == (None, None, None)


def test_scan_file_missing_usage_key(transcript_dir, tmp_path):
    line = json.dumps({"type": "assistant", "message": {"model": "m"}})
    path = tmp_path / "only.jsonl"
    path.write_text(line, encoding="utf-8")
    stats = core.scan_transcripts(tmp_path)
    assert "m" not in stats["usage"]
    assert stats["echoed"]["m"] == 1


def test_live_transport_post_and_get(local_server):
    base = f"http://127.0.0.1:{local_server.server_address[1]}"
    transport = core.LiveTransport(base, "tok")
    body = transport.post_json("/v1/messages", {"model": "glm-5.3-flash"})
    assert body == {"model": "glm-5.3-flash"}
    assert local_server.received_headers["Authorization"] == "Bearer tok"
    assert json.loads(local_server.received_body)["model"] == "glm-5.3-flash"
    assert transport.get_json(f"{base}/anything") == {"model": "glm-5.3-flash"}


def test_live_transport_tolerates_control_characters(local_server):
    base = f"http://127.0.0.1:{local_server.server_address[1]}"
    local_server.response = (200, b'{"model": "g\x01lm"}')
    transport = core.LiveTransport(base, "tok")
    assert transport.get_json(f"{base}/x") == {"model": "g\x01lm"}


def test_live_transport_http_error(local_server):
    local_server.response = (500, b"boom")
    transport = core.LiveTransport(f"http://127.0.0.1:{local_server.server_address[1]}", "tok")
    with pytest.raises(TransportError) as excinfo:
        transport.post_json("/v1/messages", {})
    assert "HTTP 500" in str(excinfo.value)


def test_live_transport_connection_error():
    import socket

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        dead_port = sock.getsockname()[1]
    transport = core.LiveTransport(f"http://127.0.0.1:{dead_port}", "tok", timeout=2.0)
    with pytest.raises(TransportError) as excinfo:
        transport.post_json("/v1/messages", {})
    assert "connection failed" in str(excinfo.value)


def test_default_settings_points_at_user_settings():
    assert core.DEFAULT_SETTINGS.name == "settings.json"
