"""Pinned tests for the high-entropy pass: hit counting, the exact
category mark, the hex exemption, and the exact entropy boundary."""

from handover_telemetry import redact

SECRET_A = "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6"
SECRET_B = "Z9y8X7w6V5u4T3s2R1q0P0o9N8m7K6l5"
BOUNDARY = "wwwwwwwwxxxxxxxx1Ghijklmnopqrstu"
HEXISH = "a1b2c3d4" * 4


def test_two_secrets_in_one_string_count_and_replace_twice():
    scrubber = redact.default_redactor()
    out = scrubber.scrub(f"lead {SECRET_A} mid {SECRET_B} tail")
    assert out == "lead [REDACTED:high_entropy] mid [REDACTED:high_entropy] tail"
    assert scrubber.counts["high_entropy"] == 2


def test_hits_accumulate_across_scrubs():
    scrubber = redact.default_redactor()
    scrubber.scrub(f"lead {SECRET_A} tail")
    scrubber.scrub(f"lead {SECRET_B} tail")
    assert scrubber.counts["high_entropy"] == 2


def test_hex_only_blob_is_kept():
    scrubber = redact.default_redactor()
    out = scrubber.scrub(f"commit {HEXISH} end")
    assert out == f"commit {HEXISH} end"
    assert scrubber.counts["high_entropy"] == 0


def test_entropy_at_the_boundary_is_a_secret():
    scrubber = redact.default_redactor()
    out = scrubber.scrub(f"lead {BOUNDARY} tail")
    assert out == "lead [REDACTED:high_entropy] tail"
    assert scrubber.counts["high_entropy"] == 1


def test_text_without_candidates_passes_through():
    scrubber = redact.default_redactor()
    assert scrubber.scrub("plain words only") == "plain words only"
    assert scrubber.counts == {}
