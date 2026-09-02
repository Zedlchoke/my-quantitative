"""Normalized instrument metadata (owner: A2, PLAN_stocks.md section 6).

One frozen, validated record describing a tradable instrument across asset
classes.  Every field is explicit; there are no defaults for venue,
calendar, cost model or asset class (and never a 24/7 calendar fallback).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from research.assets.common.contracts import (
    canonical_json,
    canonical_payload,
    require_asset_class,
    require_digest_hex,
    require_finite_float,
    require_token,
)


@dataclass(frozen=True, kw_only=True)
class InstrumentSpec:
    """Normalized instrument metadata shared by all asset-class lanes."""

    symbol: str
    venue: str
    asset_class: str
    tick_size: float
    lot_size: float
    calendar_id: str
    cost_model_id: str
    quote_currency: str
    base_currency: str | None = None
    provider_id: str | None = None
    provider_schema_digest: str | None = None

    def __post_init__(self) -> None:
        require_token(self.symbol, "symbol")
        require_token(self.venue, "venue")
        require_asset_class(self.asset_class)
        require_finite_float(self.tick_size, "tick_size", positive=True)
        require_finite_float(self.lot_size, "lot_size", positive=True)
        require_token(self.calendar_id, "calendar_id")
        require_token(self.cost_model_id, "cost_model_id")
        require_token(self.quote_currency, "quote_currency")
        if self.base_currency is not None:
            require_token(self.base_currency, "base_currency")
        if self.provider_id is not None:
            require_token(self.provider_id, "provider_id")
        if self.provider_schema_digest is not None:
            require_digest_hex(self.provider_schema_digest, "provider_schema_digest")

    def canonical_payload(self) -> dict[str, Any]:
        return canonical_payload(self)

    def canonical_json(self) -> str:
        return canonical_json(self.canonical_payload())
