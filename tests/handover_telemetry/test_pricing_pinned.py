"""Pinned tests for the price table: the usage split, the alias depth
and its errors, the million-token divisor, the sorted model list, and
the loader messages."""

import json
from pathlib import Path

import pytest

from handover_telemetry import pricing


def _table(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "table.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_tokens_from_usage_prefers_the_5m_tier():
    usage = {
        "input_tokens": 10,
        "output_tokens": 20,
        "cache_read_input_tokens": 30,
        "cache_creation_input_tokens": 40,
        "cache_creation": {
            "ephemeral_5m_input_tokens": 9,
            "ephemeral_1h_input_tokens": 15,
        },
    }
    assert pricing._tokens_from_usage(usage) == {
        "input": 10,
        "output": 20,
        "cache_read": 30,
        "cache_write_5m": 9,
        "cache_write_1h": 15,
    }


def test_tokens_from_usage_derives_the_5m_tier():
    usage = {
        "input_tokens": 10,
        "output_tokens": 20,
        "cache_read_input_tokens": 30,
        "cache_creation_input_tokens": 40,
        "cache_creation": {"ephemeral_1h_input_tokens": 15},
    }
    assert pricing._tokens_from_usage(usage)["cache_write_5m"] == 25


def test_tokens_from_usage_derives_the_5m_tier_without_tiers():
    usage = {"cache_creation_input_tokens": 40}
    assert pricing._tokens_from_usage(usage) == {
        "input": 0,
        "output": 0,
        "cache_read": 0,
        "cache_write_5m": 40,
        "cache_write_1h": 0,
    }


def _chain_table(tmp_path: Path, depth: int) -> Path:
    rates = {}
    for index in range(depth - 1):
        rates[f"deep{index}"] = {"alias_of": f"deep{index + 1}"}
    rates[f"deep{depth - 1}"] = {"input": 2.0}
    return _table(tmp_path, {"source_date": "2026-01-01", "rates_per_mtok": rates})


def test_alias_chain_resolves_within_the_depth_limit(tmp_path):
    table = pricing.load_prices(_chain_table(tmp_path, 9))
    assert table.rate_for("deep0", "input") == 2.0


def test_alias_chain_too_deep_raises(tmp_path):
    table = pricing.load_prices(_chain_table(tmp_path, 10))
    with pytest.raises(pricing.CostError) as exc:
        table.rate_for("deep0", "input")
    assert str(exc.value) == "alias chain too deep at deep0"


def test_alias_loop_raises(tmp_path):
    table = pricing.load_prices(
        _table(
            tmp_path,
            {
                "source_date": "2026-01-01",
                "rates_per_mtok": {
                    "loop-a": {"alias_of": "loop-b"},
                    "loop-b": {"alias_of": "loop-a"},
                },
            },
        )
    )
    with pytest.raises(pricing.CostError) as exc:
        table.rate_for("loop-a", "input")
    assert str(exc.value) == "alias loop at loop-a"


def test_cost_for_divides_by_one_million(tmp_path):
    table = pricing.load_prices(
        _table(
            tmp_path,
            {
                "source_date": "2026-01-01",
                "rates_per_mtok": {"m": {"input": 2.0, "output": 3.0}},
            },
        )
    )
    got = table.cost_for(
        "m", {"input": 500000, "output": 500000, "cache_read": 1000000}
    )
    assert got == pytest.approx(2.7, rel=1e-9)


def test_cost_without_an_input_rate_is_none(tmp_path):
    table = pricing.load_prices(
        _table(
            tmp_path,
            {"source_date": "2026-01-01", "rates_per_mtok": {"m": {}}},
        )
    )
    assert table.cost_for("m", {"input": 10}) is None


def test_models_are_sorted(tmp_path):
    table = pricing.load_prices(
        _table(
            tmp_path,
            {
                "source_date": "2026-01-01",
                "rates_per_mtok": {"zmodel": {"input": 1.0}, "amodel": {"input": 1.0}},
            },
        )
    )
    assert table.models == ["amodel", "zmodel"]


def test_load_prices_pins_the_table_fields(tmp_path):
    path = _table(
        tmp_path,
        {"source_date": "2026-01-01", "rates_per_mtok": {"m": {"input": 1.0}}},
    )
    table = pricing.load_prices(path)
    assert table.source_date == "2026-01-01"
    assert table.rates == {"m": {"input": 1.0}}


def test_load_prices_defaults_the_source_date(tmp_path):
    path = _table(tmp_path, {"rates_per_mtok": {"m": {"input": 1.0}}})
    assert pricing.load_prices(path).source_date == "unknown"


def test_load_prices_missing_file_message_is_exact(tmp_path):
    absent = tmp_path / "none.json"
    with pytest.raises(pricing.CostError) as exc:
        pricing.load_prices(absent)
    assert str(exc.value) == (
        f"cannot read price table {absent}: "
        f"[Errno 2] No such file or directory: '{absent}'"
    )


def test_load_prices_corrupt_file_message_is_exact(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("]", encoding="utf-8")
    with pytest.raises(pricing.CostError) as exc:
        pricing.load_prices(path)
    assert str(exc.value) == (
        f"cannot read price table {path}: "
        "Expecting value: line 1 column 1 (char 0)"
    )


def test_load_prices_without_rates_message_is_exact(tmp_path):
    path = _table(tmp_path, {"source_date": "2026-01-01"})
    with pytest.raises(pricing.CostError) as exc:
        pricing.load_prices(path)
    assert str(exc.value) == f"price table {path} carries no rates_per_mtok map"


def test_load_prices_rejects_a_nondict_rates_map(tmp_path):
    path = _table(tmp_path, {"rates_per_mtok": ["m"]})
    with pytest.raises(pricing.CostError):
        pricing.load_prices(path)


def test_default_table_path_sits_beside_the_module():
    assert pricing.default_table_path() == (
        Path(pricing.__file__).resolve().parent / "pricing.json"
    )
