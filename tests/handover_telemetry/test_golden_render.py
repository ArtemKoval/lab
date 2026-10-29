"""Golden tests for the renderers: the fixture session renders to the
pinned markdown and JSON text, and empty metrics render to the pinned
markdown. Any drift in text, order, or number format fails a test."""

from golden_data import GOLDEN_EMPTY_MD, GOLDEN_JSON, GOLDEN_MD, render_reports


def test_fixture_session_renders_the_pinned_markdown():
    md, _ = render_reports()
    assert md == GOLDEN_MD


def test_fixture_session_renders_the_pinned_json():
    _, js = render_reports()
    assert js == GOLDEN_JSON


def test_empty_metrics_render_the_pinned_markdown():
    from handover_telemetry import metrics, redact, render

    md = render.render_markdown(metrics.TaskMetrics(), {}, redact.default_redactor())
    assert md == GOLDEN_EMPTY_MD
