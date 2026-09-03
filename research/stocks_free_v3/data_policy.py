"""Unavailable-data policy: the V3 field whitelist, enforced fail-closed.

Owner: lane A3, STOCKS-FREE-V3 P1 (PLAN_stocks.md section 9 A3, deliverable
6: "Verify no family requires earnings/borrow/quotes unavailable in the free
snapshot").

The zero-cost snapshot contains exactly::

    daily OHLCV, volume, split factors, distributions, calendar

Nothing else exists.  Any V3 family/arm config that requires a field outside
this whitelist (earnings dates, borrow fees, quote spreads, fundamentals,
analyst estimates, intraday bars, ...) is REJECTED at config-validation time
by :func:`validate_family_data_requirements` — before any data is touched,
before any fold is run, and deterministically (same input, same rejection).
The whitelist is closed: an unrecognized field name is a rejection, not an
assumption.
"""

from __future__ import annotations

from typing import Iterable

ALLOWED_DATA_FIELDS = frozenset(
    {
        "daily_ohlcv",
        "volume",
        "split_factors",
        "distributions",
        "calendar",
    }
)

#: Canonical unavailable categories the plan names explicitly, with the
#: common aliases families might use to request them.  Anything not in
#: :data:`ALLOWED_DATA_FIELDS` is rejected anyway; this table only makes the
#: rejection reason precise for the named categories.
UNAVAILABLE_FIELD_ALIASES: dict[str, str] = {
    "earnings": "EARNINGS",
    "earnings_dates": "EARNINGS",
    "earnings_date": "EARNINGS",
    "eps": "EARNINGS",
    "borrow": "BORROW",
    "borrow_fee": "BORROW",
    "borrow_availability": "BORROW",
    "short_interest": "BORROW",
    "quote": "QUOTE_SPREAD",
    "quotes": "QUOTE_SPREAD",
    "quote_spread": "QUOTE_SPREAD",
    "bid_ask": "QUOTE_SPREAD",
    "spread": "QUOTE_SPREAD",
    "spreads": "QUOTE_SPREAD",
    "fundamentals": "FUNDAMENTALS",
    "pe": "FUNDAMENTALS",
    "book_value": "FUNDAMENTALS",
    "analyst": "ANALYST_ESTIMATES",
    "analyst_estimates": "ANALYST_ESTIMATES",
    "estimates": "ANALYST_ESTIMATES",
    "intraday": "INTRADAY_BARS",
    "minute_bars": "INTRADAY_BARS",
    "options": "OPTIONS",
    "implied_vol": "OPTIONS",
}


class UnavailableDataError(ValueError):
    """Raised when a family requires data absent from the free snapshot."""


def normalize_field_name(field: str) -> str:
    """Lowercase, trim, and collapse non-alphanumerics to underscores."""
    cleaned = []
    previous_us = False
    for ch in field.strip().lower():
        if ch.isalnum():
            cleaned.append(ch)
            previous_us = False
        elif not previous_us:
            cleaned.append("_")
            previous_us = True
    return "".join(cleaned).strip("_")


def validate_family_data_requirements(required: Iterable[str]) -> tuple[str, ...]:
    """Validate a family's declared data requirements against the whitelist.

    Returns the normalized, sorted tuple of allowed fields.  Raises
    :class:`UnavailableDataError` when ANY requirement is outside
    :data:`ALLOWED_DATA_FIELDS` (empty requirements fail closed too: a
    family that declares no data cannot run on this snapshot).
    """
    normalized = sorted({normalize_field_name(f) for f in required})
    if not normalized:
        raise UnavailableDataError(
            "family declares no data requirements; the declaration is mandatory "
            "and must be drawn from the free-snapshot whitelist"
        )
    rejected: list[str] = []
    reasons: list[str] = []
    for field in normalized:
        if field in ALLOWED_DATA_FIELDS:
            continue
        category = UNAVAILABLE_FIELD_ALIASES.get(field, field.upper())
        reason = (
            f"{field!r} requires {category} data, which is absent from the "
            "zero-cost snapshot (allowed: daily OHLCV, volume, split factors, "
            "distributions, calendar)"
        )
        rejected.append(field)
        reasons.append(reason)
    if rejected:
        raise UnavailableDataError(
            "config rejected by the V3 unavailable-data whitelist: "
            + "; ".join(reasons)
        )
    return tuple(normalized)


__all__ = [
    "ALLOWED_DATA_FIELDS",
    "UNAVAILABLE_FIELD_ALIASES",
    "UnavailableDataError",
    "normalize_field_name",
    "validate_family_data_requirements",
]
