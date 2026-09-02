"""USD conversion graph for G10 spot FX (A5 lane, PLAN_forex.md section 7).

Correctness contracts implemented here (fail closed, always):

* every conversion is anchored to timestamp-aligned quotes supplied by the
  caller; a quote whose timestamp is outside the explicitly configured
  tolerance of ``as_of`` is NEVER used (the request fails);
* direct pair, explicit inverse (``1 / price``) and two-leg paths through the
  USD hub are supported; a missing path or missing quote raises
  :class:`ConversionUnavailable` with a machine-readable ``reason``;
* bid / ask / mid are distinct sides.  ``MID`` may only be obtained by
  naming it explicitly (valuation convention); executable prices are handled
  by :mod:`research.assets.forex.execution`, never here;
* crossed or invalid quotes cannot be constructed at all (``FxQuote``
  validates), so they can never enter the graph.

The instrument registry is owned by a sibling lane: pair conventions and pip
sizes are local constants for the seven initial G10 pairs and callers pass
overrides explicitly where needed.  All quote data used in tests is
SYNTHETIC_TEST_ONLY; no broker schedule is fabricated here.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping, Sequence

__all__ = [
    "DEFAULT_PAIR_CONVENTIONS",
    "DEFAULT_PIP_SIZE",
    "JPY_PIP_SIZE",
    "ConversionError",
    "ConversionUnavailable",
    "ConversionGraph",
    "FxQuote",
    "parse_utc_timestamp",
    "pair_currencies",
    "base_currency_of",
    "quote_currency_of",
    "pip_size_for_quote",
]

# --- lane-local conventions (instrument registry lives in a sibling lane) --- #
# pair -> (base_currency, quote_currency).  The pair NAME itself encodes the
# convention: "EURUSD" quotes 1 EUR in USD.  This table is documentation plus
# a validation aid; ConversionGraph relies on name order.
DEFAULT_PAIR_CONVENTIONS: dict[str, tuple[str, str]] = {
    "EURUSD": ("EUR", "USD"),
    "GBPUSD": ("GBP", "USD"),
    "USDJPY": ("USD", "JPY"),
    "AUDUSD": ("AUD", "USD"),
    "USDCAD": ("USD", "CAD"),
    "USDCHF": ("USD", "CHF"),
    "NZDUSD": ("NZD", "USD"),
}

# pip sizes for hand-computed goldens: 0.0001, or 0.01 when JPY is the quote.
DEFAULT_PIP_SIZE = 0.0001
JPY_PIP_SIZE = 0.01

_CCY_RE = re.compile(r"^[A-Z]{3}$")
_PAIR_RE = re.compile(r"^[A-Z]{6}$")

_QUOTE_SIDES = ("MID", "BID", "ASK")


class ConversionError(Exception):
    """Base class for conversion failures (always fail closed)."""


class ConversionUnavailable(ConversionError):
    """A conversion could not be performed; carries a machine-readable reason.

    Reasons: ``UNKNOWN_CURRENCY``, ``MISSING_PAIR``, ``MISSING_QUOTE_AT_TIME``,
    ``NO_PATH``.  The exception message carries the human-readable detail.
    """

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(f"{reason}: {detail}")
        self.reason = reason
        self.detail = detail


def parse_utc_timestamp(value: str | datetime, field: str = "timestamp") -> datetime:
    """Parse an ISO-8601 string or datetime into an aware UTC datetime.

    Naive datetimes are rejected (fail closed): a missing timezone is data
    corruption, not UTC by assumption.
    """
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        text = value.strip()
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"{field} is not ISO-8601: {value!r}") from exc
    else:
        raise ValueError(f"{field} must be an ISO-8601 string or datetime, got {type(value).__name__}")
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must be timezone-aware, got {value!r}")
    return parsed.astimezone(timezone.utc)


def _require_currency(value: object, field: str) -> str:
    if not isinstance(value, str) or not _CCY_RE.match(value):
        raise ConversionUnavailable(
            "UNKNOWN_CURRENCY",
            f"{field} must be a 3-letter uppercase currency code, got {value!r}",
        )
    return value


def pair_currencies(pair: str) -> tuple[str, str]:
    """(base, quote) for a pair; registry table first, then 6-letter split."""
    if isinstance(pair, str) and pair in DEFAULT_PAIR_CONVENTIONS:
        return DEFAULT_PAIR_CONVENTIONS[pair]
    if not isinstance(pair, str) or not _PAIR_RE.match(pair):
        raise ConversionUnavailable(
            "UNKNOWN_PAIR_CONVENTION",
            f"pair must be a 6-letter symbol with a known convention, got {pair!r}",
        )
    return pair[:3], pair[3:]


def base_currency_of(pair: str) -> str:
    return pair_currencies(pair)[0]


def quote_currency_of(pair: str) -> str:
    return pair_currencies(pair)[1]


def pip_size_for_quote(quote_currency: str) -> float:
    """Pip size for hand-computed goldens: 0.01 when JPY is the quote."""
    _require_currency(quote_currency, "quote_currency")
    return JPY_PIP_SIZE if quote_currency == "JPY" else DEFAULT_PIP_SIZE


@dataclass(frozen=True)
class FxQuote:
    """One timestamped two-sided quote.  Crossed quotes cannot be constructed.

    ``timestamp_utc`` is an ISO-8601 timezone-aware string; ``bid < ask`` and
    both sides are strictly positive and finite.
    """

    pair: str
    timestamp_utc: str
    bid: float
    ask: float

    def __post_init__(self) -> None:
        if not isinstance(self.pair, str) or not _PAIR_RE.match(self.pair):
            raise ValueError(f"pair must be a 6-letter symbol, got {self.pair!r}")
        parse_utc_timestamp(self.timestamp_utc, field="FxQuote.timestamp_utc")
        for name in ("bid", "ask"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"FxQuote.{name} must be a number, got {value!r}")
            if not math.isfinite(float(value)) or float(value) <= 0:
                raise ValueError(f"FxQuote.{name} must be finite and > 0, got {value!r}")
        if float(self.ask) <= float(self.bid):
            raise ValueError(
                f"crossed or degenerate quote rejected (fail closed): "
                f"{self.pair} bid={self.bid!r} ask={self.ask!r} at {self.timestamp_utc}"
            )

    @property
    def timestamp(self) -> datetime:
        return parse_utc_timestamp(self.timestamp_utc, field="FxQuote.timestamp_utc")

    @property
    def mid(self) -> float:
        """Explicitly derived midpoint (valuation side, never an executable)."""
        return (float(self.bid) + float(self.ask)) / 2.0


class ConversionGraph:
    """Timestamp-aligned USD conversion graph over supplied quote snapshots.

    ``tolerance_seconds`` is required and explicit: a quote may only be used
    when ``abs(quote_time - as_of) <= tolerance_seconds``.  When several
    quotes are inside the window the closest one wins; ties resolve to the
    later timestamp (deterministic, documented).
    """

    def __init__(
        self,
        quotes_by_pair: Mapping[str, Sequence[FxQuote]],
        *,
        tolerance_seconds: float,
    ) -> None:
        if isinstance(tolerance_seconds, bool) or not isinstance(tolerance_seconds, (int, float)):
            raise ValueError(f"tolerance_seconds must be a number, got {tolerance_seconds!r}")
        if not math.isfinite(float(tolerance_seconds)) or float(tolerance_seconds) < 0:
            raise ValueError(f"tolerance_seconds must be finite and >= 0, got {tolerance_seconds!r}")
        self._tolerance = float(tolerance_seconds)
        self._quotes: dict[str, list[FxQuote]] = {}
        for pair, quotes in quotes_by_pair.items():
            if not isinstance(pair, str) or not _PAIR_RE.match(pair):
                raise ValueError(f"quote book key must be a 6-letter pair, got {pair!r}")
            validated = [self._validate_quote(pair, q) for q in quotes]
            validated.sort(key=lambda q: (q.timestamp, q.bid))
            if not validated:
                raise ValueError(f"quote book for {pair} is empty (fail closed: omit the pair instead)")
            self._quotes[pair] = validated

    @staticmethod
    def _validate_quote(pair: str, quote: object) -> FxQuote:
        if not isinstance(quote, FxQuote):
            raise ValueError(f"quotes must be FxQuote instances, got {type(quote).__name__}")
        if quote.pair != pair:
            raise ValueError(f"quote pair {quote.pair!r} does not match book key {pair!r}")
        return quote

    @property
    def tolerance_seconds(self) -> float:
        return self._tolerance

    # --- quote selection ---------------------------------------------------- #
    def _quote_at(self, pair: str, as_of: datetime) -> FxQuote:
        book = self._quotes.get(pair)
        if book is None:
            raise ConversionUnavailable(
                "MISSING_PAIR",
                f"no quotes supplied for {pair}",
            )
        best: FxQuote | None = None
        best_key: tuple[float, float] | None = None
        for quote in book:
            delta = abs((quote.timestamp - as_of).total_seconds())
            if delta <= self._tolerance + 1e-9:
                # closest first; ties resolve to the LATER timestamp
                key = (delta, -quote.timestamp.timestamp())
                if best_key is None or key < best_key:
                    best, best_key = quote, key
        if best is None:
            nearest = min(book, key=lambda q: abs((q.timestamp - as_of).total_seconds()))
            nearest_gap = abs((nearest.timestamp - as_of).total_seconds())
            raise ConversionUnavailable(
                "MISSING_QUOTE_AT_TIME",
                f"{pair}: nearest quote at {nearest.timestamp_utc} is {nearest_gap:.6f}s "
                f"from as_of {as_of.isoformat()}, tolerance is {self._tolerance:.6f}s",
            )
        return best

    @staticmethod
    def _side_price(quote: FxQuote, side: str) -> float:
        if side == "BID":
            return float(quote.bid)
        if side == "ASK":
            return float(quote.ask)
        if side == "MID":
            return quote.mid
        raise ValueError(f"side must be one of {_QUOTE_SIDES}, got {side!r}")

    def _direct_rate(
        self, from_ccy: str, to_ccy: str, as_of: datetime, side: str
    ) -> float | None:
        """Rate for one graph edge, or ``None`` when no edge exists.

        Direct pair (``from+to``) multiplies by the side price; the inverse
        pair (``to+from``) divides by it — the inversion is explicit here so
        the code reads as the arithmetic it performs.
        """
        direct = self._quotes.get(from_ccy + to_ccy)
        if direct is not None:
            quote = self._quote_at(from_ccy + to_ccy, as_of)
            return self._side_price(quote, side)
        inverse = self._quotes.get(to_ccy + from_ccy)
        if inverse is not None:
            quote = self._quote_at(to_ccy + from_ccy, as_of)
            price = self._side_price(quote, side)
            return 1.0 / price  # explicit inversion: pair quotes `to` in `from`
        return None

    # --- public API ---------------------------------------------------------- #
    def rate(
        self,
        from_ccy: str,
        to_ccy: str,
        as_of: str | datetime,
        *,
        side: str = "MID",
    ) -> float:
        """Multiplicative rate such that ``amount_in_from * rate = amount_in_to``.

        ``side`` must be named explicitly: ``"MID"`` (valuation), ``"BID"`` or
        ``"ASK"``.  One unit of ``from_ccy`` quoted by the direct pair
        ``{from}{to}`` is the side price; through the inverse pair it is its
        reciprocal; otherwise the path goes through the USD hub in two legs.
        """
        _require_currency(from_ccy, "from_ccy")
        _require_currency(to_ccy, "to_ccy")
        if side not in _QUOTE_SIDES:
            raise ValueError(f"side must be one of {_QUOTE_SIDES}, got {side!r}")
        as_of_dt = parse_utc_timestamp(as_of, field="as_of")
        if from_ccy == to_ccy:
            return 1.0
        one_leg = self._direct_rate(from_ccy, to_ccy, as_of_dt, side)
        if one_leg is not None:
            return one_leg
        if "USD" in (from_ccy, to_ccy):
            raise ConversionUnavailable(
                "NO_PATH",
                f"no direct or inverse pair connects {from_ccy} to {to_ccy}",
            )
        leg_to_usd = self._direct_rate(from_ccy, "USD", as_of_dt, side)
        leg_from_usd = self._direct_rate("USD", to_ccy, as_of_dt, side)
        if leg_to_usd is None or leg_from_usd is None:
            missing = from_ccy if leg_to_usd is None else to_ccy
            raise ConversionUnavailable(
                "NO_PATH",
                f"no two-leg path {from_ccy}->USD->{to_ccy}: "
                f"missing rate between USD and {missing} at {as_of_dt.isoformat()}",
            )
        return leg_to_usd * leg_from_usd

    def convert(
        self,
        amount: float,
        from_ccy: str,
        to_ccy: str,
        as_of: str | datetime,
        *,
        side: str = "MID",
    ) -> float:
        """Convert ``amount`` from ``from_ccy`` to ``to_ccy`` at ``as_of``."""
        if isinstance(amount, bool) or not isinstance(amount, (int, float)):
            raise ValueError(f"amount must be a number, got {amount!r}")
        if not math.isfinite(float(amount)):
            raise ValueError(f"amount must be finite, got {amount!r}")
        return float(amount) * self.rate(from_ccy, to_ccy, as_of, side=side)

    def to_usd(
        self,
        amount: float,
        ccy: str,
        as_of: str | datetime,
        *,
        side: str = "MID",
    ) -> float:
        """Convenience wrapper: convert any graph currency into USD."""
        _require_currency(ccy, "ccy")
        return self.convert(amount, ccy, "USD", as_of, side=side)
