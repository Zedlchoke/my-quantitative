"""Carrying-cost interface (owner: A2, PLAN_stocks.md section 6).

Asset-neutral interface for the three carry families:

* crypto: perpetual funding (``CryptoFundingCarry``);
* equities: borrow cost plus dividend liability on shorts
  (``EquityBorrowDividendCarry``);
* forex: overnight rollover / swap points (``FxRolloverCarry``).

Carry is always expressed as signed :class:`CashflowLine` results
(negative = paid by the position holder).  This module defines interfaces
and the result type only; each asset-class lane implements its own models.
No default carry, no implicit zero-cost assumption.
"""

from __future__ import annotations

import abc
import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

from research.assets.common.contracts import canonical_json, canonical_payload, require_token

CASHFLOW_KINDS = ("FUNDING", "BORROW", "DIVIDEND", "ROLLOVER")


@dataclass(frozen=True, kw_only=True)
class CashflowLine:
    """One signed carry cashflow (neutral result type for all asset classes).

    ``amount`` is signed: negative means the position pays (funding paid,
    borrow fees, dividends owed on shorts, negative rollover).  ``kind`` is
    one of :data:`CASHFLOW_KINDS`.
    """

    timestamp_utc: str
    amount: float
    currency: str
    kind: str
    instrument_symbol: str | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        stamp = self.timestamp_utc
        if not isinstance(stamp, str) or not stamp.strip():
            raise ValueError("timestamp_utc must be a non-empty ISO-8601 UTC string")
        try:
            parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"timestamp_utc is not ISO-8601: {stamp!r}") from exc
        if parsed.tzinfo is None:
            raise ValueError("timestamp_utc must be timezone-aware (UTC)")
        if isinstance(self.amount, bool) or not isinstance(self.amount, (int, float)):
            raise ValueError(f"amount must be a number, got {self.amount!r}")
        if not math.isfinite(float(self.amount)):
            raise ValueError(f"amount must be finite, got {self.amount!r}")
        require_token(self.currency, "currency")
        if self.kind not in CASHFLOW_KINDS:
            raise ValueError(f"kind must be one of {CASHFLOW_KINDS}, got {self.kind!r}")
        if self.instrument_symbol is not None:
            require_token(self.instrument_symbol, "instrument_symbol")

    @property
    def is_paid(self) -> bool:
        return float(self.amount) < 0.0

    def canonical_payload(self) -> dict[str, Any]:
        return canonical_payload(self)

    def canonical_json(self) -> str:
        return canonical_json(self.canonical_payload())


def parse_cashflow_line(payload: Mapping[str, Any]) -> CashflowLine:
    """Rebuild a :class:`CashflowLine` from its canonical payload."""
    return CashflowLine(
        timestamp_utc=payload["timestamp_utc"],
        amount=payload["amount"],
        currency=payload["currency"],
        kind=payload["kind"],
        instrument_symbol=payload.get("instrument_symbol"),
        note=payload.get("note"),
    )


class CarryingCostModel(abc.ABC):
    """Interface implemented per asset class; carry is never implicit."""

    @property
    @abc.abstractmethod
    def model_id(self) -> str:
        """Stable identifier of this carry model (referenced by contracts)."""

    @abc.abstractmethod
    def cashflows(
        self,
        *,
        instrument_symbol: str,
        position_qty: float,
        interval_start_utc: str,
        interval_end_utc: str,
        context: Mapping[str, Any] | None = None,
    ) -> tuple[CashflowLine, ...]:
        """Signed carry cashflows for the position over the closed interval."""


class CryptoFundingCarry(CarryingCostModel):
    """Crypto perpetual funding carry (implemented by the crypto lane)."""


class EquityBorrowDividendCarry(CarryingCostModel):
    """Equity borrow cost + short dividend liability (stocks lane)."""


class FxRolloverCarry(CarryingCostModel):
    """FX overnight rollover / swap carry (forex lane)."""
