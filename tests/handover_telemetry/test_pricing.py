"""Tests for the price table loader: exact ids, aliases, multiplier
fallbacks, the unknown mark, and the cost math. One behaviour each."""

import json

import pytest
from handover_telemetry.pricing import CostError, PriceTable, default_table_path, load_prices

GLM = "glm-5.3"


@pytest.fixture()
def table() -> PriceTable:
    return load_prices()


def test_default_table_path_resolves():
    path = default_table_path()
    assert path.name == "pricing.json"
    assert path.exists()


def test_load_prices_reads_the_packaged_file(table):
    assert table.source_date == "2026-10-29"
    assert GLM in table.models


def test_exact_model_has_input_and_output_rates(table):
    assert table.rate_for(GLM, "input") == 1.40
    assert table.rate_for(GLM, "output") == 4.40


def test_explicit_cache_read_rate_wins(table):
    assert table.rate_for(GLM, "cache_read") == 0.26


def test_alias_resolves_to_its_target(table):
    assert table.rate_for("glm-5.3-flash", "input") == 1.40
    assert table.rate_for("glm-5.3-flash", "cache_read") == 0.26


def test_missing_cache_rates_fall_back_to_multipliers(table):
    assert table.rate_for("claude-opus-5", "cache_read") == pytest.approx(0.5)
    assert table.rate_for("claude-opus-5", "cache_write_5m") == pytest.approx(6.25)
    assert table.rate_for("claude-opus-5", "cache_write_1h") == pytest.approx(10.0)


def test_unknown_model_has_no_input_rate(table):
    assert table.rate_for("totally-unknown-model", "input") is None


def test_known_model_has_no_output_fallback_gaps(table):
    for model in table.models:
        assert table.rate_for(model, "input") is not None


def test_cost_sums_all_five_token_kinds(table):
    tokens = {
        "input": 1000,
        "output": 500,
        "cache_read": 10000,
        "cache_write_5m": 2000,
        "cache_write_1h": 0,
    }
    cost = table.cost_for(GLM, tokens)
    expected = (1000 * 1.40 + 500 * 4.40 + 10000 * 0.26 + 2000 * 1.40 * 1.25) / 1e6
    assert cost == pytest.approx(expected)


def test_cost_of_unknown_model_is_none(table):
    assert table.cost_for("totally-unknown-model", {"input": 10, "output": 10}) is None


def test_missing_token_kinds_cost_zero(table):
    assert table.cost_for(GLM, {"input": 0, "output": 0}) == 0.0


def test_unknown_token_kind_is_skipped(table):
    assert table.cost_for(GLM, {"input": 0, "output": 0, "bogus_kind": 5}) == 0.0


def test_usage_block_maps_to_cost(table):
    usage = {
        "input_tokens": 1000,
        "output_tokens": 500,
        "cache_read_input_tokens": 10000,
        "cache_creation_input_tokens": 2000,
    }
    cost = table.cost_for_usage(GLM, usage)
    expected = (1000 * 1.40 + 500 * 4.40 + 10000 * 0.26 + 2000 * 1.40 * 1.25) / 1e6
    assert cost == pytest.approx(expected)


def test_usage_block_with_tier_split_costs_the_1h_tier_higher(table):
    flat = {"input_tokens": 0, "output_tokens": 0, "cache_creation_input_tokens": 1000}
    split = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_creation_input_tokens": 1000,
        "cache_creation": {"ephemeral_5m_input_tokens": 0, "ephemeral_1h_input_tokens": 1000},
    }
    assert table.cost_for_usage(GLM, split) > table.cost_for_usage(GLM, flat)


def test_corrupt_table_file_raises_cost_error(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(CostError):
        load_prices(bad)


def test_table_file_missing_rates_key_raises_cost_error(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"source_date": "2026-01-01"}), encoding="utf-8")
    with pytest.raises(CostError):
        load_prices(bad)


def test_alias_chain_depth_is_bounded(tmp_path):
    deep = tmp_path / "deep.json"
    rates = {f"m{i}": {"alias_of": f"m{i+1}", "source": "test"} for i in range(12)}
    deep.write_text(json.dumps({"source_date": "2026-01-01", "rates_per_mtok": rates}), encoding="utf-8")
    with pytest.raises(CostError):
        load_prices(deep).rate_for("m0", "input")


def test_alias_cycle_raises_cost_error(tmp_path):
    cycle = tmp_path / "cycle.json"
    rates = {"a": {"alias_of": "b", "source": "test"}, "b": {"alias_of": "a", "source": "test"}}
    cycle.write_text(json.dumps({"source_date": "2026-01-01", "rates_per_mtok": rates}), encoding="utf-8")
    with pytest.raises(CostError):
        load_prices(cycle).rate_for("a", "input")


def test_entry_without_input_rate_has_no_rates(tmp_path):
    odd = tmp_path / "odd.json"
    rates = {"weird": {"output": 5.0, "source": "test"}}
    odd.write_text(json.dumps({"source_date": "2026-01-01", "rates_per_mtok": rates}), encoding="utf-8")
    assert load_prices(odd).rate_for("weird", "cache_read") is None
