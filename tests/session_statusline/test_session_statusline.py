"""Behavior tests for the session status line renderer.

One test per spec scenario, plus the cache and format seams. The
clock, the transport, and the cache directory inject through the
render arguments, and the suite stays hermetic.
"""

import io
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest
from session_statusline import (
    cache_totals,
    default_transport,
    degraded_line,
    fmt_cache_rate,
    fmt_millions,
    fmt_pct,
    load_payload,
    main,
    pool_percentages,
    read_transcript_sums,
    render,
    transcript_sums,
    usable_offset,
    write_json_cache,
)

NOW = datetime(2026, 11, 10, 14, 5, tzinfo=UTC).timestamp()
FULL_PAYLOAD = {
    "session_id": "s1",
    "transcript_path": "",
    "model": {"display_name": "GLM-5.3-Flash"},
    "effort": {"level": "high"},
    "rate_limits": {
        "five_hour": {"used_percentage": 9},
        "seven_day": {"used_percentage": 83},
    },
    "prompt_cache": {"hit_ratio": 0.98},
}


def usage_line(total_in, total_out, cache_read=0, cache_creation=0):
    return json.dumps(
        {
            "type": "assistant",
            "message": {
                "usage": {
                    "input_tokens": total_in,
                    "output_tokens": total_out,
                    "cache_read_input_tokens": cache_read,
                    "cache_creation_input_tokens": cache_creation,
                }
            },
        }
    )


def write_transcript(tmp_path, lines):
    transcript = tmp_path / "session.jsonl"
    transcript.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(transcript)


def fake_transport(pools=None, code=0):
    calls = []

    def transport(argv):
        calls.append(argv)
        if code != 0:
            return code, ""
        return 0, json.dumps({"pools": pools or []})

    transport.calls = calls
    return transport


def render_line(payload, tmp_path, transport=None, now=NOW):
    line, fields = render(
        payload, now, transport or fake_transport(), tmp_path
    )
    return line, fields


def test_complete_payload_renders_every_field(tmp_path):
    transcript = write_transcript(
        tmp_path, [usage_line(606225, 205336)]
    )
    payload = {**FULL_PAYLOAD, "transcript_path": transcript}
    line, fields = render_line(payload, tmp_path)
    assert "GLM-5.3-Flash" in line
    assert "effort high" in line
    assert "5h 9%" in line
    assert "wk 83%" in line
    assert "cache 98%" in line
    assert "in 0.61M" in line
    assert "out 0.21M" in line
    assert line.endswith("14:05 UTC")
    assert fields["fault"] is None
    assert len(line) < 100
    # Task 1.7 pin: the standard payload line is exactly 91 characters.
    assert line == (
        "GLM-5.3-Flash | effort high | 5h 9% | wk 83% | cache 98% "
        "| in 0.61M | out 0.21M | 14:05 UTC"
    )
    assert len(line) == 91


def test_absent_effort_renders_na(tmp_path):
    payload = {key: value for key, value in FULL_PAYLOAD.items() if key != "effort"}
    line, _ = render_line(payload, tmp_path)
    assert "effort n/a" in line


@pytest.mark.parametrize(
    "level,shown",
    [
        ("none", "low"),
        ("minimal", "low"),
        ("low", "low"),
        ("medium", "high"),
        ("high", "high"),
        ("xhigh", "max"),
        ("max", "max"),
    ],
)
def test_table_row_maps_to_the_coding_plan_effort(tmp_path, level, shown):
    payload = {**FULL_PAYLOAD, "effort": {"level": level}}
    line, fields = render_line(payload, tmp_path)
    assert fields["effort"] == shown
    assert f"effort {shown}" in line


def test_unknown_level_stays_raw(tmp_path):
    payload = {**FULL_PAYLOAD, "effort": {"level": "turbo"}}
    line, fields = render_line(payload, tmp_path)
    assert fields["effort"] == "turbo"
    assert "effort turbo" in line


def test_mixed_case_level_maps_to_high(tmp_path):
    payload = {**FULL_PAYLOAD, "effort": {"level": "HIGH"}}
    line, fields = render_line(payload, tmp_path)
    assert fields["effort"] == "high"
    assert "effort high" in line


def test_falsy_level_renders_na(tmp_path):
    payload = {**FULL_PAYLOAD, "effort": {"level": 0}}
    _, fields = render_line(payload, tmp_path)
    assert fields["effort"] == "n/a"


def test_truthy_non_string_level_stays_raw(tmp_path):
    payload = {**FULL_PAYLOAD, "effort": {"level": 42}}
    _, fields = render_line(payload, tmp_path)
    assert fields["effort"] == 42


def test_map_applies_without_a_model_name(tmp_path):
    payload = {key: value for key, value in FULL_PAYLOAD.items() if key != "model"}
    payload = {**payload, "effort": {"level": "xhigh"}}
    line, fields = render_line(payload, tmp_path)
    assert fields["effort"] == "max"
    assert "effort max" in line


def test_json_effort_carries_the_mapped_value(monkeypatch, capsys, tmp_path):
    payload = {**FULL_PAYLOAD, "effort": {"level": "xhigh"}}
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
    assert main(["--json", "--cache-dir", str(tmp_path / "c")]) == 0
    fields = json.loads(capsys.readouterr().out)
    assert fields["effort"] == "max"


def test_line_joins_blocks_with_the_separator(tmp_path):
    payload = {**FULL_PAYLOAD, "effort": {"level": "xhigh"}}
    line, _ = render_line(payload, tmp_path)
    assert line.count(" | ") == 7
    assert "GLM-5.3-Flash | effort max |" in line


def test_scenario_payload_renders_the_full_then(tmp_path):
    transcript = write_transcript(
        tmp_path, [usage_line(606225, 205336)]
    )
    payload = {**FULL_PAYLOAD, "effort": {"level": "xhigh"}}
    payload = {**payload, "transcript_path": transcript}
    line, _ = render_line(payload, tmp_path)
    assert line.count(" | ") == 7
    assert "GLM-5.3-Flash" in line
    assert "effort max" in line
    assert "5h 9%" in line
    assert "wk 83%" in line
    assert "cache 98%" in line
    assert "in 0.61M" in line
    assert "out 0.21M" in line
    assert line.endswith(" UTC")


def test_degraded_line_joins_fields_with_the_separator():
    line, _ = degraded_line(NOW)
    assert line.count(" | ") == 7
    assert line == (
        "statusline: unparsable payload | effort n/a | 5h n/a | wk n/a "
        "| cache n/a | in n/a | out n/a | 14:05 UTC"
    )


def test_absent_cache_object_falls_back_to_transcript(tmp_path):
    transcript = write_transcript(
        tmp_path, [usage_line(1000, 500, cache_read=8000, cache_creation=1000)]
    )
    payload = {**FULL_PAYLOAD, "transcript_path": transcript}
    del payload["prompt_cache"]
    line, _ = render_line(payload, tmp_path)
    assert "cache 80%" in line


def test_empty_transcript_renders_zero_totals_and_na_cache(tmp_path):
    payload = {**FULL_PAYLOAD, "transcript_path": ""}
    del payload["prompt_cache"]
    line, _ = render_line(payload, tmp_path)
    assert "cache n/a" in line
    assert "in n/a" in line
    assert "out n/a" in line


def test_no_usage_rows_render_zero_totals(tmp_path):
    transcript = write_transcript(tmp_path, ['{"type":"user"}'])
    payload = {**FULL_PAYLOAD, "transcript_path": transcript}
    del payload["prompt_cache"]
    line, _ = render_line(payload, tmp_path)
    assert "in 0.00M" in line
    assert "out 0.00M" in line
    assert "cache n/a" in line


def test_totals_survive_refresh(tmp_path):
    transcript = write_transcript(tmp_path, [usage_line(500000, 100000)])
    payload = {**FULL_PAYLOAD, "transcript_path": transcript}
    cache_dir = tmp_path / "cache"
    first, _ = render(payload, NOW, fake_transport(), cache_dir)
    with open(transcript, "a", encoding="utf-8") as handle:
        handle.write(usage_line(106225, 105336) + "\n")
    second, _ = render(payload, NOW, fake_transport(), cache_dir)
    assert "in 0.50M" in first
    assert "in 0.61M" in second
    assert "out 0.21M" in second


def test_new_session_resets_totals(tmp_path):
    transcript = write_transcript(tmp_path, [usage_line(606225, 205336)])
    payload = {**FULL_PAYLOAD, "transcript_path": transcript}
    cache_dir = tmp_path / "cache"
    render(payload, NOW, fake_transport(), cache_dir)
    fresh = {**payload, "session_id": "s2"}
    transcript2 = write_transcript(tmp_path, [usage_line(10, 20)])
    fresh = {**fresh, "transcript_path": transcript2}
    _, fields = render(fresh, NOW, fake_transport(), cache_dir)
    assert fields["in_millions"] == "0.00M"


def test_stale_offset_triggers_full_reread(tmp_path):
    transcript = write_transcript(tmp_path, [usage_line(606225, 205336)])
    payload = {**FULL_PAYLOAD, "transcript_path": transcript}
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    (cache_dir / "sums.json").write_text(
        json.dumps(
            {"session_id": "s1", "offset": 10 ** 9, "in": 500000,
             "out": 900000, "cache_read": 0, "cache_creation": 0}
        )
    )
    _, fields = render(payload, NOW, fake_transport(), cache_dir)
    assert fields["in_millions"] == "0.61M"
    assert fields["out_millions"] == "0.21M"


def test_partial_line_is_skipped(tmp_path):
    transcript = write_transcript(
        tmp_path,
        [
            usage_line(100000, 200000),
            '{"broken": ',
            usage_line(300000, 400000),
        ],
    )
    payload = {**FULL_PAYLOAD, "transcript_path": transcript}
    del payload["prompt_cache"]
    _, fields = render_line(payload, tmp_path)
    assert fields["in_millions"] == "0.40M"
    assert fields["out_millions"] == "0.60M"


def test_missing_transcript_renders_na_totals(tmp_path):
    payload = {**FULL_PAYLOAD, "transcript_path": str(tmp_path / "gone.jsonl")}
    _, fields = render_line(payload, tmp_path)
    assert fields["in_millions"] == "n/a"
    assert fields["out_millions"] == "n/a"


def test_payload_rate_limits_win(tmp_path):
    transport = fake_transport()
    _, fields = render_line(FULL_PAYLOAD, tmp_path, transport=transport)
    assert fields["five"] == "9%"
    assert fields["seven"] == "83%"
    assert transport.calls == []


def test_one_absent_window_reads_console(tmp_path):
    transport = fake_transport(
        pools=[
            {"type": "CREDIT_LIMIT", "consumed": 2537, "remaining": 25462},
            {"type": "CREDIT_LIMIT", "consumed": 116129, "remaining": 23870},
        ]
    )
    payload = {
        "session_id": "s1",
        "transcript_path": "",
        "model": {"display_name": "GLM-5.3-Flash"},
        "rate_limits": {"five_hour": {"used_percentage": 9}},
    }
    _, fields = render_line(payload, tmp_path, transport=transport)
    assert fields["five"] == "9%"
    assert fields["seven"] == "83%"
    assert len(transport.calls) == 1


def test_zero_total_pool_renders_na(tmp_path):
    transport = fake_transport(
        pools=[
            {"type": "CREDIT_LIMIT", "consumed": 0, "remaining": 0},
            {"type": "CREDIT_LIMIT", "consumed": 10, "remaining": 90},
        ]
    )
    _, fields = render_line(
        {"session_id": "s1", "transcript_path": "",
         "model": {"display_name": "m"}}, tmp_path, transport=transport
    )
    assert fields["five"] == "n/a"
    assert fields["seven"] == "10%"


def test_pool_count_that_is_not_two_renders_na(tmp_path):
    transport = fake_transport(
        pools=[{"type": "CREDIT_LIMIT", "consumed": 1, "remaining": 1}]
    )
    _, fields = render_line(
        {"session_id": "s1", "transcript_path": "",
         "model": {"display_name": "m"}}, tmp_path, transport=transport
    )
    assert fields["five"] == "n/a"
    assert fields["seven"] == "n/a"


def test_fresh_cache_makes_no_console_call(tmp_path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    (cache_dir / "console.json").write_text(
        json.dumps({"updated": NOW - 10, "five": 5, "seven": 50})
    )
    transport = fake_transport()
    _, fields = render(
        {"session_id": "s1", "transcript_path": "",
         "model": {"display_name": "m"}},
        NOW, transport, cache_dir,
    )
    assert fields["five"] == "5%"
    assert fields["seven"] == "50%"
    assert transport.calls == []


def test_failed_console_read_serves_stale_cache(tmp_path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    (cache_dir / "console.json").write_text(
        json.dumps({"updated": NOW - 400, "five": 5, "seven": 50})
    )
    transport = fake_transport(code=1)
    _, fields = render(
        {"session_id": "s1", "transcript_path": "",
         "model": {"display_name": "m"}},
        NOW, transport, cache_dir,
    )
    assert fields["five"] == "5%"
    assert fields["seven"] == "50%"
    assert len(transport.calls) == 1


def test_console_read_writes_cache(tmp_path):
    transport = fake_transport(
        pools=[
            {"type": "CREDIT_LIMIT", "consumed": 25, "remaining": 75},
            {"type": "CREDIT_LIMIT", "consumed": 50, "remaining": 50},
        ]
    )
    cache_dir = tmp_path / "cache"
    _, _ = render(
        {"session_id": "s1", "transcript_path": "",
         "model": {"display_name": "m"}},
        NOW, transport, cache_dir,
    )
    cached = json.loads((cache_dir / "console.json").read_text())
    assert cached == {"updated": NOW, "five": 25, "seven": 50}


def test_broken_payload_renders_degraded_line():
    line, fields = degraded_line(NOW)
    assert "unparsable payload" in line
    assert fields["fault"] == "unparsable payload"
    assert fields["five"] == "n/a"
    assert line.endswith("14:05 UTC")


def test_main_renders_degraded_on_broken_stdin(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr("sys.stdin", io.StringIO("{not json"))
    assert main(["--cache-dir", str(tmp_path / "c")]) == 0
    out = capsys.readouterr().out
    assert "unparsable payload" in out
    assert "n/a" in out


def test_main_json_output(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(FULL_PAYLOAD)))
    code = main(["--json", "--cache-dir", str(tmp_path / "c")])
    out = capsys.readouterr().out
    fields = json.loads(out)
    assert code == 0
    assert fields["model"] == "GLM-5.3-Flash"
    assert fields["five"] == "9%"
    assert fields["fault"] is None


def test_wrong_invocation_exits_2(capsys):
    with pytest.raises(SystemExit) as raised:
        main(["--bogus"])
    assert raised.value.code == 2
    assert "usage:" in capsys.readouterr().err


def test_load_payload_rejects_non_object():
    with pytest.raises(ValueError):
        load_payload(io.StringIO("[]"))


def test_pool_percentages_rejects_bad_json():
    assert pool_percentages("{nope") == (None, None)
    assert pool_percentages("[1, 2]") == (None, None)


def test_formatters_round_and_render_na():
    assert fmt_pct(None) == "n/a"
    assert fmt_pct(9.4) == "9%"
    assert fmt_millions(None) == "n/a"
    assert fmt_millions(606225) == "0.61M"
    assert fmt_cache_rate(None) == "n/a"
    assert fmt_cache_rate(0.98) == "98%"


def test_sums_are_incremental_against_the_real_rule(tmp_path):
    transcript = write_transcript(tmp_path, [usage_line(10, 20)])
    sums = read_transcript_sums(transcript, tmp_path / "sums.json", "s1")
    assert sums["in"] == 10
    assert sums["out"] == 20
    sums = read_transcript_sums(transcript, tmp_path / "sums.json", "s1")
    assert sums["in"] == 10  # the cached offset re-adds nothing


def test_default_transport_runs_and_survives_faults(tmp_path):
    code, stdout = default_transport(
        [sys.executable, "-c", "print('{}')"]
    )
    assert code == 0
    assert stdout.strip() == "{}"
    code, stdout = default_transport(["/nonexistent/interpreter"])
    assert code == 1
    assert stdout == ""


def test_cache_write_fault_is_ignored(tmp_path):
    target = tmp_path / "sums.json"
    target.mkdir()  # a directory at the cache path makes the rename fail
    write_json_cache(target, {"session_id": "s1"})
    assert target.is_dir()


def test_non_dict_and_flat_message_lines_are_skipped(tmp_path):
    transcript = write_transcript(
        tmp_path,
        ["[1, 2]", '{"message": "flat"}', '{"message": {"usage": "x"}}',
         usage_line(10, 20)]
    )
    sums = read_transcript_sums(transcript, tmp_path / "sums.json", "s1")
    assert sums["in"] == 10
    assert sums["rows"] == 1


def test_console_failure_with_no_cache_renders_na(tmp_path):
    transport = fake_transport(code=1)
    _, fields = render(
        {"session_id": "s1", "transcript_path": "",
         "model": {"display_name": "m"}},
        NOW, transport, tmp_path / "cache",
    )
    assert fields["five"] == "n/a"
    assert fields["seven"] == "n/a"


def test_corrupt_sums_cache_counts_as_no_cache(tmp_path):
    transcript = write_transcript(tmp_path, [usage_line(606225, 205336)])
    payload = {**FULL_PAYLOAD, "transcript_path": transcript}
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    (cache_dir / "sums.json").write_text("{not json", encoding="utf-8")
    _, fields = render(payload, NOW, fake_transport(), cache_dir)
    assert fields["in_millions"] == "0.61M"


def test_non_ascii_transcript_keeps_the_byte_offset(tmp_path):
    transcript = write_transcript(
        tmp_path, ["{\"type\":\"note\",\"text\":\"héllo wörld\"}"]
    )
    payload = {**FULL_PAYLOAD, "transcript_path": transcript}
    cache_dir = tmp_path / "cache"
    render(payload, NOW, fake_transport(), cache_dir)
    with open(transcript, "a", encoding="utf-8") as handle:
        handle.write(usage_line(606225, 205336) + "\n")
    _, fields = render(payload, NOW, fake_transport(), cache_dir)
    assert fields["in_millions"] == "0.61M"
    assert fields["out_millions"] == "0.21M"


def test_transcript_sums_carry_exact_integers():
    lines = [
        json.dumps({"message": {"usage": {"input_tokens": 3}}}),
        json.dumps({"message": {"usage": {"output_tokens": 7}}}),
        json.dumps({"message": {"usage": {}}}),
        json.dumps({"message": {"usage": {"input_tokens": 5,
                                          "output_tokens": 11,
                                          "cache_read_input_tokens": 13,
                                          "cache_creation_input_tokens": 17}}}),
    ]
    sums = transcript_sums("\n".join(lines))
    assert sums == {
        "rows": 4,
        "in": 8,
        "out": 18,
        "cache_read": 13,
        "cache_creation": 17,
    }


def test_transcript_sums_reject_non_dict_usage():
    sums = transcript_sums(json.dumps({"message": {"usage": "x"}}))
    assert sums["rows"] == 0
    assert sums["in"] == 0


def test_cache_write_leaves_no_temporary_files(tmp_path):
    target = tmp_path / "sums.json"
    write_json_cache(target, {"session_id": "s1"})
    assert target.is_file()
    assert list(tmp_path.glob("*.tmp")) == []


def test_usable_offset_boundaries():
    assert usable_offset(1, 10) is True
    assert usable_offset(10, 10) is True
    assert usable_offset(0, 10) is False
    assert usable_offset(11, 10) is False
    assert usable_offset("3", 10) is False
    assert usable_offset(3, 0) is False


def test_cache_totals_return_the_cached_totals_exactly():
    cache = {
        "session_id": "s1",
        "offset": 5,
        "rows": 2,
        "in": 10,
        "out": 20,
        "cache_read": 30,
        "cache_creation": 40,
    }
    assert cache_totals(cache, "s1", 100) == (
        5, 2,
        {"in": 10, "out": 20, "cache_read": 30, "cache_creation": 40},
    )


def test_cache_totals_reject_foreign_sessions_and_bad_offsets():
    empty = (0, 0, {"in": 0, "out": 0, "cache_read": 0, "cache_creation": 0})
    cache = {"session_id": "s1", "offset": 5, "rows": 2, "in": 10,
             "out": 20, "cache_read": 30, "cache_creation": 40}
    assert cache_totals(None, "s1", 100) == empty
    assert cache_totals(cache, "s2", 100) == empty
    assert cache_totals({**cache, "offset": 0}, "s1", 100) == empty
    assert cache_totals({**cache, "offset": 101}, "s1", 100) == empty
    assert cache_totals({**cache, "rows": None}, "s1", 100)[1] == 0
    assert cache_totals({**cache, "cache_read": None}, "s1", 100)[2]["cache_read"] == 0


def test_pool_rows_reject_strings_and_zero_windows(tmp_path):
    transport = fake_transport(
        pools=[
            {"type": "CREDIT_LIMIT", "consumed": "5", "remaining": 5},
            {"type": "CREDIT_LIMIT", "consumed": 0, "remaining": 1},
        ]
    )
    _, fields = render(
        {"session_id": "s1", "transcript_path": "",
         "model": {"display_name": "m"}},
        NOW, transport, tmp_path / "cache",
    )
    assert fields["five"] == "n/a"
    assert fields["seven"] == "0%"


def test_pool_rows_skip_non_dict_entries(tmp_path):
    transport = fake_transport(
        pools=["row", {"type": "CREDIT_LIMIT", "consumed": 1, "remaining": 3}]
    )
    _, fields = render(
        {"session_id": "s1", "transcript_path": "",
         "model": {"display_name": "m"}},
        NOW, transport, tmp_path / "cache",
    )
    assert fields["five"] == "n/a"
    assert fields["seven"] == "n/a"


def test_console_cache_expires_at_exact_ttl(tmp_path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    (cache_dir / "console.json").write_text(
        json.dumps({"updated": NOW - 300, "five": 5, "seven": 50})
    )
    transport = fake_transport(
        pools=[
            {"type": "CREDIT_LIMIT", "consumed": 1, "remaining": 3},
            {"type": "CREDIT_LIMIT", "consumed": 1, "remaining": 1},
        ]
    )
    _, fields = render(
        {"session_id": "s1", "transcript_path": "",
         "model": {"display_name": "m"}},
        NOW, transport, cache_dir,
    )
    assert fields["five"] == "25%"
    assert len(transport.calls) == 1


def test_cache_offset_covers_the_whole_file(tmp_path):
    transcript = write_transcript(tmp_path, [usage_line(10, 20)])
    payload = {**FULL_PAYLOAD, "transcript_path": transcript}
    render(payload, NOW, fake_transport(), tmp_path / "cache")
    record = json.loads((tmp_path / "cache" / "sums.json").read_text())
    assert record["offset"] == Path(transcript).stat().st_size


def test_main_honors_the_cache_dir(monkeypatch, capsys, tmp_path):
    transcript = write_transcript(tmp_path, [usage_line(10, 20)])
    payload = {**FULL_PAYLOAD, "transcript_path": transcript}
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
    cache_dir = tmp_path / "c"
    code = main(["--json", "--cache-dir", str(cache_dir)])
    assert code == 0
    assert (cache_dir / "sums.json").is_file()


def test_cache_write_lands_in_an_existing_directory(tmp_path):
    transcript = write_transcript(tmp_path, [usage_line(10, 20)])
    payload = {**FULL_PAYLOAD, "transcript_path": transcript}
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    render(payload, NOW, fake_transport(), cache_dir)
    assert (cache_dir / "sums.json").is_file()


def test_cache_write_creates_missing_parent_directories(tmp_path):
    transcript = write_transcript(tmp_path, [usage_line(10, 20)])
    payload = {**FULL_PAYLOAD, "transcript_path": transcript}
    cache_dir = tmp_path / "a" / "b"
    render(payload, NOW, fake_transport(), cache_dir)
    assert (cache_dir / "sums.json").is_file()
