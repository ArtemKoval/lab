"""The scoreboard's award read: the pack's metric, with the award float as
the fallback the removal stage drops."""

from backend.scoreboard import scored_award


def a_row(**changes):
    row = {"payload": None, "award": 400.0}
    return row | changes


def test_the_award_comes_from_the_pack_metric():
    assert scored_award(a_row(payload={"award": 420.0})) == 420.0


def test_a_copy_with_no_payload_uses_the_award_float():
    assert scored_award(a_row()) == 400.0
