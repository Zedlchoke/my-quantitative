"""Unavailable-data whitelist: V3 families may require only what exists.

Whitelist: {daily OHLCV, volume, split factors, distributions, calendar}.
Earnings, borrow, quote-spread and fundamentals data are absent from the
free snapshot and MUST be rejected at config-validation time.
"""

from __future__ import annotations

import pytest

from research.stocks_free_v3.data_policy import (
    ALLOWED_DATA_FIELDS,
    UnavailableDataError,
    normalize_field_name,
    validate_family_data_requirements,
)

WHITELIST = {"daily_ohlcv", "volume", "split_factors", "distributions", "calendar"}


def test_whitelist_is_exactly_the_free_snapshot() -> None:
    assert ALLOWED_DATA_FIELDS == WHITELIST


def test_whitelisted_requirements_validate() -> None:
    allowed = validate_family_data_requirements(
        ["daily_ohlcv", "volume", "split_factors", "distributions", "calendar"]
    )
    assert allowed == tuple(sorted(WHITELIST))


def test_normalized_aliases_validate() -> None:
    assert validate_family_data_requirements(["Daily OHLCV", "VOLUME"]) == (
        "daily_ohlcv",
        "volume",
    )
    assert validate_family_data_requirements(["split-factors", "distributions"]) == (
        "distributions",
        "split_factors",
    )


@pytest.mark.parametrize(
    "forbidden",
    [
        "earnings",
        "earnings_dates",
        "eps",
        "borrow",
        "borrow_fee",
        "short_interest",
        "quote",
        "quote_spread",
        "bid_ask",
        "spread",
        "fundamentals",
        "pe",
        "book_value",
        "analyst_estimates",
        "intraday",
        "minute_bars",
        "options",
        "implied_vol",
    ],
)
def test_unavailable_categories_rejected(forbidden: str) -> None:
    with pytest.raises(UnavailableDataError, match=forbidden):
        validate_family_data_requirements(["daily_ohlcv", forbidden])


def test_unknown_field_rejected_whitelist_is_closed() -> None:
    with pytest.raises(UnavailableDataError, match="whitelist"):
        validate_family_data_requirements(["satellite_imagery"])


def test_rejection_lists_every_offender() -> None:
    with pytest.raises(UnavailableDataError) as excinfo:
        validate_family_data_requirements(
            ["earnings", "borrow", "quote_spread", "fundamentals"]
        )
    message = str(excinfo.value)
    for term in ("earnings", "borrow", "quote_spread", "fundamentals"):
        assert term in message


def test_mixed_requirements_rejected_atomically() -> None:
    """One unavailable requirement rejects the whole config (fail closed)."""
    with pytest.raises(UnavailableDataError):
        validate_family_data_requirements(["daily_ohlcv", "volume", "earnings"])


def test_empty_requirements_fail_closed() -> None:
    with pytest.raises(UnavailableDataError, match="no data requirements"):
        validate_family_data_requirements([])


def test_normalizer_is_deterministic() -> None:
    assert normalize_field_name("  Quote-Spread ") == "quote_spread"
    assert normalize_field_name("EarningsDates") == "earningsdates"  # then rejected
    with pytest.raises(UnavailableDataError):
        validate_family_data_requirements(["EarningsDates"])
