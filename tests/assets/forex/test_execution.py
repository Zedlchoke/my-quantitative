"""Hand-computed goldens for FX bid/ask execution (FX2 gate).

Arithmetic is shown in comments next to every expected number.  Quotes are
SYNTHETIC_TEST_ONLY.  Note on one task-stated golden: the brief wrote
"close at bid 1.1010 -> PnL (1.1010-1.1002)*10000 = +80.00", but
0.0008 * 10,000 = 8.00; the correct hand value +8.00 is asserted here.
"""

from __future__ import annotations

import json

import pytest

from research.assets.common.execution_cost import (
    CostModelId,
    ExecutionCostEstimate,
    parse_cost_estimate,
)

from research.assets.forex.accounting import price_pnl_quote
from research.assets.forex.conversion import ConversionGraph, FxQuote
from research.assets.forex.execution import (
    FxExecutionCostModel,
    FxQuoteRejected,
    close_side_for,
)

MODEL_ID = CostModelId("FX_BID_ASK_V1")
T_OPEN = "2026-01-08T21:00:00+00:00"  # Thu 16:00 America/New_York (EST)
T_NOW = "2026-01-08T21:00:30+00:00"  # 30s after the quote: fresh


def make_model():
    # EURUSD costs are USD-quoted -> identity conversion; a USDJPY snapshot
    # (mid exactly 150.00) supports JPY-quoted cost conversion goldens.
    graph = ConversionGraph(
        {
            "USDJPY": [FxQuote(pair="USDJPY", timestamp_utc=T_OPEN, bid=149.99, ask=150.01)],
        },
        tolerance_seconds=60.0,
    )
    return FxExecutionCostModel(model_id=MODEL_ID, conversion=graph, max_quote_age_seconds=60.0)


def ctx(bid, ask, *, timestamp=T_OPEN, now=T_NOW, commission=0.0, slip=0.0, impact=0.0, **extra):
    base = {
        "bid": bid,
        "ask": ask,
        "quote_timestamp_utc": timestamp,
        "now_utc": now,
        "commission_quote": commission,
        "slippage_pips": slip,
        "impact_quote": impact,
    }
    base.update(extra)
    return base


# --- golden: buy fills at ASK, spread cost = (ask - bid) * qty ------------------ #
def test_buy_fills_at_ask_with_spread_cost():
    model = make_model()
    est = model.estimate(
        symbol="EURUSD",
        side="BUY",
        quantity=10_000,
        price=1.1002,
        context=ctx(bid=1.1000, ask=1.1002, commission=1.00),
    )
    assert isinstance(est, ExecutionCostEstimate)
    # fill = ASK = 1.1002
    assert est.price == pytest.approx(1.1002, abs=1e-12)
    # spread cost = (1.1002 - 1.1000) * 10,000 = 2 pips * 0.0001 * 10,000 = 2.00 USD
    assert est.spread_cost == pytest.approx(2.00, abs=1e-12)
    # commission passed in USD-quoted: 1.00
    assert est.commission == pytest.approx(1.00, abs=1e-12)
    assert est.side == "BUY"
    assert est.quantity == 10_000
    assert est.currency == "USD"
    assert est.cost_model_id == "FX_BID_ASK_V1"
    assert est.slippage_cost == 0.0 and est.impact_cost == 0.0
    assert est.total() == pytest.approx(3.00, abs=1e-12)


def test_sell_fills_at_bid():
    model = make_model()
    est = model.estimate(
        symbol="EURUSD",
        side="SELL",
        quantity=10_000,
        price=1.1000,
        context=ctx(bid=1.1000, ask=1.1002),
    )
    # fill = BID = 1.1000; same 2-pip spread -> 2.00 USD
    assert est.price == pytest.approx(1.1000, abs=1e-12)
    assert est.spread_cost == pytest.approx(2.00, abs=1e-12)


# --- golden: close of the long sells at BID; price PnL from executable fills ---- #
def test_long_close_at_bid_price_pnl():
    model = make_model()
    open_est = model.estimate(
        symbol="EURUSD",
        side="BUY",
        quantity=10_000,
        price=1.1002,
        context=ctx(bid=1.1000, ask=1.1002),
    )
    assert close_side_for("LONG") == "SELL"
    close_est = model.estimate(
        symbol="EURUSD",
        side=close_side_for("LONG"),
        quantity=10_000,
        price=1.1010,
        context=ctx(bid=1.1010, ask=1.1012),
    )
    # close fill = BID = 1.1010 (never the 1.1011 midpoint)
    assert close_est.price == pytest.approx(1.1010, abs=1e-12)
    # price PnL = (1.1010 - 1.1002) * 10,000 = 0.0008 * 10,000 = +8.00 USD
    pnl = price_pnl_quote(
        position_side="LONG",
        open_fill_price=open_est.price,
        close_fill_price=close_est.price,
        quantity=10_000,
    )
    assert pnl == pytest.approx(8.00, abs=1e-9)


def test_short_close_buys_at_ask():
    model = make_model()
    assert close_side_for("SHORT") == "BUY"
    open_est = model.estimate(
        symbol="EURUSD",
        side="SELL",
        quantity=10_000,
        price=1.1000,
        context=ctx(bid=1.1000, ask=1.1002),
    )
    assert open_est.price == pytest.approx(1.1000, abs=1e-12)
    close_est = model.estimate(
        symbol="EURUSD",
        side=close_side_for("SHORT"),
        quantity=10_000,
        price=1.1002,
        context=ctx(bid=1.1000, ask=1.1002),
    )
    # short close buys at ASK = 1.1002
    assert close_est.price == pytest.approx(1.1002, abs=1e-12)
    # short price PnL = (open_bid - close_ask) * qty = (1.1000 - 1.1002)*10,000 = -2.00
    pnl = price_pnl_quote(
        position_side="SHORT",
        open_fill_price=open_est.price,
        close_fill_price=close_est.price,
        quantity=10_000,
    )
    assert pnl == pytest.approx(-2.00, abs=1e-9)


# --- fail-closed: crossed / stale / future quotes -------------------------------- #
def test_crossed_quote_raises():
    model = make_model()
    with pytest.raises(FxQuoteRejected) as excinfo:
        model.estimate(
            symbol="EURUSD",
            side="BUY",
            quantity=10_000,
            price=1.1002,
            context=ctx(bid=1.1005, ask=1.1002),  # ask < bid: crossed
        )
    assert excinfo.value.reason == "CROSSED_QUOTE"
    with pytest.raises(FxQuoteRejected) as excinfo:
        model.estimate(
            symbol="EURUSD",
            side="BUY",
            quantity=10_000,
            price=1.1001,
            context=ctx(bid=1.1001, ask=1.1001),  # degenerate zero spread rejected too
        )
    assert excinfo.value.reason == "CROSSED_QUOTE"


def test_stale_quote_raises():
    model = make_model()
    stale_now = "2026-01-08T21:01:01+00:00"  # 61s after the quote > 60s limit
    with pytest.raises(FxQuoteRejected) as excinfo:
        model.estimate(
            symbol="EURUSD",
            side="BUY",
            quantity=10_000,
            price=1.1002,
            context=ctx(bid=1.1000, ask=1.1002, now=stale_now),
        )
    assert excinfo.value.reason == "STALE_QUOTE"
    # exactly 60s old: still acceptable (inclusive limit)
    edge_now = "2026-01-08T21:01:00+00:00"
    est = model.estimate(
        symbol="EURUSD",
        side="BUY",
        quantity=10_000,
        price=1.1002,
        context=ctx(bid=1.1000, ask=1.1002, now=edge_now),
    )
    assert est.price == pytest.approx(1.1002)


def test_quote_from_future_raises():
    model = make_model()
    with pytest.raises(FxQuoteRejected) as excinfo:
        model.estimate(
            symbol="EURUSD",
            side="BUY",
            quantity=10_000,
            price=1.1002,
            context=ctx(bid=1.1000, ask=1.1002, now="2026-01-08T20:59:00+00:00"),
        )
    assert excinfo.value.reason == "QUOTE_FROM_FUTURE"


# --- midpoint terminal valuation is forbidden ------------------------------------ #
def test_midpoint_price_refused():
    model = make_model()
    midpoint = (1.1000 + 1.1002) / 2  # 1.1001
    with pytest.raises(FxQuoteRejected) as excinfo:
        model.estimate(
            symbol="EURUSD",
            side=close_side_for("LONG"),  # terminal close of the long
            quantity=10_000,
            price=midpoint,
            context=ctx(bid=1.1000, ask=1.1002),
        )
    assert excinfo.value.reason == "PRICE_NOT_EXECUTABLE_SIDE"
    # the executable side price itself is accepted for the same close
    est = model.estimate(
        symbol="EURUSD",
        side=close_side_for("LONG"),
        quantity=10_000,
        price=1.1000,
        context=ctx(bid=1.1000, ask=1.1002),
    )
    assert est.price == pytest.approx(1.1000)


def test_wrong_side_price_refused():
    model = make_model()
    with pytest.raises(FxQuoteRejected) as excinfo:
        model.estimate(
            symbol="EURUSD",
            side="SELL",
            quantity=10_000,
            price=1.1002,  # the ASK: a SELL must fill at the BID
            context=ctx(bid=1.1000, ask=1.1002),
        )
    assert excinfo.value.reason == "PRICE_NOT_EXECUTABLE_SIDE"


def test_missing_context_fails_closed():
    model = make_model()
    incomplete = {
        "bid": 1.1000,
        "ask": 1.1002,
        "quote_timestamp_utc": T_OPEN,
        "now_utc": T_NOW,
        # commission_quote / slippage_pips / impact_quote deliberately missing
    }
    with pytest.raises(FxQuoteRejected) as excinfo:
        model.estimate(symbol="EURUSD", side="BUY", quantity=10_000, price=1.1002, context=incomplete)
    assert excinfo.value.reason == "MISSING_CONTEXT"


# --- variable spread + JPY quote-currency conversion (pip 0.01) ------------------ #
def test_slippage_and_jpy_conversion():
    model = make_model()
    est = model.estimate(
        symbol="USDJPY",
        side="BUY",
        quantity=100_000,
        price=150.00,
        context=ctx(
            bid=149.98,
            ask=150.00,
            commission=500.0,  # JPY
            slip=1.0,          # 1 pip adverse
            pip_size=0.01,     # JPY quote -> pip is 0.01
        ),
    )
    # adverse fill = ASK + 1 pip = 150.00 + 0.01 = 150.01
    assert est.price == pytest.approx(150.01, abs=1e-12)
    # spread cost = (150.00 - 149.98) * 100,000 = 2,000 JPY -> /150.00 = 13.333... USD
    assert est.spread_cost == pytest.approx(2_000 / 150.0, rel=1e-12)
    # slippage cost = 1 pip * 0.01 * 100,000 = 1,000 JPY -> /150.00 = 6.666... USD
    assert est.slippage_cost == pytest.approx(1_000 / 150.0, rel=1e-12)
    assert est.commission == pytest.approx(500 / 150.0, rel=1e-12)


def test_slippage_requires_explicit_pip_size():
    model = make_model()
    with pytest.raises(FxQuoteRejected) as excinfo:
        model.estimate(
            symbol="USDJPY",
            side="BUY",
            quantity=100_000,
            price=150.00,
            context=ctx(bid=149.98, ask=150.00, slip=1.0),  # no pip_size
        )
    assert excinfo.value.reason == "MISSING_CONTEXT"


def test_estimate_round_trips_canonical_payload():
    model = make_model()
    est = model.estimate(
        symbol="EURUSD",
        side="BUY",
        quantity=10_000,
        price=1.1002,
        context=ctx(bid=1.1000, ask=1.1002, commission=1.0),
    )
    payload = json.loads(est.canonical_json())
    rebuilt = parse_cost_estimate(payload)
    assert rebuilt == est
