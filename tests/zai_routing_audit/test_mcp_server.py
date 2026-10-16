"""Tests for the thin FastMCP wrapper."""

import json

from conftest import TOKEN
from zai_routing_audit import mcp_server


def test_server_name():
    assert mcp_server.mcp.name == "zai-routing-audit"


def test_config_report_redacts(settings_file):
    payload = mcp_server.config_report(settings_path=str(settings_file))
    assert payload["token_redacted"] == TOKEN[:4] + "..."
    assert TOKEN not in json.dumps(payload)


def test_transcripts_scan_counts(transcript_dir):
    payload = mcp_server.transcripts_scan(directory=str(transcript_dir))
    assert payload["requested"] == {"glm-5.3-flash": 1}


def test_burn_plan_never_spends():
    payload = mcp_server.burn_plan(names=["glm-5.3-flash"])
    assert payload["spend"] is False
    assert payload["plan"]["names"] == ["glm-5.3-flash"]


def test_tools_are_registered():
    for name in ("config_report", "transcripts_scan", "echo_compare", "usage_report", "throughput_compare", "burn_plan"):
        assert callable(getattr(mcp_server, name))


def test_network_tools_with_fake_transport(
    monkeypatch, settings_file, model_usage_payload, quota_payload
):
    from conftest import FakeClock, FakeTransport
    from zai_routing_audit import cli as cli_mod
    from zai_routing_audit import core

    fake = FakeTransport(
        posts=[
            {"model": "m", "usage": {"output_tokens": 10}},
            {"model": "m", "usage": {"output_tokens": 10}},
        ],
        gets=[model_usage_payload, quota_payload],
    )
    fake.base_url = "https://api.z.ai/api/anthropic"
    monkeypatch.setattr(cli_mod, "LiveTransport", lambda *args, **kwargs: fake)
    monkeypatch.setattr(core, "DEFAULT_SETTINGS", settings_file)
    monkeypatch.setattr(core.time, "monotonic", FakeClock(step=2.0))

    echo = mcp_server.echo_compare(names=["m"])
    assert echo["results"][0]["echoed"] == "m"
    usage = mcp_server.usage_report()
    assert usage["models"][0]["model"] == "GLM-5.3"
    speed = mcp_server.throughput_compare(names=["m"])
    assert speed["results"][0]["tokens_per_second"] == 5.0


def test_main_starts_server(monkeypatch):
    monkeypatch.setattr(mcp_server.mcp, "run", lambda: None)
    mcp_server.main()
