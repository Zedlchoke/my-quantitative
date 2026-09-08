"""Canonical USD accounting identity for G10 spot FX (A5 lane).

Implements PLAN_forex.md section 7 exactly:

    ending_USD - starting_USD
    = realized_price_pnl_USD + terminal_pnl_USD
      + rollover_cashflows_USD + explicit_interest_USD
      - commissions_USD - spread_USD - slippage_USD
      - market_impact_USD - rejection_costs_USD

Contracts (fail closed, always):

* every identity term is explicit; a missing (None) term raises
  :class:`MissingAccountingInput` instead of defaulting to 0.0;
* position accounting is computed in the pair's quote currency and converted
  to USD through the timestamp-aligned conversion graph
  (:mod:`research.assets.forex.conversion`);
* price PnL uses executable fills only: long PnL is (close_fill - open_fill)
  where the open fill was the ASK and the close fill is the BID (and
  symmetrically for shorts) — the executable sides are enforced by
  :mod:`research.assets.forex.execution`;
* exposure is reported per underlying currency (base and quote legs), not
  only by pair, and each native exposure converts to USD through the graph;
* the identity check takes an explicit tolerance and raises
  :class:`AccountingIdentityError` on breach.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Sequence

from research.assets.common.carrying_cost import CashflowLine

from research.assets.forex.conversion import (
    ConversionGraph,
    parse_utc_timestamp,
    quote_currency_of,
)

__all__ = [
    "AccountingError",
    "MissingAccountingInput",
    "AccountingIdentityError",
    "FxAccountingStatement",
    "check_identity",
    "identity_residual",
    "price_pnl_quote",
    "usd_amount",
    "rollover_usd_total",
    "currency_exposures",
    "exposure_usd_by_currency",
    "round_trip_statement",
]

_IDENTITY_TERMS = (
    "starting_usd",
    "ending_usd",
    "realized_price_pnl_usd",
    "terminal_pnl_usd",
    "rollover_cashflows_usd",
    "explicit_interest_usd",
    "commissions_usd",
    "spread_usd",
    "slippage_usd",
    "market_impact_usd",
    "rejection_costs_usd",
)


class AccountingError(Exception):
    """Base class for FX accounting failures (always fail closed)."""


class MissingAccountingInput(AccountingError):
    """An identity term or accounting input is missing; nothing is defaulted."""


class AccountingIdentityError(AccountingError):
    """The canonical USD identity does not close within tolerance."""

    def __init__(self, residual: float, tolerance: float) -> None:
        super().__init__(
            f"accounting identity breached: residual={residual!r} exceeds "
            f"tolerance={tolerance!r} (USD)"
        )
        self.residual = residual
        self.tolerance = tolerance


def _require_term(value: object, field: str) -> float:
    if value is None:
        raise MissingAccountingInput(
            f"accounting term {field!r} is missing; identity cannot be evaluated "
            f"(fail closed: no silent 0.0 default)"
        )
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MissingAccountingInput(f"accounting term {field!r} must be a number, got {value!r}")
    if not math.isfinite(float(value)):
        raise MissingAccountingInput(f"accounting term {field!r} must be finite, got {value!r}")
    return float(value)


@dataclass(frozen=True, kw_only=True)
class FxAccountingStatement:
    """The canonical USD identity, term by term.

    Every term must be provided explicitly (use ``0.0`` for "nothing", not
    ``None``); ``None`` blocks the identity with
    :class:`MissingAccountingInput`.
    """

    starting_usd: float | None
    ending_usd: float | None
    realized_price_pnl_usd: float | None
    terminal_pnl_usd: float | None
    rollover_cashflows_usd: float | None
    explicit_interest_usd: float | None
    commissions_usd: float | None
    spread_usd: float | None
    slippage_usd: float | None
    market_impact_usd: float | None
    rejection_costs_usd: float | None

    def residual(self) -> float:
        """LHS - RHS of the canonical identity (raises on missing terms)."""
        values = {name: _require_term(getattr(self, name), name) for name in _IDENTITY_TERMS}
        lhs = math.fsum((values["ending_usd"], -values["starting_usd"]))
        rhs = math.fsum(
            (
                values["realized_price_pnl_usd"],
                values["terminal_pnl_usd"],
                values["rollover_cashflows_usd"],
                values["explicit_interest_usd"],
                -values["commissions_usd"],
                -values["spread_usd"],
                -values["slippage_usd"],
                -values["market_impact_usd"],
                -values["rejection_costs_usd"],
            )
        )
        return math.fsum((lhs, -rhs))

    def with_ending_usd(self, ending_usd: float) -> "FxAccountingStatement":
        """Perturbation helper (tests): a copy with a different ending mark."""
        return replace(self, ending_usd=ending_usd)


def identity_residual(statement: FxAccountingStatement) -> float:
    """Residual of the canonical USD identity (raises on missing terms)."""
    return statement.residual()


def check_identity(statement: FxAccountingStatement, *, tolerance: float) -> float:
    """Fail-closed identity check with an explicit tolerance.

    Returns the residual (0.0 within floating noise) when the identity
    closes; raises :class:`AccountingIdentityError` otherwise.
    """
    if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)) or not math.isfinite(float(tolerance)) or tolerance < 0:
        raise ValueError(f"tolerance must be a finite number >= 0, got {tolerance!r}")
    residual = statement.residual()
    if abs(residual) > float(tolerance):
        raise AccountingIdentityError(residual, float(tolerance))
    return residual


# --- quote-currency position accounting -------------------------------------- #
def price_pnl_quote(
    *,
    position_side: str,
    open_fill_price: float,
    close_fill_price: float,
    quantity: float,
) -> float:
    """Realized price PnL in the pair's quote currency from executable fills.

    LONG: bought at the ASK, closed at the BID ->
        (close_fill - open_fill) * quantity.
    SHORT: sold at the BID, closed at the ASK ->
        (open_fill - close_fill) * quantity.
    """
    if position_side not in ("LONG", "SHORT"):
        raise ValueError(f"position_side must be LONG or SHORT, got {position_side!r}")
    for name, value in (
        ("open_fill_price", open_fill_price),
        ("close_fill_price", close_fill_price),
        ("quantity", quantity),
    ):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise ValueError(f"{name} must be a finite number, got {value!r}")
    if float(quantity) <= 0:
        raise ValueError(f"quantity must be > 0, got {quantity!r}")
    if float(open_fill_price) <= 0 or float(close_fill_price) <= 0:
        raise ValueError("fill prices must be > 0")
    if position_side == "LONG":
        return (float(close_fill_price) - float(open_fill_price)) * float(quantity)
    return (float(open_fill_price) - float(close_fill_price)) * float(quantity)


def usd_amount(
    amount_quote: float,
    pair: str,
    as_of: str,
    *,
    graph: ConversionGraph,
    side: str = "MID",
) -> float:
    """Convert a quote-currency amount to USD at the timestamp-aligned quote."""
    quote_ccy = quote_currency_of(pair)
    return graph.convert(amount_quote, quote_ccy, "USD", as_of, side=side)


def rollover_usd_total(
    lines: Sequence[CashflowLine],
    *,
    graph: ConversionGraph,
) -> float:
    """Sum signed rollover cashflow lines into USD at each line's timestamp.

    Every line must be a rollover line (kind ``ROLLOVER``, never FUNDING)
    carrying its own quote currency; conversion failures propagate (fail
    closed).
    """
    total = 0.0
    for line in lines:
        if line.kind != "ROLLOVER":
            raise AccountingError(
                f"unexpected cashflow kind {line.kind!r} in FX accounting "
                f"(FX rollover is never FUNDING)"
            )
        total = math.fsum((total, graph.to_usd(line.amount, line.currency, line.timestamp_utc)))
    return total


# --- exposure by underlying currency ------------------------------------------ #
@dataclass(frozen=True)
class CurrencyExposure:
    """One native-currency leg of a position (signed, in that currency)."""

    currency: str
    native_amount: float


def currency_exposures(
    *,
    pair: str,
    position_qty: float,
    fill_price: float,
) -> tuple[CurrencyExposure, CurrencyExposure]:
    """Split a position into its two underlying-currency legs.

    Long ``q`` of ``BASEQUOTE`` at fill ``p`` is long ``q`` BASE and short
    ``q * p`` QUOTE (and symmetrically for shorts).  The pair convention
    comes from the conversion module's registry mapping.
    """
    from research.assets.forex.conversion import pair_currencies

    base, quote = pair_currencies(pair)
    if isinstance(position_qty, bool) or not isinstance(position_qty, (int, float)) or not math.isfinite(float(position_qty)):
        raise ValueError(f"position_qty must be a finite number, got {position_qty!r}")
    if isinstance(fill_price, bool) or not isinstance(fill_price, (int, float)) or not math.isfinite(float(fill_price)) or float(fill_price) <= 0:
        raise ValueError(f"fill_price must be a finite number > 0, got {fill_price!r}")
    qty = float(position_qty)
    return (
        CurrencyExposure(currency=base, native_amount=qty),
        CurrencyExposure(currency=quote, native_amount=-qty * float(fill_price)),
    )


def exposure_usd_by_currency(
    exposures: Sequence[CurrencyExposure],
    *,
    graph: ConversionGraph,
    as_of: str,
) -> dict[str, float]:
    """Each native exposure converted to USD at ``as_of`` (fail closed)."""
    parse_utc_timestamp(as_of, field="as_of")
    converted: dict[str, float] = {}
    for exposure in exposures:
        usd = graph.to_usd(exposure.native_amount, exposure.currency, as_of)
        converted[exposure.currency] = math.fsum((converted.get(exposure.currency, 0.0), usd))
    return converted


# --- end-to-end statement assembly --------------------------------------------- #
def round_trip_statement(
    *,
    starting_usd: float,
    ending_usd: float,
    realized_price_pnl_quote_amount: float,
    pair: str,
    close_as_of: str,
    graph: ConversionGraph,
    rollover_lines: Sequence[CashflowLine],
    commissions_usd: float,
    spread_usd: float,
    slippage_usd: float,
    market_impact_usd: float,
    rejection_costs_usd: float,
    explicit_interest_usd: float,
    terminal_pnl_usd: float,
    conversion_side: str,
) -> FxAccountingStatement:
    """Assemble the canonical statement for a closed round trip.

    The realized price PnL (quote currency) converts at the closing
    timestamp quote; rollover lines convert at each line's own timestamp.
    A missing rollover schedule upstream raises before any statement exists
    (fail closed) — this function never substitutes a default.
    """
    realized_usd = graph.convert(
        realized_price_pnl_quote_amount,
        quote_currency_of(pair),
        "USD",
        close_as_of,
        side=conversion_side,
    )
    rollover_usd = rollover_usd_total(rollover_lines, graph=graph)
    return FxAccountingStatement(
        starting_usd=starting_usd,
        ending_usd=ending_usd,
        realized_price_pnl_usd=realized_usd,
        terminal_pnl_usd=terminal_pnl_usd,
        rollover_cashflows_usd=rollover_usd,
        explicit_interest_usd=explicit_interest_usd,
        commissions_usd=commissions_usd,
        spread_usd=spread_usd,
        slippage_usd=slippage_usd,
        market_impact_usd=market_impact_usd,
        rejection_costs_usd=rejection_costs_usd,
    )
