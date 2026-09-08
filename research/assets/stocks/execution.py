"""Stock execution-cost models and fail-closed fill decisions (owner: A5).

PLAN_stocks.md section 7 (A5), implemented against the frozen
``research.assets.common.execution_cost`` interface (never edited):

* venue commission schedule (per-share with an order minimum);
* bid/ask spread from quotes, or an explicit conservative proxy spread in
  bps when quotes are absent — never both silently;
* participation/ADV market impact (square-root law) with a hard
  order-size cap: orders above the cap DO NOT FILL;
* NO fill on halt / closed session / missing quote / missing ADV when
  impact is priced — every condition arrives as an explicit flag or quote
  field, because the session calendar belongs to another lane;
* one-event entry delay helpers: a signal may only execute on a LATER
  observable event, never on its own event;
* the cost model is an immutable frozen record carrying a
  :class:`CostModelId` and a canonical sha256 ``digest`` of its parameters.

Convention: BUY fills at the ask, SELL fills at the bid (taker, mid =
reference).  ``spread_cost`` is the half-spread paid versus mid:
``quantity * (ask - bid) / 2``.  With the proxy, ``mid * bps / 2 / 1e4``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from research.assets.common.contracts import (
    canonical_json,
    require_finite_float,
    require_token,
    sha256_text,
)
from research.assets.common.execution_cost import (
    CostModelId,
    ExecutionCostEstimate,
    ExecutionCostModel,
)

from research.assets.stocks.accounting import CostBreakdown, FillRecord


# --- component models -------------------------------------------------------- #
@dataclass(frozen=True)
class CommissionSchedule:
    """Per-share commission with a per-order minimum (both explicit)."""

    per_share: float
    min_per_order: float

    def __post_init__(self) -> None:
        require_finite_float(self.per_share, "per_share")
        if float(self.per_share) < 0:
            raise ValueError(f"per_share must be >= 0, got {self.per_share!r}")
        require_finite_float(self.min_per_order, "min_per_order")
        if float(self.min_per_order) < 0:
            raise ValueError(f"min_per_order must be >= 0, got {self.min_per_order!r}")

    def commission(self, quantity: float) -> float:
        require_finite_float(quantity, "quantity")
        if float(quantity) <= 0:
            raise ValueError(f"quantity must be > 0, got {quantity!r}")
        return max(float(self.per_share) * float(quantity), float(self.min_per_order))


@dataclass(frozen=True)
class SpreadQuote:
    """Resolved spread: mid, half-spread, and taker fill prices."""

    mid: float
    half_spread: float
    buy_price: float
    sell_price: float
    source: str


@dataclass(frozen=True)
class SpreadPolicy:
    """Spread from quotes, else the explicit conservative proxy in bps.

    ``proxy_spread_bps=None`` means quotes are REQUIRED (fail closed
    otherwise).  When both quotes and a proxy exist, QUOTES WIN and the
    proxy stays inert — no silent blending.
    """

    proxy_spread_bps: float | None

    def __post_init__(self) -> None:
        if self.proxy_spread_bps is not None:
            require_finite_float(self.proxy_spread_bps, "proxy_spread_bps")
            if float(self.proxy_spread_bps) <= 0:
                raise ValueError(
                    f"proxy_spread_bps must be > 0 when set, got {self.proxy_spread_bps!r}"
                )

    def resolve(
        self,
        *,
        reference_price: float,
        bid: float | None = None,
        ask: float | None = None,
    ) -> SpreadQuote:
        require_finite_float(reference_price, "reference_price")
        if float(reference_price) <= 0:
            raise ValueError(f"reference_price must be > 0, got {reference_price!r}")
        have_quotes = bid is not None and ask is not None
        if have_quotes:
            require_finite_float(bid, "bid")
            require_finite_float(ask, "ask")
            if float(bid) <= 0 or float(ask) <= 0:
                raise ValueError(f"quotes must be > 0, bid={bid!r} ask={ask!r}")
            if float(ask) < float(bid):
                raise ValueError(f"crossed quotes: ask {ask!r} < bid {bid!r}")
            mid = math.fsum((float(bid), float(ask))) / 2.0
            half = math.fsum((float(ask), -float(bid))) / 2.0
            return SpreadQuote(
                mid=mid,
                half_spread=half,
                buy_price=float(ask),
                sell_price=float(bid),
                source="QUOTES",
            )
        if self.proxy_spread_bps is None:
            raise NoQuoteSourceError(
                "no bid/ask quote and no spread proxy configured; fail closed"
            )
        mid = float(reference_price)
        half = mid * float(self.proxy_spread_bps) / 2.0 / 1e4
        return SpreadQuote(
            mid=mid,
            half_spread=half,
            buy_price=math.fsum((mid, half)),
            sell_price=math.fsum((mid, -half)),
            source="PROXY_BPS",
        )


class NoQuoteSourceError(ValueError):
    """Neither quotes nor a proxy spread were available (fail closed)."""


class OrderSizeCapExceeded(ValueError):
    """Order participation exceeds the ADV cap; the order must not fill."""


@dataclass(frozen=True)
class ImpactModel:
    """Square-root participation impact with a hard order-size cap.

    ``impact = coefficient * price * quantity * sqrt(quantity / adv)``.
    ``quantity / adv > max_participation`` raises :class:`OrderSizeCapExceeded`
    (the caller turns that into a NO_FILL decision, never a partial fill).
    """

    coefficient: float
    max_participation: float

    def __post_init__(self) -> None:
        require_finite_float(self.coefficient, "coefficient")
        if float(self.coefficient) < 0:
            raise ValueError(f"coefficient must be >= 0, got {self.coefficient!r}")
        require_finite_float(self.max_participation, "max_participation")
        if not 0 < float(self.max_participation) <= 1:
            raise ValueError(
                f"max_participation must be in (0, 1], got {self.max_participation!r}"
            )

    def participation(self, *, quantity: float, adv: float) -> float:
        require_finite_float(quantity, "quantity")
        if float(quantity) <= 0:
            raise ValueError(f"quantity must be > 0, got {quantity!r}")
        require_finite_float(adv, "adv")
        if float(adv) <= 0:
            raise ValueError(f"adv must be > 0, got {adv!r}")
        return float(quantity) / float(adv)

    def impact(self, *, price: float, quantity: float, adv: float) -> float:
        require_finite_float(price, "price")
        if float(price) <= 0:
            raise ValueError(f"price must be > 0, got {price!r}")
        share = self.participation(quantity=quantity, adv=adv)
        if share > float(self.max_participation):
            raise OrderSizeCapExceeded(
                f"participation {share!r} exceeds cap {self.max_participation!r}; "
                "order must not fill"
            )
        if float(self.coefficient) == 0.0:
            return 0.0
        return float(self.coefficient) * float(price) * float(quantity) * math.sqrt(share)


# --- the equity cost model ---------------------------------------------------- #
@dataclass(frozen=True)
class EquityExecutionModel(ExecutionCostModel):
    """Immutable US-cash-equity cost model implementing the common interface."""

    cost_model_id: str
    commission: CommissionSchedule
    spread: SpreadPolicy
    impact: ImpactModel
    slippage_bps: float
    currency: str

    def __post_init__(self) -> None:
        require_token(self.cost_model_id, "cost_model_id")
        if not isinstance(self.commission, CommissionSchedule):
            raise ValueError("commission must be a CommissionSchedule")
        if not isinstance(self.spread, SpreadPolicy):
            raise ValueError("spread must be a SpreadPolicy")
        if not isinstance(self.impact, ImpactModel):
            raise ValueError("impact must be an ImpactModel")
        require_finite_float(self.slippage_bps, "slippage_bps")
        if float(self.slippage_bps) < 0:
            raise ValueError(f"slippage_bps must be >= 0, got {self.slippage_bps!r}")
        require_token(self.currency, "currency")

    # -- common ExecutionCostModel interface --------------------------------- #
    @property
    def model_id(self) -> CostModelId:
        return CostModelId(self.cost_model_id)

    @property
    def digest(self) -> str:
        """Canonical sha256 over the full parameter set (cost_model_id digest)."""
        payload = {
            "schema": "equity_execution_cost_model",
            "cost_model_id": self.cost_model_id,
            "commission": {
                "per_share": float(self.commission.per_share),
                "min_per_order": float(self.commission.min_per_order),
            },
            "spread": {
                "proxy_spread_bps": (
                    None if self.spread.proxy_spread_bps is None
                    else float(self.spread.proxy_spread_bps)
                ),
            },
            "impact": {
                "coefficient": float(self.impact.coefficient),
                "max_participation": float(self.impact.max_participation),
            },
            "slippage_bps": float(self.slippage_bps),
            "currency": self.currency,
        }
        return sha256_text(canonical_json(payload))

    def _components(
        self,
        *,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        context: Mapping[str, Any] | None,
    ) -> tuple[float, float, float, float, SpreadQuote]:
        """(commission, spread_cost, slippage_cost, impact_cost, quote)."""
        ctx: Mapping[str, Any] = {} if context is None else context
        quote = self.spread.resolve(
            reference_price=price,
            bid=ctx.get("bid"),
            ask=ctx.get("ask"),
        )
        commission = self.commission.commission(quantity)
        spread_cost = float(quantity) * quote.half_spread
        slippage_cost = float(quantity) * float(price) * float(self.slippage_bps) / 1e4
        if float(self.impact.coefficient) > 0.0:
            adv = ctx.get("adv")
            if adv is None:
                raise NoAdvError("impact is priced but context has no adv; fail closed")
            impact_cost = self.impact.impact(price=price, quantity=quantity, adv=float(adv))
        else:
            impact_cost = 0.0
        return commission, spread_cost, slippage_cost, impact_cost, quote

    def estimate(
        self,
        *,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        context: Mapping[str, Any] | None = None,
    ) -> ExecutionCostEstimate:
        """Neutral cost estimate for one fill at ``price`` (common interface)."""
        if side not in ("BUY", "SELL"):
            raise ValueError(f"side must be BUY or SELL, got {side!r}")
        require_finite_float(price, "price")
        if float(price) <= 0:
            raise ValueError(f"price must be > 0, got {price!r}")
        commission, spread_cost, slippage_cost, impact_cost, _ = self._components(
            symbol=symbol, side=side, quantity=quantity, price=float(price), context=context
        )
        return ExecutionCostEstimate(
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=float(price),
            commission=commission,
            spread_cost=spread_cost,
            slippage_cost=slippage_cost,
            impact_cost=impact_cost,
            currency=self.currency,
            cost_model_id=self.cost_model_id,
        )

    # -- fail-closed fill decision ------------------------------------------- #
    def attempt_fill(
        self,
        *,
        symbol: str,
        side: str,
        quantity: float,
        reference_price: float,
        timestamp_utc: str,
        session_open: bool,
        halted: bool,
        bid: float | None = None,
        ask: float | None = None,
        adv: float | None = None,
        fill_id: str | None = None,
    ) -> "ExecutionDecision":
        """All-or-nothing fill decision; every blocker is an explicit input.

        Fail-closed order: HALTED -> SESSION_CLOSED -> MISSING_QUOTE ->
        MISSING_ADV -> PARTICIPATION_CAP.  A NO_FILL decision carries zero
        cost and never touches the ledger.
        """
        require_token(symbol, "symbol")
        if side not in ("BUY", "SELL"):
            raise ValueError(f"side must be BUY or SELL, got {side!r}")
        require_finite_float(quantity, "quantity")
        if float(quantity) <= 0:
            raise ValueError(f"quantity must be > 0, got {quantity!r}")
        require_finite_float(reference_price, "reference_price")
        if float(reference_price) <= 0:
            raise ValueError(f"reference_price must be > 0, got {reference_price!r}")
        if not isinstance(session_open, bool):
            raise ValueError(f"session_open must be a bool, got {session_open!r}")
        if not isinstance(halted, bool):
            raise ValueError(f"halted must be a bool, got {halted!r}")

        if halted:
            return ExecutionDecision.no_fill(
                symbol=symbol, side=side, quantity=quantity, timestamp_utc=timestamp_utc,
                reason="HALTED", detail="trading halted on the symbol",
            )
        if not session_open:
            return ExecutionDecision.no_fill(
                symbol=symbol, side=side, quantity=quantity, timestamp_utc=timestamp_utc,
                reason="SESSION_CLOSED", detail="outside the regular session",
            )
        try:
            quote = self.spread.resolve(
                reference_price=reference_price, bid=bid, ask=ask
            )
        except NoQuoteSourceError as exc:
            return ExecutionDecision.no_fill(
                symbol=symbol, side=side, quantity=quantity, timestamp_utc=timestamp_utc,
                reason="MISSING_QUOTE", detail=str(exc),
            )
        if float(self.impact.coefficient) > 0.0:
            if adv is None:
                return ExecutionDecision.no_fill(
                    symbol=symbol, side=side, quantity=quantity, timestamp_utc=timestamp_utc,
                    reason="MISSING_ADV",
                    detail="impact priced but adv missing; fail closed",
                )
            try:
                share = self.impact.participation(quantity=quantity, adv=float(adv))
            except ValueError as exc:
                return ExecutionDecision.no_fill(
                    symbol=symbol, side=side, quantity=quantity, timestamp_utc=timestamp_utc,
                    reason="BAD_ADV", detail=str(exc),
                )
            if share > float(self.impact.max_participation):
                return ExecutionDecision.no_fill(
                    symbol=symbol, side=side, quantity=quantity, timestamp_utc=timestamp_utc,
                    reason="PARTICIPATION_CAP",
                    detail=f"participation {share!r} > cap "
                           f"{self.impact.max_participation!r}",
                )

        fill_price = quote.buy_price if side == "BUY" else quote.sell_price
        commission = self.commission.commission(quantity)
        spread_cost = float(quantity) * quote.half_spread
        slippage_cost = float(quantity) * fill_price * float(self.slippage_bps) / 1e4
        impact_cost = (
            self.impact.impact(price=fill_price, quantity=quantity, adv=float(adv))
            if float(self.impact.coefficient) > 0.0
            else 0.0
        )
        cost = CostBreakdown(
            commission=commission,
            spread=spread_cost,
            slippage=slippage_cost,
            market_impact=impact_cost,
        )
        estimate = ExecutionCostEstimate(
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=fill_price,
            commission=commission,
            spread_cost=spread_cost,
            slippage_cost=slippage_cost,
            impact_cost=impact_cost,
            currency=self.currency,
            cost_model_id=self.cost_model_id,
        )
        fill = FillRecord(
            symbol=symbol,
            side=side,
            quantity=float(quantity),
            price=fill_price,
            timestamp_utc=timestamp_utc,
            cost=cost,
            fill_id=fill_id,
        )
        return ExecutionDecision(
            status="FILLED",
            reason=None,
            detail=None,
            symbol=symbol,
            side=side,
            quantity=float(quantity),
            timestamp_utc=timestamp_utc,
            fill=fill,
            estimate=estimate,
            rejection_cost=0.0,
        )


class NoAdvError(ValueError):
    """Impact is priced but ADV is missing (fail closed)."""


@dataclass(frozen=True)
class ExecutionDecision:
    """Outcome of one fill attempt: FILLED or NO_FILL (with explicit reason)."""

    status: str
    reason: str | None
    detail: str | None
    symbol: str
    side: str
    quantity: float
    timestamp_utc: str
    fill: FillRecord | None
    estimate: ExecutionCostEstimate | None
    rejection_cost: float

    def __post_init__(self) -> None:
        if self.status not in ("FILLED", "NO_FILL"):
            raise ValueError(f"status must be FILLED or NO_FILL, got {self.status!r}")
        require_token(self.symbol, "symbol")
        if self.side not in ("BUY", "SELL"):
            raise ValueError(f"side must be BUY or SELL, got {self.side!r}")
        require_finite_float(self.quantity, "quantity")
        require_finite_float(self.rejection_cost, "rejection_cost")
        if float(self.rejection_cost) < 0:
            raise ValueError(f"rejection_cost must be >= 0, got {self.rejection_cost!r}")
        if not isinstance(self.timestamp_utc, str) or not self.timestamp_utc.strip():
            raise ValueError("timestamp_utc must be a non-empty ISO-8601 UTC string")
        if self.status == "FILLED":
            if self.reason is not None or self.detail is not None:
                raise ValueError("a FILLED decision must not carry a reason/detail")
            if not isinstance(self.fill, FillRecord) or not isinstance(self.estimate, ExecutionCostEstimate):
                raise ValueError("a FILLED decision requires fill and estimate")
        else:
            if not isinstance(self.reason, str) or not self.reason.strip():
                raise ValueError("a NO_FILL decision REQUIRES a non-empty reason")
            if self.fill is not None or self.estimate is not None:
                raise ValueError("a NO_FILL decision must not carry a fill/estimate")

    @classmethod
    def no_fill(
        cls,
        *,
        symbol: str,
        side: str,
        quantity: float,
        timestamp_utc: str,
        reason: str,
        detail: str,
        rejection_cost: float = 0.0,
    ) -> "ExecutionDecision":
        return cls(
            status="NO_FILL",
            reason=reason,
            detail=detail,
            symbol=symbol,
            side=side,
            quantity=quantity,
            timestamp_utc=timestamp_utc,
            fill=None,
            estimate=None,
            rejection_cost=float(rejection_cost),
        )


# --- one-event entry delay ----------------------------------------------------- #
def next_executable_event_index(
    signal_index: int,
    executable_flags: Sequence[bool],
) -> int | None:
    """One-event entry delay: the first EXECUTABLE event strictly AFTER the signal.

    A signal observed at ``signal_index`` may fill no earlier than the next
    executable event (index >= signal_index + 1); returns None when no later
    event is executable (the entry never happens — fail closed, no same-event
    fill is ever manufactured).
    """
    if not isinstance(signal_index, int) or isinstance(signal_index, bool):
        raise ValueError(f"signal_index must be an int, got {signal_index!r}")
    if signal_index < 0:
        raise ValueError(f"signal_index must be >= 0, got {signal_index!r}")
    flags = tuple(executable_flags)
    for flag in flags:
        if not isinstance(flag, bool):
            raise ValueError(f"executable_flags must be bools, got {flag!r}")
    for index in range(signal_index + 1, len(flags)):
        if flags[index]:
            return index
    return None


def deferred_entry_timestamp(
    timestamps: Sequence[str],
    executable_flags: Sequence[bool],
    signal_index: int,
) -> str | None:
    """Timestamp of the one-event-delayed entry, or None when it never executes."""
    if len(timestamps) != len(executable_flags):
        raise ValueError(
            f"timestamps ({len(timestamps)}) and executable_flags "
            f"({len(executable_flags)}) must have equal length"
    )
    index = next_executable_event_index(signal_index, executable_flags)
    if index is None:
        return None
    stamp = timestamps[index]
    if not isinstance(stamp, str) or not stamp.strip():
        raise ValueError(f"timestamp at {index} must be a non-empty string")
    return stamp
