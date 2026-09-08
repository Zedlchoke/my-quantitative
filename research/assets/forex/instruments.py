"""Frozen G10 spot-FX instrument metadata (owner: A3, PLAN_forex.md 7-A3).

Exactly the seven initial pairs, in their conventional USD quotation:

- USD as *quote* currency (``is_inverse_usd_pair=False``):
  ``EURUSD, GBPUSD, AUDUSD, NZDUSD`` — price is USD per 1 unit of base;
- USD as *base* currency (``is_inverse_usd_pair=True``):
  ``USDJPY, USDCAD, USDCHF`` — price is quote currency per 1 USD.

Conventions frozen per pair (no provider coverage is implied; provider
entitlement is currently ``UNAVAILABLE_FAIL_CLOSED`` — see provider.py):

- ``pip_size``: ``0.0001``, except pairs quoted in JPY where it is ``0.01``;
- ``tick_size``: the minimum price increment of the declared quote
  convention, one tenth of a pip (fractional-pip convention);
- ``display_precision``: conventional decimal places (5, or 3 for JPY
  quotes, matching the fractional-pip convention);
- ``size_increment``: 1.0 unit of the base currency.

Lookups and digests fail closed: unknown symbols raise ``ValueError`` (no
silent case-folding, no fallback pair).  The instrument digest is sha256
over the canonical JSON of a schema-tagged payload, byte-stable across
processes via :func:`research.assets.common.contracts.canonical_json`.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from research.assets.common.contracts import (
    canonical_json,
    require_finite_float,
    require_token,
)

INSTRUMENT_SCHEMA = "forex_instrument"
INSTRUMENT_SCHEMA_VERSION = 1

_CURRENCY_CODE_LENGTH = 3


@dataclass(frozen=True)
class ForexPair:
    """Frozen metadata for one spot-FX pair (all fields explicit)."""

    symbol: str
    base_currency: str
    quote_currency: str
    pip_size: float
    tick_size: float
    size_increment: float
    display_precision: int
    is_inverse_usd_pair: bool

    def __post_init__(self) -> None:
        require_token(self.symbol, "symbol")
        require_token(self.base_currency, "base_currency")
        require_token(self.quote_currency, "quote_currency")
        for name in ("base_currency", "quote_currency"):
            code = getattr(self, name)
            if (
                len(code) != _CURRENCY_CODE_LENGTH
                or not code.isalpha()
                or not code.isupper()
            ):
                raise ValueError(
                    f"{name} must be a 3-letter uppercase currency code, got {code!r}"
                )
        if self.symbol != self.base_currency + self.quote_currency:
            raise ValueError(
                f"symbol {self.symbol!r} must equal base+quote "
                f"({self.base_currency!r}+{self.quote_currency!r})"
            )
        if self.base_currency == self.quote_currency:
            raise ValueError("base and quote currencies must differ")
        if "USD" not in (self.base_currency, self.quote_currency):
            raise ValueError(
                f"{self.symbol!r}: this registry only declares the seven "
                "conventional USD pairs; one side must be USD"
            )
        require_finite_float(self.pip_size, "pip_size", positive=True)
        require_finite_float(self.tick_size, "tick_size", positive=True)
        require_finite_float(self.size_increment, "size_increment", positive=True)
        pip_per_tick = self.pip_size / self.tick_size
        if pip_per_tick < 1 or abs(pip_per_tick - round(pip_per_tick)) > 1e-9:
            raise ValueError(
                f"pip_size {self.pip_size!r} must be a positive integer multiple "
                f"of tick_size {self.tick_size!r}"
            )
        if isinstance(self.display_precision, bool) or not isinstance(
            self.display_precision, int
        ) or self.display_precision < 0:
            raise ValueError(
                "display_precision must be a non-negative int, got "
                f"{self.display_precision!r}"
            )
        if not isinstance(self.is_inverse_usd_pair, bool):
            raise ValueError(
                "is_inverse_usd_pair must be a bool, got "
                f"{self.is_inverse_usd_pair!r}"
            )
        # The flag is redundant with the currencies by design; a mismatch is
        # a construction error, never silently recomputed.
        if self.is_inverse_usd_pair != (self.base_currency == "USD"):
            raise ValueError(
                f"{self.symbol!r}: is_inverse_usd_pair="
                f"{self.is_inverse_usd_pair!r} contradicts base currency "
                f"{self.base_currency!r} (True iff USD is the base)"
            )

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "schema": INSTRUMENT_SCHEMA,
            "version": INSTRUMENT_SCHEMA_VERSION,
            "fields": {
                "symbol": self.symbol,
                "base_currency": self.base_currency,
                "quote_currency": self.quote_currency,
                "pip_size": self.pip_size,
                "tick_size": self.tick_size,
                "size_increment": self.size_increment,
                "display_precision": self.display_precision,
                "is_inverse_usd_pair": self.is_inverse_usd_pair,
            },
        }

    def digest(self) -> str:
        """Stable sha256 over the canonical JSON of the convention payload."""
        return hashlib.sha256(
            canonical_json(self.canonical_payload()).encode("utf-8")
        ).hexdigest()


def _pair(
    base: str, quote: str, *, pip: float, tick: float, precision: int
) -> ForexPair:
    return ForexPair(
        symbol=base + quote,
        base_currency=base,
        quote_currency=quote,
        pip_size=pip,
        tick_size=tick,
        size_increment=1.0,
        display_precision=precision,
        is_inverse_usd_pair=(base == "USD"),
    )


_PIP_MAJOR = 0.0001
_PIP_JPY = 0.01
_TICK_MAJOR = _PIP_MAJOR / 10.0
_TICK_JPY = _PIP_JPY / 10.0
_PRECISION_MAJOR = 5
_PRECISION_JPY = 3

#: The seven initial pairs (PLAN_forex.md section 7-A3), frozen registry.
_FX_PAIRS: dict[str, ForexPair] = {
    pair.symbol: pair
    for pair in (
        _pair("EUR", "USD", pip=_PIP_MAJOR, tick=_TICK_MAJOR, precision=_PRECISION_MAJOR),
        _pair("GBP", "USD", pip=_PIP_MAJOR, tick=_TICK_MAJOR, precision=_PRECISION_MAJOR),
        _pair("USD", "JPY", pip=_PIP_JPY, tick=_TICK_JPY, precision=_PRECISION_JPY),
        _pair("AUD", "USD", pip=_PIP_MAJOR, tick=_TICK_MAJOR, precision=_PRECISION_MAJOR),
        _pair("USD", "CAD", pip=_PIP_MAJOR, tick=_TICK_MAJOR, precision=_PRECISION_MAJOR),
        _pair("USD", "CHF", pip=_PIP_MAJOR, tick=_TICK_MAJOR, precision=_PRECISION_MAJOR),
        _pair("NZD", "USD", pip=_PIP_MAJOR, tick=_TICK_MAJOR, precision=_PRECISION_MAJOR),
    )
}

#: Read-only view of the frozen registry.
FX_PAIRS: Mapping[str, ForexPair] = MappingProxyType(dict(_FX_PAIRS))

ALL_SYMBOLS: tuple[str, ...] = tuple(sorted(_FX_PAIRS))


def lookup_symbol(symbol: str) -> ForexPair:
    """Resolve a pair; unknown/invalid symbols fail closed.

    Only the exact canonical uppercase symbol (e.g. ``"EURUSD"``) resolves;
    there is no case-folding, trimming or aliasing fallback.
    """
    if not isinstance(symbol, str):
        raise ValueError(
            f"symbol must be a string, got {type(symbol).__name__}"
        )
    try:
        return _FX_PAIRS[symbol]
    except KeyError as exc:
        raise ValueError(
            f"unknown forex symbol {symbol!r}; known symbols: {sorted(_FX_PAIRS)}"
        ) from exc


def instrument_digest(symbol: str) -> str:
    """Stable convention digest for one pair (fail-closed lookup)."""
    return lookup_symbol(symbol).digest()


def all_instrument_digests() -> Mapping[str, str]:
    """``{symbol: digest}`` for the whole frozen registry (stable order)."""
    return MappingProxyType({s: _FX_PAIRS[s].digest() for s in ALL_SYMBOLS})
