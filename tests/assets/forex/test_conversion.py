"""Hand-computed goldens for the FX USD conversion graph (FX3 gate).

Every expected number below is derived in a comment from the synthetic
quotes supplied here (SYNTHETIC_TEST_ONLY data).  Pip conventions: 0.0001,
or 0.01 when JPY is the quote.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from research.assets.forex.conversion import (
    ConversionGraph,
    ConversionUnavailable,
    FxQuote,
    JPY_PIP_SIZE,
    DEFAULT_PIP_SIZE,
    base_currency_of,
    pair_currencies,
    pip_size_for_quote,
    quote_currency_of,
)

TOL = 60.0  # explicit tolerance window (seconds), never a silent default

T_MAIN = "2026-01-08T12:00:00+00:00"  # all main quotes live exactly here


def make_graph(extra=None, tolerance=TOL):
    """Graph over the seven initial G10 pairs' quotes we need for goldens."""
    quotes = {
        "EURUSD": [FxQuote(pair="EURUSD", timestamp_utc=T_MAIN, bid=1.1000, ask=1.1002)],
        "USDJPY": [FxQuote(pair="USDJPY", timestamp_utc=T_MAIN, bid=149.99, ask=150.01)],
        "USDCHF": [FxQuote(pair="USDCHF", timestamp_utc=T_MAIN, bid=0.8880, ask=0.8882)],
    }
    if extra:
        for pair, items in extra.items():
            quotes.setdefault(pair, []).extend(items)
    return ConversionGraph(quotes, tolerance_seconds=tolerance)


# --- golden: USD -> JPY direct ----------------------------------------------- #
def test_usd_to_jpy_direct_golden():
    graph = make_graph()
    # USDJPY mid at T_MAIN = (149.99 + 150.01) / 2 = 150.00 exactly.
    # USD is the base of USDJPY, so USD -> JPY multiplies:
    #   10,000 USD * 150.00 = 1,500,000.00 JPY
    assert graph.convert(10_000, "USD", "JPY", T_MAIN) == pytest.approx(1_500_000.0, abs=1e-9)


def test_quote_side_is_explicit_bid_ask_mid():
    graph = make_graph()
    # BID: 10,000 * 149.99 = 1,499,900.00 JPY
    assert graph.convert(10_000, "USD", "JPY", T_MAIN, side="BID") == pytest.approx(1_499_900.0)
    # ASK: 10,000 * 150.01 = 1,500,100.00 JPY
    assert graph.convert(10_000, "USD", "JPY", T_MAIN, side="ASK") == pytest.approx(1_500_100.0)


# --- golden: inverse pair JPY -> USD ------------------------------------------ #
def test_jpy_to_usd_inverse_golden():
    graph = make_graph()
    # JPY -> USD uses the inverse of USDJPY (explicit 1/price inversion):
    #   1,000,000 JPY / 150.00 = 6,666.666666... USD (exactly 20,000/3)
    assert graph.convert(1_000_000, "JPY", "USD", T_MAIN) == pytest.approx(1_000_000 / 150.0, rel=1e-12)
    assert graph.convert(1_000_000, "JPY", "USD", T_MAIN) == pytest.approx(20_000.0 / 3.0, rel=1e-12)


# --- direct vs two-leg consistency --------------------------------------------- #
def test_eur_direct_vs_two_leg_consistency():
    graph = make_graph()
    # Direct legs: EURUSD mid = (1.1000 + 1.1002)/2 = 1.1001; USDJPY mid = 150.00.
    direct_eur_usd = graph.convert(1.0, "EUR", "USD", T_MAIN)
    direct_usd_jpy = graph.convert(1.0, "USD", "JPY", T_MAIN)
    # Two-leg EUR -> JPY through the USD hub must equal the product of legs:
    #   1.1001 * 150.00 = 165.015 JPY per EUR
    two_leg = graph.convert(1.0, "EUR", "JPY", T_MAIN)
    assert two_leg == pytest.approx(direct_eur_usd * direct_usd_jpy, rel=1e-12)
    assert two_leg == pytest.approx(165.015, rel=1e-12)
    # 1,000 EUR -> 165,015.00 JPY
    assert graph.convert(1_000, "EUR", "JPY", T_MAIN) == pytest.approx(165_015.0, rel=1e-12)


def test_inverse_round_trip_is_one():
    graph = make_graph()
    # EUR -> USD = 1.1001 (mid); USD -> EUR = 1 / 1.1001 (inverse pair).
    forward = graph.rate("EUR", "USD", T_MAIN)
    backward = graph.rate("USD", "EUR", T_MAIN)
    assert forward == pytest.approx(1.1001, abs=1e-12)
    assert forward * backward == pytest.approx(1.0, rel=1e-12)


def test_chf_to_jpy_two_leg_golden():
    graph = make_graph()
    # CHF -> USD is the inverse of USDCHF (mid 0.8881): 1 / 0.8881.
    # USD -> JPY multiplies by 150.00.
    #   150.00 / 0.8881 = 168.89967... JPY per CHF
    assert graph.convert(1.0, "CHF", "JPY", T_MAIN) == pytest.approx(150.0 / 0.8881, rel=1e-12)


def test_identity_conversion_needs_no_quotes():
    empty = ConversionGraph({}, tolerance_seconds=TOL)
    assert empty.convert(123.45, "USD", "USD", T_MAIN) == 123.45


# --- fail-closed: missing quote / outside tolerance ----------------------------- #
def test_missing_jpy_quote_at_as_of_fails_closed():
    graph = make_graph()
    later = "2026-01-08T12:05:00+00:00"  # 300s after the only USDJPY quote
    with pytest.raises(ConversionUnavailable) as excinfo:
        graph.convert(10_000, "USD", "JPY", later)
    assert excinfo.value.reason == "MISSING_QUOTE_AT_TIME"


def test_timestamp_outside_tolerance_fails_closed():
    quotes = {
        "USDJPY": [
            FxQuote(pair="USDJPY", timestamp_utc=T_MAIN, bid=149.99, ask=150.01),
            # a much older quote, far outside any tolerance
            FxQuote(pair="USDJPY", timestamp_utc="2026-01-08T09:00:00+00:00", bid=149.0, ask=149.02),
        ]
    }
    graph = ConversionGraph(quotes, tolerance_seconds=60.0)
    # 61s away from the nearest quote -> beyond the 60s window -> hard failure.
    with pytest.raises(ConversionUnavailable) as excinfo:
        graph.convert(1.0, "USD", "JPY", "2026-01-08T12:01:01+00:00")
    assert excinfo.value.reason == "MISSING_QUOTE_AT_TIME"
    # 59s away -> inside the window, must succeed.
    assert graph.convert(1.0, "USD", "JPY", "2026-01-08T12:00:59+00:00") == pytest.approx(150.0)


def test_nearest_quote_inside_window_wins():
    quotes = {
        "USDJPY": [
            FxQuote(pair="USDJPY", timestamp_utc="2026-01-08T11:59:00+00:00", bid=149.99, ask=150.01),
            FxQuote(pair="USDJPY", timestamp_utc="2026-01-08T12:00:30+00:00", bid=150.99, ask=151.01),
        ]
    }
    graph = ConversionGraph(quotes, tolerance_seconds=120.0)
    # as_of 12:00:20: nearest quote is 12:00:30 (10s) vs 11:59:00 (80s).
    # Its mid is 151.00 -> a different-timestamp quote is never used silently.
    assert graph.convert(1.0, "USD", "JPY", "2026-01-08T12:00:20+00:00") == pytest.approx(151.0)


def test_missing_path_fails_closed():
    # No USDJPY anywhere: CHF -> JPY has no USD-hub path.
    graph = ConversionGraph(
        {"USDCHF": [FxQuote(pair="USDCHF", timestamp_utc=T_MAIN, bid=0.8880, ask=0.8882)]},
        tolerance_seconds=TOL,
    )
    with pytest.raises(ConversionUnavailable) as excinfo:
        graph.convert(1.0, "CHF", "JPY", T_MAIN)
    assert excinfo.value.reason == "NO_PATH"


def test_unknown_currency_fails_closed():
    graph = make_graph()
    with pytest.raises(ConversionUnavailable) as excinfo:
        graph.convert(1.0, "USD", "xx", T_MAIN)
    assert excinfo.value.reason == "UNKNOWN_CURRENCY"


def test_crossed_quote_cannot_be_constructed():
    with pytest.raises(ValueError, match="crossed"):
        FxQuote(pair="EURUSD", timestamp_utc=T_MAIN, bid=1.1002, ask=1.1000)
    with pytest.raises(ValueError, match="degenerate"):
        FxQuote(pair="EURUSD", timestamp_utc=T_MAIN, bid=1.1001, ask=1.1001)


def test_naive_timestamp_rejected():
    graph = make_graph()
    with pytest.raises(ValueError, match="timezone-aware"):
        graph.convert(1.0, "USD", "JPY", datetime(2026, 1, 8, 12, 0, 0))


# --- lane-local convention helpers ---------------------------------------------- #
def test_pair_conventions_and_pip_sizes():
    assert pair_currencies("EURUSD") == ("EUR", "USD")
    assert base_currency_of("USDCAD") == "USD"
    assert quote_currency_of("USDJPY") == "JPY"
    # pip sizes for hand-computed goldens: 0.0001, 0.01 when JPY is the quote
    assert JPY_PIP_SIZE == 0.01
    assert DEFAULT_PIP_SIZE == 0.0001
    assert pip_size_for_quote("JPY") == 0.01
    assert pip_size_for_quote("USD") == 0.0001
    assert pip_size_for_quote("CAD") == 0.0001
