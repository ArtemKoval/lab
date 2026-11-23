"""The pure id-series helper: prefix retention, the next number, the
evaluation-copy exclusion, and the empty fallback."""

from backend.case_ids import FALLBACK, next_case_id


def test_the_seed_continues_at_the_next_number():
    assert next_case_id(["LN-5001", "LN-5002", "LN-5003"]) == "LN-5004"


def test_a_higher_seed_moves_the_series():
    ids = [
        "LN-5001",
        "LN-5002",
        "LN-5003",
        "LN-5004",
        "LN-5005",
        "LN-5006",
        "LN-5007",
        "LN-5008",
    ]
    assert next_case_id(ids) == "LN-5009"


def test_an_evaluation_copy_sits_out_of_the_scan():
    ids = ["LN-5003", "LN-5003-E7"]
    assert next_case_id(ids) == "LN-5004"


def test_the_prefix_of_the_highest_id_carries():
    ids = ["LN-5006", "XY-9"]
    assert next_case_id(ids) == "XY-10"


def test_an_empty_database_starts_the_fallback():
    assert next_case_id([]) == FALLBACK


def test_ids_outside_the_series_shape_sit_out():
    assert next_case_id(["not-a-series", "", "LN-5002"]) == "LN-5003"
