"""The versioned price table for the cost estimates.

`pricing.json` ships beside this module and carries a source date plus
per-model rates in USD per million tokens. A missing cache rate falls
back to the Anthropic multipliers on the input rate. A model with no
entry carries no input rate, and the report renders its cost as
unknown. The loader never touches the network.
"""

import json
from pathlib import Path

_INPUT = "input"
_OUTPUT = "output"
_CACHE_READ = "cache_read"
_CACHE_WRITE_5M = "cache_write_5m"
_CACHE_WRITE_1H = "cache_write_1h"

_FALLBACK_MULTIPLIER = {
    _CACHE_READ: 0.1,
    _CACHE_WRITE_5M: 1.25,
    _CACHE_WRITE_1H: 2.0,
}

_MAX_ALIAS_DEPTH = 8


class CostError(Exception):
    """The price table file is missing, corrupt, or loops an alias."""


def default_table_path() -> Path:
    return Path(__file__).resolve().parent / "pricing.json"


class PriceTable:
    """Rates for one table version. All lookups stay offline."""

    def __init__(self, source_date: str, rates: dict[str, dict]) -> None:
        self.source_date = source_date
        self.rates = rates

    @property
    def models(self) -> list[str]:
        return sorted(self.rates)

    def _entry_for(self, model: str) -> dict | None:
        seen: set[str] = set()
        current = model
        for _ in range(_MAX_ALIAS_DEPTH + 1):
            if current in seen:
                raise CostError(f"alias loop at {current}")
            seen.add(current)
            entry = self.rates.get(current)
            if entry is None:
                return None
            target = entry.get("alias_of")
            if not target:
                return entry
            current = target
        raise CostError(f"alias chain too deep at {model}")

    def rate_for(self, model: str, kind: str) -> float | None:
        entry = self._entry_for(model)
        if entry is None or entry.get(kind) is None:
            base = entry.get(_INPUT) if entry else None
            fallback = _FALLBACK_MULTIPLIER.get(kind)
            if base is None or fallback is None:
                return None
            return base * fallback
        return float(entry[kind])

    def cost_for(self, model: str, tokens: dict[str, float]) -> float | None:
        input_rate = self.rate_for(model, _INPUT)
        if input_rate is None:
            return None
        total = 0.0
        for kind, count in tokens.items():
            rate = self.rate_for(model, kind)
            if rate is not None:
                total += rate * count
        return total / 1e6

    def cost_for_usage(self, model: str, usage: dict) -> float | None:
        return self.cost_for(model, _tokens_from_usage(usage))


def _tokens_from_usage(usage: dict) -> dict[str, float]:
    creation = usage.get("cache_creation_input_tokens") or 0
    tiers = usage.get("cache_creation") or {}
    write_1h = tiers.get("ephemeral_1h_input_tokens") or 0
    write_5m = (tiers.get("ephemeral_5m_input_tokens") or 0) or (creation - write_1h)
    return {
        _INPUT: usage.get("input_tokens") or 0,
        _OUTPUT: usage.get("output_tokens") or 0,
        _CACHE_READ: usage.get("cache_read_input_tokens") or 0,
        _CACHE_WRITE_5M: write_5m,
        _CACHE_WRITE_1H: write_1h,
    }


def load_prices(path: Path | None = None) -> PriceTable:
    table_path = path or default_table_path()
    try:
        # the locale default equals utf-8, so the encoding alternatives behave the same
        data = json.loads(table_path.read_text(encoding="utf-8"))  # pragma: no mutate
    except (OSError, ValueError) as error:
        raise CostError(f"cannot read price table {table_path}: {error}") from error
    rates = data.get("rates_per_mtok")
    if not isinstance(rates, dict):
        raise CostError(f"price table {table_path} carries no rates_per_mtok map")
    return PriceTable(data.get("source_date", "unknown"), rates)
