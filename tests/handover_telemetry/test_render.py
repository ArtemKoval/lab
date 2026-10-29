"""Tests for the markdown and JSON renderers: section presence,
honest gaps, scrubbed strings, and the GenAI field names."""

from pathlib import Path

import json as jsonlib

import pytest
from handover_telemetry import logparse, machine, metrics, pricing, redact, render, transcript

FIXTURES = Path(__file__).parent / "fixtures"
SESSION_DIR = FIXTURES / "session"
HOOK_LOG = FIXTURES / "hook" / "sess-1.jsonl"
TMP_ROOT = Path(__file__).parent.parent.parent


@pytest.fixture()
def output(tmp_path) -> tuple[str, str]:
    main = tmp_path / "main.jsonl"
    main.write_text((SESSION_DIR / "main.jsonl").read_text(encoding="utf-8"), encoding="utf-8")
    sub = tmp_path / "sess-1" / "subagents"
    sub.mkdir(parents=True)
    (sub / "agent-42.jsonl").write_text(
        (SESSION_DIR / "sess-1" / "subagents" / "agent-42.jsonl").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    session = transcript.parse_session(main)
    logparse.apply_hook_durations(session.primary.tool_calls, HOOK_LOG)
    scrubber = redact.default_redactor()
    got = metrics.compute(session, price_table=pricing.load_prices(), hook_log=HOOK_LOG)
    host = machine.collect(repo=tmp_path)
    host = {k: "stub-" + k for k in host}
    host["disk_total_gb"] = 500.0
    md = render.render_markdown(got, host, scrubber)
    js = render.render_json(got, host, scrubber)
    return md, js


def test_markdown_has_every_section(output):
    md, _ = output
    for head in (
        "### Run",
        "### Funnel",
        "### Models and tokens",
        "### Cost",
        "### Pipeline proxies",
        "### Decisions",
        "### Friction",
        "### Machine",
        "### Redaction",
    ):
        assert head in md


def test_markdown_marks_missing_proxies_as_na(output):
    md, js = output
    assert "n/a" in md
    assert jsonlib.loads(js)["dora"]["deployment_frequency"] is None


def test_markdown_carries_funnel_row_with_hook_duration(output):
    md, _ = output
    assert "Bash" in md
    assert "1960" in md


def test_markdown_carries_cost_rows_and_total(output):
    md, _ = output
    assert "glm-5.3-flash" in md
    assert "$" in md
    assert "source date" in md


def test_markdown_lists_decisions(output):
    md, _ = output
    assert "AskUserQuestion" in md
    assert "adversarial-reviewer" in md


def test_planted_secret_never_reaches_render(output):
    md, js = output
    assert "sk-live-synthetic" not in md
    assert "sk-live-synthetic" not in js


def test_scrubbed_argument_reaches_render(tmp_path):
    main = tmp_path / "main.jsonl"
    main.write_text((SESSION_DIR / "main.jsonl").read_text(encoding="utf-8"), encoding="utf-8")
    session = transcript.parse_session(main)
    for call in session.primary.tool_calls:
        if call.name == "Agent":
            call.input["description"] = "review with key sk-live-synthetic000key00000000"
    got = metrics.compute(session, price_table=pricing.load_prices())
    scrubber = redact.default_redactor()
    md = render.render_markdown(got, {}, scrubber)
    assert "sk-live-synthetic000key00000000" not in md
    assert "[REDACTED:token]" in md


def test_transcript_names_render_redacted_in_both_outputs(tmp_path):
    main = tmp_path / "main.jsonl"
    main.write_text((SESSION_DIR / "main.jsonl").read_text(encoding="utf-8"), encoding="utf-8")
    session = transcript.parse_session(main)
    secret = "gho_AAAABBBBCCCCDDDDEEEEFFFFGGGGHHH1"
    session.primary.tool_calls[0].name = secret
    session.primary.turns[0].model = secret
    session.sidechains = [transcript.AgentRun(agent_id=secret)]
    got = metrics.compute(session, price_table=pricing.load_prices())
    scrubber = redact.default_redactor()
    md = render.render_markdown(got, {}, scrubber)
    js = render.render_json(got, {}, scrubber)
    assert secret not in md
    assert "[REDACTED:token]" in md
    assert secret not in js
    assert "[REDACTED:token]" in js


def test_json_uses_genai_field_names(output):
    _, js = output
    data = jsonlib.loads(js)
    model_rows = data["models"]
    row = model_rows["glm-5.3-flash"]
    assert "gen_ai.usage.input_tokens" in row
    assert "gen_ai.usage.output_tokens" in row
    assert row["gen_ai.usage.output_tokens"] == 350


def test_json_labels_the_served_model_as_response_model(output):
    _, js = output
    data = jsonlib.loads(js)
    row = data["models"]["glm-5.3-flash"]
    assert row["gen_ai.response.model"] == "glm-5.3-flash"
    assert "gen_ai.request.model" not in row


def test_cost_section_renders_the_per_agent_split(output):
    md, js = output
    assert "Cost split per agent" in md
    assert "| Agent | USD |" in md
    assert "| primary | $0.0050 |" in md
    assert "| agent-42 | $0.0012 |" in md
    data = jsonlib.loads(js)
    assert data["cost"]["by_agent"]["primary"] == pytest.approx(0.005012)
    assert data["cost"]["by_agent"]["agent-42"] == pytest.approx(0.001228)


def test_json_carries_fingerprint_and_requested(output):
    _, js = output
    data = jsonlib.loads(js)
    assert data["fingerprint"]["session_id"] == "sess-1"
    assert data["requested_models"]["claude-opus-5-5"] == 1


def test_render_tolerates_empty_metrics():
    empty = metrics.TaskMetrics()
    scrubber = redact.default_redactor()
    md = render.render_markdown(empty, {}, scrubber)
    assert "### Funnel" in md
    assert "n/a" in md


def test_unknown_model_renders_unknown_row(tmp_path):
    main = tmp_path / "main.jsonl"
    main.write_text((SESSION_DIR / "main.jsonl").read_text(encoding="utf-8"), encoding="utf-8")
    session = transcript.parse_session(main)
    session.primary.turns.append(
        transcript.Turn("mx", "mystery-model", None, {"input_tokens": 5, "output_tokens": 5}, None, None, None, None)
    )
    got = metrics.compute(session, price_table=pricing.load_prices())
    md = render.render_markdown(got, {}, redact.default_redactor())
    assert "mystery-model | unknown (no rate in the table)" in md
