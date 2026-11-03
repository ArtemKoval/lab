"""Tests for the pure window math and the block-set decision.

Every test pins one behavior from the peak-hours-gate spec. The clock
enters as a parameter, so no test waits on a real clock.
"""

from datetime import datetime, timedelta, timezone

from peak_hours_gate import core

UTC = timezone.utc
JST = timezone(timedelta(hours=9))
SGT = timezone(timedelta(hours=8))


def _utc(text):
    return datetime.fromisoformat(text).replace(tzinfo=UTC)


def test_window_opens_at_1400_sgt_monday():
    assert core.is_peak(_utc("2026-11-02T06:00:00")) is True


def test_last_minute_belongs_to_window():
    assert core.is_peak(_utc("2026-11-06T09:59:00")) is True


def test_window_closes_at_1800_sgt_friday():
    assert core.is_peak(_utc("2026-11-06T10:00:00")) is False


def test_minute_before_window_stays_open():
    assert core.is_peak(_utc("2026-11-02T05:59:00")) is False


def test_weekend_stays_open():
    assert core.is_peak(_utc("2026-11-07T07:00:00")) is False


def test_friday_evening_utc_is_saturday_in_sgt():
    # 20:00 UTC Friday is 04:00 SGT Saturday. The SGT weekday decides.
    assert core.is_peak(_utc("2026-11-06T20:00:00")) is False


def test_zone_does_not_matter():
    same_instant_utc = datetime(2026, 11, 2, 6, 0, tzinfo=UTC)
    same_instant_jst = datetime(2026, 11, 2, 15, 0, tzinfo=JST)
    assert core.is_peak(same_instant_utc) == core.is_peak(same_instant_jst)


def test_next_open_names_today_before_the_window():
    # 13:00 SGT Monday: the window opens later the same day.
    line = core.describe(_utc("2026-11-02T05:00:00"))
    assert "outside the peak window" in line
    assert "Mon 14:00" in line


def test_next_open_names_tomorrow_after_the_window():
    # 19:00 SGT Tuesday: the next open is Wednesday.
    line = core.describe(_utc("2026-11-03T11:00:00"))
    assert "Wed 14:00" in line


def test_next_open_names_tomorrow_at_the_close_hour():
    # 18:00 SGT Wednesday is out of the window: the next open is Thursday.
    line = core.describe(_utc("2026-11-04T10:00:00"))
    assert "outside the peak window" in line
    assert "Thu 14:00" in line


def test_next_open_walks_off_the_weekend():
    # 15:00 SGT Saturday: the next open is Monday.
    line = core.describe(_utc("2026-11-07T07:00:00"))
    assert "Mon 14:00" in line


def test_close_boundary_names_today_in_the_window():
    # 15:00 SGT Tuesday: the window closes the same day.
    line = core.describe(_utc("2026-11-03T07:00:00"))
    assert "in the peak window" in line
    assert "Tue 18:00" in line


def test_close_boundary_names_friday_in_the_window():
    line = core.describe(_utc("2026-11-06T07:00:00"))
    assert "Fri 18:00" in line


def test_sgt_maps_utc_to_wall_time():
    sgt_time = core.sgt(_utc("2026-11-02T06:00:00"))
    assert (sgt_time.hour, sgt_time.minute) == (14, 0)
    assert sgt_time.weekday() == 0


def test_sgt_rolls_the_date():
    # 20:00 UTC Tuesday is 04:00 SGT Wednesday.
    sgt_time = core.sgt(_utc("2026-11-03T20:00:00"))
    assert (sgt_time.hour, sgt_time.minute) == (4, 0)
    assert sgt_time.weekday() == 2


IN_WINDOW = _utc("2026-11-03T07:00:00")  # 15:00 SGT Tuesday
OUT_WINDOW = _utc("2026-11-03T11:00:00")  # 19:00 SGT Tuesday


def _event(name, command=None):
    event = {"tool_name": name}
    if command is not None:
        event["tool_input"] = {"command": command}
    return event


def test_task_denies_in_window():
    code, message = core.decide(_event("Task"), IN_WINDOW, None)
    assert code == 2
    assert message


def test_block_set_tools_deny_in_window():
    for name in ("Agent", "Workflow", "WebSearch", "WebFetch"):
        code, _ = core.decide(_event(name), IN_WINDOW, None)
        assert code == 2, name


def test_mcp_prefix_denies_in_window():
    code, _ = core.decide(_event("mcp__zai-routing-audit__usage_report"), IN_WINDOW, None)
    assert code == 2


def test_bash_live_paths_deny_in_window():
    for word in ("optimize", "certify", "evals", "nightly"):
        command = f"python -m dspy_gate {word} add-x"
        code, _ = core.decide(_event("Bash", command), IN_WINDOW, None)
        assert code == 2, word


def test_bash_match_tolerates_spacing_and_dash_form():
    spaced = "python  -m  dspy_gate  optimize"
    dashed = "dspy-gate certify add-x"
    assert core.decide(_event("Bash", spaced), IN_WINDOW, None)[0] == 2
    assert core.decide(_event("Bash", dashed), IN_WINDOW, None)[0] == 2


def test_bash_local_subcommand_allows_in_window():
    code, _ = core.decide(_event("Bash", "python -m dspy_gate lint add-x"), IN_WINDOW, None)
    assert code == 0


def test_plain_bash_allows_in_window():
    code, _ = core.decide(_event("Bash", "git status"), IN_WINDOW, None)
    assert code == 0


def test_write_allows_in_window():
    code, _ = core.decide(_event("Write"), IN_WINDOW, None)
    assert code == 0


def test_send_message_allows_in_window():
    code, _ = core.decide(_event("SendMessage"), IN_WINDOW, None)
    assert code == 0


def test_task_allows_outside_window():
    code, message = core.decide(_event("Task"), OUT_WINDOW, None)
    assert code == 0
    assert message == ""


def test_task_allows_at_the_close_hour():
    # 18:00 SGT sharp: the end is exclusive, so the call passes.
    code, message = core.decide(_event("Task"), _utc("2026-11-03T10:00:00"), None)
    assert code == 0
    assert message == ""


def test_bash_with_non_dict_tool_input_allows():
    event = {"tool_name": "Bash", "tool_input": ["not", "a", "dict"]}
    code, _ = core.decide(event, IN_WINDOW, None)
    assert code == 0


def test_override_one_allows_in_window():
    code, _ = core.decide(_event("Task"), IN_WINDOW, "1")
    assert code == 0


def test_other_override_values_do_not_bypass():
    for value in ("0", "true", "yes", ""):
        code, _ = core.decide(_event("Task"), IN_WINDOW, value)
        assert code == 2, repr(value)


def test_deny_message_names_window_and_override():
    _, message = core.decide(_event("Task"), IN_WINDOW, None)
    assert "14:00" in message
    assert "18:00" in message
    assert "ZAI_PEAK_HOURS_OVERRIDE" in message


def test_non_dict_event_allows():
    code, message = core.decide("not a dict", IN_WINDOW, None)
    assert code == 0
    assert message == ""


def test_missing_tool_name_allows():
    code, _ = core.decide({}, IN_WINDOW, None)
    assert code == 0


def test_bash_without_command_allows():
    code, _ = core.decide({"tool_name": "Bash", "tool_input": {}}, IN_WINDOW, None)
    assert code == 0


def test_block_set_stays_data():
    assert core.BLOCKED_TOOLS == frozenset(
        {"Task", "Agent", "Workflow", "WebSearch", "WebFetch"}
    )
    assert core.MCP_PREFIX == "mcp__"
    assert set(core.BASH_LIVE_WORDS) == {"optimize", "certify", "evals", "nightly"}
