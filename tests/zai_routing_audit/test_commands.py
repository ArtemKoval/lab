"""Tests for the CLI commands, run through main() with scripted transports."""

import json

import pytest

from conftest import TOKEN, FakeClock, FakeTransport
from zai_routing_audit import cli, core


def patch_transport(monkeypatch, fake):
    """Point the CLI at a scripted transport instance."""
    monkeypatch.setattr(cli, "LiveTransport", lambda *args, **kwargs: fake)
    return fake


def test_namespace_defaults():
    ns = cli.namespace()
    assert ns.json is False
    assert ns.spend_credits is False
    assert ns.names is None


def test_namespace_overrides():
    ns = cli.namespace(json=True, names=["a"])
    assert ns.json is True
    assert ns.names == ["a"]


def test_parser_requires_command(capsys):
    with pytest.raises(SystemExit) as excinfo:
        cli.build_parser().parse_args([])
    assert excinfo.value.code == 2


def test_parser_help_lists_all_commands(capsys):
    with pytest.raises(SystemExit) as excinfo:
        cli.build_parser().parse_args(["--help"])
    assert excinfo.value.code == 0
    out = capsys.readouterr().out
    for name in ("config", "transcripts", "echo", "usage", "throughput", "burn"):
        assert name in out


def test_parser_burn_flag_default():
    args = cli.build_parser().parse_args(["burn", "glm-5.3-flash"])
    assert args.spend_credits is False
    assert args.pad_words == 48000
    assert args.max_tokens == 1


def test_config_text_redacts_token(settings_file, capsys):
    code = cli.main(["config", "--settings", str(settings_file)])
    out = capsys.readouterr().out
    assert code == 0
    assert core.redact(TOKEN) in out
    assert TOKEN not in out


def test_config_json_parses(settings_file, capsys):
    code = cli.main(["--json", "config", "--settings", str(settings_file)])
    out = capsys.readouterr().out
    assert code == 0
    payload = json.loads(out)
    assert payload["base_url"] == "https://api.z.ai/api/anthropic"
    assert TOKEN not in out


def test_config_missing_file(settings_file, capsys):
    missing = settings_file.with_name("nope.json")
    code = cli.main(["config", "--settings", str(missing)])
    err = capsys.readouterr().err
    assert code == 2
    assert "error:" in err
    assert "nope.json" in err


def test_transcripts_command(transcript_dir, capsys):
    code = cli.main(["--json", "transcripts", "--directory", str(transcript_dir)])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["requested"] == {"glm-5.3-flash": 1}
    assert payload["files"] == 3


def test_transcripts_requires_directory(capsys):
    with pytest.raises(SystemExit):
        cli.build_parser().parse_args(["transcripts"])


def test_echo_match_exits_zero(settings_file, monkeypatch, capsys):
    fake = patch_transport(monkeypatch, FakeTransport(posts=[{"model": "glm-5.3-flash", "usage": {}}]))
    fake.base_url = "https://api.z.ai/api/anthropic"
    code = cli.main(["echo", "glm-5.3-flash", "--settings", str(settings_file)])
    assert code == 0


def test_echo_mismatch_exits_two(settings_file, monkeypatch, capsys):
    fake = patch_transport(monkeypatch, FakeTransport(posts=[{"model": "glm-5.3", "usage": {}}]))
    fake.base_url = "https://api.z.ai/api/anthropic"
    code = cli.main(["echo", "glm-5.3-flash", "--settings", str(settings_file)])
    assert code == 2


def test_echo_transport_error_has_no_traceback(settings_file, monkeypatch, capsys):
    from zai_routing_audit.core import TransportError

    fake = patch_transport(monkeypatch, FakeTransport(posts=[TransportError("HTTP 500: nope")]))
    fake.base_url = "https://api.z.ai/api/anthropic"
    code = cli.main(["echo", "glm-5.3-flash", "--settings", str(settings_file)])
    captured = capsys.readouterr()
    assert code == 2
    assert "HTTP 500" in captured.out
    assert "Traceback" not in captured.err


def test_echo_without_token_fails(settings_file, monkeypatch, capsys):
    import json as jsonlib

    path = settings_file.with_name("notoken.json")
    path.write_text(jsonlib.dumps({"env": {"ANTHROPIC_BASE_URL": "https://x"}}), encoding="utf-8")
    code = cli.main(["echo", "glm-5.3-flash", "--settings", str(path)])
    assert code == 2
    assert "no ANTHROPIC_AUTH_TOKEN" in capsys.readouterr().err


def test_echo_without_base_url_fails(settings_file, monkeypatch, capsys):
    import json as jsonlib

    path = settings_file.with_name("nobase.json")
    path.write_text(jsonlib.dumps({"env": {"ANTHROPIC_AUTH_TOKEN": "t"}}), encoding="utf-8")
    code = cli.main(["echo", "glm-5.3-flash", "--settings", str(path)])
    assert code == 2
    assert "no ANTHROPIC_BASE_URL" in capsys.readouterr().err


def test_usage_reports_rows_and_pools(settings_file, monkeypatch, capsys, model_usage_payload, quota_payload):
    fake = patch_transport(monkeypatch, FakeTransport(gets=[model_usage_payload, quota_payload]))
    fake.base_url = "https://api.z.ai/api/anthropic"
    code = cli.main(["--json", "usage", "--settings", str(settings_file)])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["models"][0]["model"] == "GLM-5.3"
    assert len(payload["pools"]) == 2
    assert "model-usage" in fake.get_calls[0]


def test_usage_explicit_window(settings_file, monkeypatch, model_usage_payload, quota_payload):
    fake = patch_transport(monkeypatch, FakeTransport(gets=[model_usage_payload, quota_payload]))
    fake.base_url = "https://api.z.ai/api/anthropic"
    cli.main(
        ["--json", "usage", "--settings", str(settings_file), "--start", "2026-10-13 00:00:00", "--end", "2026-10-15 23:59:59"]
    )
    assert "2026-10-13+00%3A00%3A00" in fake.get_calls[0]
    assert "2026-10-15+23%3A59%3A59" in fake.get_calls[0]


def test_usage_drift_prints_redacted_excerpt(settings_file, monkeypatch, capsys):
    fake = patch_transport(monkeypatch, FakeTransport(gets=[{"surprise": True}]))
    fake.base_url = "https://api.z.ai/api/anthropic"
    code = cli.main(["--json", "usage", "--settings", str(settings_file)])
    captured = capsys.readouterr()
    assert code == 2
    assert "unexpected model-usage shape" in captured.err
    assert TOKEN not in captured.err


def test_throughput_reports_rate(settings_file, monkeypatch, capsys):
    fake = patch_transport(monkeypatch, FakeTransport(posts=[{"model": "m", "usage": {"output_tokens": 100}}]))
    fake.base_url = "https://api.z.ai/api/anthropic"
    monkeypatch.setattr(core.time, "monotonic", FakeClock(step=5.0))
    code = cli.main(["--json", "throughput", "glm-5.3-flash", "--settings", str(settings_file)])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["results"][0]["tokens_per_second"] == 20.0


def test_burn_without_flag_sends_nothing(settings_file, monkeypatch, capsys):
    fake = patch_transport(monkeypatch, FakeTransport())
    fake.base_url = "https://api.z.ai/api/anthropic"
    code = cli.main(["--json", "burn", "glm-5.3-flash", "--settings", str(settings_file)])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["spend"] is False
    assert fake.post_calls == []
    assert fake.get_calls == []


def test_burn_with_flag_measures_deltas(
    settings_file, monkeypatch, capsys, quota_step
):
    fake = patch_transport(
        monkeypatch,
        FakeTransport(
            posts=[{"usage": {"input_tokens": 48021}}, {"usage": {"input_tokens": 48021}}],
            gets=[quota_step(2600), quota_step(2613), quota_step(2630)],
        ),
    )
    fake.base_url = "https://api.z.ai/api/anthropic"
    monkeypatch.setattr(core.time, "sleep", lambda seconds: None)
    code = cli.main(
        ["--json", "burn", "glm-5.3-flash", "glm-5.3", "--spend-credits", "--settings", str(settings_file)]
    )
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["spend"] is True
    assert payload["results"][0]["pools"][0]["delta"] == 13
    assert payload["results"][1]["pools"][0]["delta"] == 17


def test_text_printer_handles_nested_payload(capsys):
    cli._print_text({"a": {"b": [1, "x"]}, "c": 2})
    out = capsys.readouterr().out
    assert "a:" in out
    assert "c: 2" in out


def test_config_directory_path_exits_two(tmp_path, capsys):
    code = cli.main(["config", "--settings", str(tmp_path)])
    captured = capsys.readouterr()
    assert code == 2
    assert "error:" in captured.err
    assert "Traceback" not in captured.err


def test_no_command_output_ever_carries_the_token(
    settings_file, transcript_dir, monkeypatch, capsys, model_usage_payload, quota_payload
):
    fake = FakeTransport(
        posts=[
            {"model": "m", "usage": {"input_tokens": 1, "output_tokens": 1}},
            {"model": "m", "usage": {"output_tokens": 1}},
            {"model": "m", "usage": {"output_tokens": 1}},
            {"usage": {"input_tokens": 1}},
        ],
        gets=[model_usage_payload, quota_payload, quota_payload, quota_payload, quota_payload],
    )
    fake.base_url = "https://api.z.ai/api/anthropic"
    monkeypatch.setattr(cli, "LiveTransport", lambda *args, **kwargs: fake)
    monkeypatch.setattr(core.time, "monotonic", FakeClock(step=5.0))
    monkeypatch.setattr(core.time, "sleep", lambda seconds: None)
    argv_list = [
        ["--json", "config", "--settings", str(settings_file)],
        ["config", "--settings", str(settings_file)],
        ["--json", "transcripts", "--directory", str(transcript_dir)],
        ["--json", "echo", "m", "--settings", str(settings_file)],
        ["echo", "m", "--settings", str(settings_file)],
        ["--json", "usage", "--settings", str(settings_file)],
        ["--json", "throughput", "m", "--settings", str(settings_file)],
        ["--json", "burn", "m", "--spend-credits", "--settings", str(settings_file)],
        ["burn", "m", "--settings", str(settings_file)],
    ]
    for argv in argv_list:
        code = cli.main(argv)
        captured = capsys.readouterr()
        assert code == 0, (argv, captured.err)
        assert TOKEN not in captured.out, argv
        assert TOKEN not in captured.err, argv
