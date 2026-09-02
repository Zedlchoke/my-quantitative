"""Bid/ask execution-cost model for G10 spot FX (A5 lane, PLAN_forex.md s7).

Contracts implemented here (fail closed, always):

* buys fill at the ASK, sells fill at the BID; closing a long is a SELL at
  the BID, closing a short is a BUY at the ASK;
* spread is variable per pair/session and arrives WITH the quote
  (``(ask - bid) * quantity`` in quote currency); there is no global pip;
* spread / commission / slippage / impact costs are booked in quote currency
  and then converted to USD through the timestamp-aligned conversion graph
  (:mod:`research.assets.forex.conversion`);
* stale quotes (beyond an explicit max age), crossed quotes, quotes from the
  future and any ``price`` argument that is not the executable side (e.g. a
  midpoint) are rejected — the model cannot be tricked into filling at a
  non-executable price, so a terminal close can only ever use BID/ASK.

Implements the neutral :class:`~research.assets.common.execution_cost.ExecutionCostModel`
interface and returns :class:`~research.assets.common.execution_cost.ExecutionCostEstimate`.
All quote data in tests is SYNTHETIC_TEST_ONLY.
"""

from __future__ import annotations

import math
from typing import Any, Mapping

from research.assets.common.execution_cost import (
    CostModelId,
    ExecutionCostEstimate,
    ExecutionCostModel,
)

from research.assets.forex.conversion import (
    ConversionGraph,
    parse_utc_timestamp,
    quote_currency_of,
)

__all__ = [
    "FxExecutionError",
    "FxQuoteRejected",
    "FxExecutionCostModel",
    "close_side_for",
]

_EXECUTION_SIDES = ("BUY", "SELL")
_POSITION_SIDES = ("LONG", "SHORT")


class FxExecutionError(Exception):
    """Base class for FX execution failures (always fail closed)."""


class FxQuoteRejected(FxExecutionError):
    """A quote or price argument was rejected; carries a machine-readable reason.

    Reasons: ``CROSSED_QUOTE``, ``STALE_QUOTE``, ``QUOTE_FROM_FUTURE``,
    ``MISSING_CONTEXT``, ``PRICE_NOT_EXECUTABLE_SIDE``, ``INVALID_ARGUMENT``.
    """

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(f"{reason}: {detail}")
        self.reason = reason
        self.detail = detail


def close_side_for(position_side: str) -> str:
    """The closing order side for an open position.

    Closing a LONG is a SELL (fills at BID); closing a SHORT is a BUY (fills
    at ASK).
    """
    if position_side == "LONG":
        return "SELL"
    if position_side == "SHORT":
        return "BUY"
    raise FxQuoteRejected(
        "INVALID_ARGUMENT",
        f"position_side must be one of {_POSITION_SIDES}, got {position_side!r}",
    )


def _require_number(context: Mapping[str, Any], key: str) -> float:
    if key not in context:
        raise FxQuoteRejected(
            "MISSING_CONTEXT",
            f"context key {key!r} is required (fail closed: no silent defaults)",
        )
    value = context[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise FxQuoteRejected("INVALID_ARGUMENT", f"context[{key!r}] must be a number, got {value!r}")
    if not math.isfinite(float(value)):
        raise FxQuoteRejected("INVALID_ARGUMENT", f"context[{key!r}] must be finite, got {value!r}")
    return float(value)


class FxExecutionCostModel(ExecutionCostModel):
    """Executable-side FX fill + cost model over a conversion graph.

    ``max_quote_age_seconds`` is required and explicit: a quote older than
    that (measured against the caller-supplied ``now_utc``) is stale and the
    fill is refused.
    """

    def __init__(
        self,
        *,
        model_id: CostModelId,
        conversion: ConversionGraph,
        max_quote_age_seconds: float,
    ) -> None:
        if not isinstance(model_id, CostModelId):
            raise ValueError(f"model_id must be a CostModelId, got {type(model_id).__name__}")
        if not isinstance(conversion, ConversionGraph):
            raise ValueError(
                f"conversion must be a ConversionGraph, got {type(conversion).__name__}"
            )
        if isinstance(max_quote_age_seconds, bool) or not isinstance(max_quote_age_seconds, (int, float)):
            raise ValueError(
                f"max_quote_age_seconds must be a number, got {max_quote_age_seconds!r}"
            )
        if not math.isfinite(float(max_quote_age_seconds)) or max_quote_age_seconds <= 0:
            raise ValueError(
                f"max_quote_age_seconds must be finite and > 0, got {max_quote_age_seconds!r}"
            )
        self._model_id = model_id
        self._conversion = conversion
        self._max_age = float(max_quote_age_seconds)

    @property
    def model_id(self) -> CostModelId:
        return self._model_id

    @property
    def max_quote_age_seconds(self) -> float:
        return self._max_age

    # --- executable-side helpers --------------------------------------------- #
    @staticmethod
    def fill_price(*, side: str, bid: float, ask: float) -> float:
        """The executable price for an order side: BUY -> ASK, SELL -> BID."""
        if side == "BUY":
            return float(ask)
        if side == "SELL":
            return float(bid)
        raise FxQuoteRejected(
            "INVALID_ARGUMENT",
            f"side must be one of {_EXECUTION_SIDES}, got {side!r}",
        )

    @staticmethod
    def _validated_sides(bid: float, ask: float) -> None:
        if ask <= bid:
            raise FxQuoteRejected(
                "CROSSED_QUOTE",
                f"bid={bid!r} ask={ask!r} is crossed or degenerate (fail closed)",
            )

    # --- ExecutionCostModel interface ----------------------------------------- #
    def estimate(
        self,
        *,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        context: Mapping[str, Any] | None = None,
    ) -> ExecutionCostEstimate:
        """Cost estimate for one FX fill.

        Required ``context`` keys (missing keys are a hard error — no silent
        defaults anywhere):

        * ``bid``, ``ask`` — the two-sided quote for this fill;
        * ``quote_timestamp_utc`` — quote stamp, anchors the USD conversion;
        * ``now_utc`` — reference "now" for the staleness check;
        * ``commission_quote`` — commission for this fill in quote currency;
        * ``slippage_pips`` — adverse slippage in pips (>= 0; ``pip_size`` in
          context is required when it is > 0);
        * ``impact_quote`` — market-impact cost in quote currency.

        The ``price`` argument must equal the executable side (BUY: ask,
        SELL: bid) within ``1e-9``; passing a midpoint (or any other
        non-executable price) raises :class:`FxQuoteRejected`.  This is what
        forbids midpoint terminal valuation at the type level.
        """
        ctx = context or {}
        if side not in _EXECUTION_SIDES:
            raise FxQuoteRejected("INVALID_ARGUMENT", f"side must be BUY or SELL, got {side!r}")
        if isinstance(symbol, str) and not symbol.strip():
            raise FxQuoteRejected("INVALID_ARGUMENT", "symbol must be a non-empty token")
        if isinstance(quantity, bool) or not isinstance(quantity, (int, float)) or not math.isfinite(float(quantity)) or float(quantity) <= 0:
            raise FxQuoteRejected(
                "INVALID_ARGUMENT", f"quantity must be a finite number > 0, got {quantity!r}"
            )
        if isinstance(price, bool) or not isinstance(price, (int, float)) or not math.isfinite(float(price)):
            raise FxQuoteRejected("INVALID_ARGUMENT", f"price must be a finite number, got {price!r}")

        bid = _require_number(ctx, "bid")
        ask = _require_number(ctx, "ask")
        self._validated_sides(bid, ask)

        for key in ("quote_timestamp_utc", "now_utc"):
            if key not in ctx:
                raise FxQuoteRejected(
                    "MISSING_CONTEXT",
                    f"context key {key!r} is required (fail closed: no silent defaults)",
                )
        quote_ts = parse_utc_timestamp(ctx["quote_timestamp_utc"], field="quote_timestamp_utc")
        now_ts = parse_utc_timestamp(ctx["now_utc"], field="now_utc")
        age_seconds = (now_ts - quote_ts).total_seconds()
        if age_seconds < 0:
            raise FxQuoteRejected(
                "QUOTE_FROM_FUTURE",
                f"quote timestamp {ctx['quote_timestamp_utc']!r} is after now {ctx['now_utc']!r}",
            )
        if age_seconds > self._max_age:
            raise FxQuoteRejected(
                "STALE_QUOTE",
                f"quote age {age_seconds:.6f}s exceeds max_quote_age_seconds "
                f"{self._max_age:.6f}s (fail closed)",
            )

        executable = self.fill_price(side=side, bid=bid, ask=ask)
        if abs(float(price) - executable) > 1e-9:
            raise FxQuoteRejected(
                "PRICE_NOT_EXECUTABLE_SIDE",
                f"side {side} must fill at the executable price {executable!r} "
                f"(BUY->ASK, SELL->BID); got price {price!r}. Midpoints are never "
                f"executable and a terminal close always uses BID/ASK.",
            )

        slippage_pips = _require_number(ctx, "slippage_pips")
        if slippage_pips < 0:
            raise FxQuoteRejected(
                "INVALID_ARGUMENT", f"slippage_pips must be >= 0, got {slippage_pips!r}"
            )
        commission_quote = _require_number(ctx, "commission_quote")
        if commission_quote < 0:
            raise FxQuoteRejected(
                "INVALID_ARGUMENT", f"commission_quote must be >= 0, got {commission_quote!r}"
            )
        impact_quote = _require_number(ctx, "impact_quote")
        if impact_quote < 0:
            raise FxQuoteRejected(
                "INVALID_ARGUMENT", f"impact_quote must be >= 0, got {impact_quote!r}"
            )

        quantity_f = float(quantity)
        if slippage_pips > 0:
            if "pip_size" not in ctx:
                raise FxQuoteRejected(
                    "MISSING_CONTEXT",
                    "context key 'pip_size' is required when slippage_pips > 0 "
                    "(pair conventions live in the caller, no global pip)",
                )
            pip_size = _require_number(ctx, "pip_size")
            if pip_size <= 0:
                raise FxQuoteRejected("INVALID_ARGUMENT", f"pip_size must be > 0, got {pip_size!r}")
            slip_price = slippage_pips * pip_size
            fill = executable + slip_price if side == "BUY" else executable - slip_price
            slippage_cost_quote = slip_price * quantity_f
        else:
            fill = executable
            slippage_cost_quote = 0.0

        # variable spread for THIS pair/session arrives with the quote
        spread_cost_quote = (ask - bid) * quantity_f

        quote_ccy = ctx.get("quote_currency") or quote_currency_of(symbol)
        as_of = quote_ts
        to_usd = lambda amount: self._conversion.convert(  # noqa: E731
            amount, quote_ccy, "USD", as_of, side="MID"
        )

        return ExecutionCostEstimate(
            symbol=symbol,
            side=side,
            quantity=quantity_f,
            price=fill,
            commission=to_usd(commission_quote),
            spread_cost=to_usd(spread_cost_quote),
            slippage_cost=to_usd(slippage_cost_quote),
            impact_cost=to_usd(impact_quote),
            currency="USD",
            cost_model_id=str(self._model_id),
        )
