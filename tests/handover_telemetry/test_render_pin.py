"""Pinned tests for the render edges: the value formats for the DORA
proxies and the cache rate, the sorted redaction counts, and the
missing-counts scrubber."""

from handover_telemetry import metrics, render


class _StubScrubber:
    """A scrubber with preset counts and identity scrubbing."""

    def __init__(self, counts):
        self.counts = counts

    def scrub(self, text):
        return text


def _metrics() -> metrics.TaskMetrics:
    return metrics.TaskMetrics()


def test_dora_values_render_in_the_pinned_formats():
    got = _metrics()
    got.dora = {
        "lead_time_ms": 1500.6,
        "deployment_frequency": None,
        "change_fail_signals": 3,
        "recovery_ms": 2500.0,
        "rework_rate": 0.25,
    }
    md = render.render_markdown(got, {}, _StubScrubber({}))
    assert "- change lead time: 1501 ms" in md
    assert "- deployment frequency: n/a (no per-task proxy)" in md
    assert "- change fail signals: 3" in md
    assert "- recovery time: 2500 ms" in md
    assert "- rework rate: 25%" in md


def test_rework_rate_two_thirds_renders_67_percent():
    got = _metrics()
    got.dora = {
        "lead_time_ms": None,
        "deployment_frequency": None,
        "change_fail_signals": None,
        "recovery_ms": None,
        "rework_rate": 2 / 3,
    }
    md = render.render_markdown(got, {}, _StubScrubber({}))
    assert "- rework rate: 67%" in md
    assert "- change fail signals: n/a" in md
    assert "- change lead time: n/a ms" in md
    assert "- recovery time: n/a ms" in md


def test_cache_hit_rate_renders_as_a_percent():
    got = _metrics()
    got.cache_hit_rate = 0.256
    md = render.render_markdown(got, {}, _StubScrubber({}))
    assert "- cache hit rate: 26%" in md


def test_redaction_counts_render_sorted():
    md = render.render_markdown(_metrics(), {}, _StubScrubber({"token": 2, "email": 1}))
    assert "### Redaction\n\n- email: 1\n- token: 2\n" in md


def test_redaction_without_a_counts_attr_renders_nothing_needed():
    class Bare:
        pass

    md = render.render_markdown(_metrics(), {}, Bare())
    assert "- nothing needed redaction" in md


def test_machine_section_renders_none_as_na():
    md = render.render_markdown(_metrics(), {"kernel": None, "arch": "x86_64"}, _StubScrubber({}))
    assert "- kernel: n/a" in md
    assert "- arch: x86_64" in md


def test_requested_models_render_as_counts():
    got = _metrics()
    got.requested_models = {"b-model": 2, "a-model": 1}
    md = render.render_markdown(got, {}, _StubScrubber({}))
    assert "- requested models: b-model x2, a-model x1" in md


def test_empty_decision_summary_renders_the_dash():
    got = _metrics()
    got.decisions = [
        {"agent": "primary", "tool": "ExitPlanMode", "summary": "", "ts": None}
    ]
    md = render.render_markdown(got, {}, _StubScrubber({}))
    assert "- [n/a] primary via ExitPlanMode: -" in md


def test_friction_retries_render_the_counted_value(tmp_path):
    from handover_telemetry import pricing, transcript

    lines = [
        '{"type": "assistant", "sessionId": "s1", "requestId": "r1", "timestamp": "2026-01-01T00:00:01Z",'
        ' "message": {"id": "m1", "model": "m", "usage": {}, "content": []}}',
        '{"type": "assistant", "sessionId": "s1", "requestId": "r1", "timestamp": "2026-01-01T00:00:02Z",'
        ' "message": {"id": "m2", "model": "m", "usage": {}, "content": []}}',
    ]
    path = tmp_path / "retry.jsonl"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    session = transcript.parse_session(path)
    got = metrics.compute(session, price_table=pricing.load_prices())
    md = render.render_markdown(got, {}, _StubScrubber({}))
    assert "- retries: 1" in md
