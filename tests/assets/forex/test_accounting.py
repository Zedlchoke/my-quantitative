"""Hand-computed goldens for the canonical USD accounting identity (FX5).

Identity under test (PLAN_forex.md section 7):

    ending_USD - starting_USD
    = realized_price_pnl_USD + terminal_pnl_USD
      + rollover_cashflows_USD + explicit_interest_USD
      - commissions_USD - spread_USD - slippage_USD
      - market_impact_USD - rejection_costs_USD

All quotes and swap schedules below are SYNTHETIC_TEST_ONLY.  Reference week
January 2026, America/New_York (EST = UTC-5): Wed 07, Thu 08, Fri 09.
"""

from __future__ import annotations

import math

import pytest

from research.assets.common.execution_cost import CostModelId

from research.assets.forex.accounting import (
    AccountingIdentityError,
    FxAccountingStatement,
    MissingAccountingInput,
    check_identity,
    currency_exposures,
    exposure_usd_by_currency,
    identity_residual,
    price_pnl_quote,
    rollover_usd_total,
    round_trip_statement,
)
from research.assets.forex.conversion import ConversionGraph, FxQuote
from research.assets.forex.execution import FxExecutionCostModel, close_side_for
from research.assets.forex.rollover import (
    RolloverLeg,
    RolloverSchedule,
    RolloverScheduleUnavailable,
    SWAP_POINTS,
    SYNTHETIC_TEST_ONLY,
    FxRolloverCarry,
)

T_OPEN = "2026-01-08T21:00:00+00:00"  # Thu 16:00 ET
T_CLOSE = "2026-01-09T21:00:00+00:00"  # Fri 16:00 ET
TOL = 1e-9


def make_graph():
    return ConversionGraph(
        {
            "EURUSD": [
                FxQuote(pair="EURUSD", timestamp_utc=T_OPEN, bid=1.1000, ask=1.1002),
                FxQuote(pair="EURUSD", timestamp_utc=T_CLOSE, bid=1.1010, ask=1.1012),
            ],
            "USDJPY": [
                FxQuote(pair="USDJPY", timestamp_utc=T_OPEN, bid=149.98, ask=150.00),
                FxQuote(pair="USDJPY", timestamp_utc=T_CLOSE, bid=151.00, ask=151.02),
            ],
            "USDCAD": [
                FxQuote(pair="USDCAD", timestamp_utc=T_OPEN, bid=1.3500, ask=1.3502),
                FxQuote(pair="USDCAD", timestamp_utc=T_CLOSE, bid=1.3478, ask=1.3480),
            ],
        },
        tolerance_seconds=60.0,
    )


def make_exec_model(graph):
    return FxExecutionCostModel(
        model_id=CostModelId("FX_BID_ASK_V1"),
        conversion=graph,
        max_quote_age_seconds=60.0,
    )


def fill_ctx(bid, ask, timestamp, commission_quote):
    return {
        "bid": bid,
        "ask": ask,
        "quote_timestamp_utc": timestamp,
        "now_utc": timestamp,
        "commission_quote": commission_quote,
        "slippage_pips": 0.0,
        "impact_quote": 0.0,
    }


def make_carry():
    return FxRolloverCarry(
        schedule=RolloverSchedule(
            entries={
                ("EURUSD", "LONG"): RolloverLeg(value=0.5, units=SWAP_POINTS, quote_currency="USD"),
                ("EURUSD", "SHORT"): RolloverLeg(value=-0.7, units=SWAP_POINTS, quote_currency="USD"),
            },
            provenance=SYNTHETIC_TEST_ONLY,
        )
    )


# ================================================================================== #
# Case 1: EURUSD long round trip, quote currency USD, one rollover night.            #
#                                                                                    #
#   open  Thu 16:00 ET: BUY 10,000 @ ASK 1.1002 (bid 1.1000 / ask 1.1002)            #
#     spread cost = (1.1002 - 1.1000) * 10,000           = 2.00 USD                  #
#     commission                                     = 1.00 USD per side             #
#   close Fri 16:00 ET: SELL 10,000 @ BID 1.1010 (bid 1.1010 / ask 1.1012)           #
#     realized price PnL = (1.1010 - 1.1002) * 10,000    = +8.00 USD                 #
#     spread cost = (1.1012 - 1.1010) * 10,000           = 2.00 USD                  #
#   rollover: window crosses the Thu 17:00 ET roll, 1 night,                         #
#     +0.5 swap points * pip 0.0001 * 10,000             = +0.50 USD                 #
#   ending = 100,000 + 8.00 + 0.50 - 2.00 (commissions) - 4.00 (spread)              #
#          = 100,002.50                                                              #
# ================================================================================== #
def test_eurusd_long_round_trip_identity_closes():
    graph = make_graph()
    model = make_exec_model(graph)
    carry = make_carry()

    open_est = model.estimate(
        symbol="EURUSD", side="BUY", quantity=10_000, price=1.1002,
        context=fill_ctx(1.1000, 1.1002, T_OPEN, commission_quote=1.00),
    )
    assert open_est.price == pytest.approx(1.1002)
    assert open_est.spread_cost == pytest.approx(2.00, abs=1e-12)
    assert open_est.commission == pytest.approx(1.00, abs=1e-12)

    close_est = model.estimate(
        symbol="EURUSD", side=close_side_for("LONG"), quantity=10_000, price=1.1010,
        context=fill_ctx(1.1010, 1.1012, T_CLOSE, commission_quote=1.00),
    )
    assert close_est.price == pytest.approx(1.1010)

    realized = price_pnl_quote(
        position_side="LONG",
        open_fill_price=open_est.price,
        close_fill_price=close_est.price,
        quantity=10_000,
    )
    assert realized == pytest.approx(8.00, abs=1e-12)  # (1.1010 - 1.1002) * 10,000

    rollover_lines = carry.cashflows(
        instrument_symbol="EURUSD",
        position_qty=10_000,
        interval_start_utc=T_OPEN,
        interval_end_utc=T_CLOSE,
        context={"holidays": set(), "pip_size": 0.0001},
    )
    assert len(rollover_lines) == 1
    assert rollover_lines[0].amount == pytest.approx(0.50, abs=1e-12)  # 0.5 * 0.0001 * 10,000
    rollover_usd = rollover_usd_total(rollover_lines, graph=graph)
    assert rollover_usd == pytest.approx(0.50, abs=1e-12)

    commissions_usd = open_est.commission + close_est.commission  # 2.00
    spread_usd = open_est.spread_cost + close_est.spread_cost  # 4.00
    starting_usd = 100_000.00
    ending_usd = math.fsum((starting_usd, realized, rollover_usd, -commissions_usd, -spread_usd))
    assert ending_usd == pytest.approx(100_002.50, abs=1e-9)

    statement = round_trip_statement(
        starting_usd=starting_usd,
        ending_usd=ending_usd,
        realized_price_pnl_quote_amount=realized,
        pair="EURUSD",
        close_as_of=T_CLOSE,
        graph=graph,
        rollover_lines=rollover_lines,
        commissions_usd=commissions_usd,
        spread_usd=spread_usd,
        slippage_usd=0.0,
        market_impact_usd=0.0,
        rejection_costs_usd=0.0,
        explicit_interest_usd=0.0,
        terminal_pnl_usd=0.0,
        conversion_side="MID",
    )
    residual = check_identity(statement, tolerance=TOL)
    assert abs(residual) <= TOL
    assert identity_residual(statement) == pytest.approx(0.0, abs=TOL)


def test_identity_mismatch_is_detected():
    graph = make_graph()
    statement = FxAccountingStatement(
        starting_usd=100_000.0,
        ending_usd=100_002.50,
        realized_price_pnl_usd=8.0,
        terminal_pnl_usd=0.0,
        rollover_cashflows_usd=0.5,
        explicit_interest_usd=0.0,
        commissions_usd=2.0,
        spread_usd=4.0,
        slippage_usd=0.0,
        market_impact_usd=0.0,
        rejection_costs_usd=0.0,
    )
    assert abs(check_identity(statement, tolerance=TOL)) <= TOL
    # perturb one term by +1.00 USD -> the identity must fail loudly
    perturbed = statement.with_ending_usd(100_003.50)
    with pytest.raises(AccountingIdentityError) as excinfo:
        check_identity(perturbed, tolerance=TOL)
    assert excinfo.value.residual == pytest.approx(1.0, abs=1e-9)


def test_missing_identity_term_blocks():
    statement = FxAccountingStatement(
        starting_usd=100_000.0,
        ending_usd=100_002.50,
        realized_price_pnl_usd=8.0,
        terminal_pnl_usd=0.0,
        rollover_cashflows_usd=None,  # unavailable: must block, never default
        explicit_interest_usd=0.0,
        commissions_usd=2.0,
        spread_usd=4.0,
        slippage_usd=0.0,
        market_impact_usd=0.0,
        rejection_costs_usd=0.0,
    )
    with pytest.raises(MissingAccountingInput):
        statement.residual()
    with pytest.raises(MissingAccountingInput):
        check_identity(statement, tolerance=TOL)


# ================================================================================== #
# Case 2: USDJPY long round trip, pip 0.01 arithmetic, JPY components converted at    #
# the closing-timestamp quote (price PnL) and at each fill's own quote (costs).       #
#                                                                                    #
#   qty 100,000 USD base; pip 0.01 -> pip value = 0.01 * 100,000 = 1,000 JPY/pip     #
#   open  @ ASK 150.00 (bid 149.98): spread = 0.02 * 100,000 = 2,000 JPY             #
#   close @ BID 151.00 (ask 151.02): spread = 0.02 * 100,000 = 2,000 JPY             #
#   realized = (151.00 - 150.00) * 100,000 = 100 pips * 1,000 JPY = +100,000 JPY     #
#   commission 500 JPY per side                                                      #
#   closing quote mid = (151.00 + 151.02)/2 = 151.01 JPY per USD                     #
# ================================================================================== #
def test_usdjpy_round_trip_jpy_math_then_usd_conversion():
    graph = make_graph()
    model = make_exec_model(graph)

    open_est = model.estimate(
        symbol="USDJPY", side="BUY", quantity=100_000, price=150.00,
        context=fill_ctx(149.98, 150.00, T_OPEN, commission_quote=500.0),
    )
    close_est = model.estimate(
        symbol="USDJPY", side=close_side_for("LONG"), quantity=100_000, price=151.00,
        context=fill_ctx(151.00, 151.02, T_CLOSE, commission_quote=500.0),
    )

    realized_jpy = (151.00 - 150.00) * 100_000
    assert realized_jpy == pytest.approx(100_000.0, abs=1e-6)  # 100 pips * 1,000 JPY pip value
    spread_open_jpy = (150.00 - 149.98) * 100_000
    spread_close_jpy = (151.02 - 151.00) * 100_000
    # hand values: 0.02 * 100,000 = 2,000 JPY each (binary FP noise ~1e-9)
    assert spread_open_jpy == pytest.approx(2_000.0, abs=1e-6)
    assert spread_close_jpy == pytest.approx(2_000.0, abs=1e-6)

    # price PnL converts at the closing-timestamp quote (inverse pair: / 151.01)
    realized_usd = graph.convert(realized_jpy, "JPY", "USD", T_CLOSE)
    assert realized_usd == pytest.approx(100_000 / 151.01, rel=1e-12)

    # costs converted at each fill's own timestamp (open mid 149.99, close mid 151.01)
    assert open_est.spread_cost == pytest.approx(2_000 / 149.99, rel=1e-12)
    assert close_est.spread_cost == pytest.approx(2_000 / 151.01, rel=1e-12)
    commissions_usd = open_est.commission + close_est.commission
    spread_usd = open_est.spread_cost + close_est.spread_cost
    assert commissions_usd == pytest.approx(500 / 149.99 + 500 / 151.01, rel=1e-12)

    starting_usd = 100_000.0
    # Costs convert at their own fill timestamps (open costs at 149.99, close
    # costs at 151.01), so ending cannot collapse into one net-JPY/rate pair:
    #   ending = 100,000 + 100,000/151.01 - (500+2,000)/149.99 - (500+2,000)/151.01
    ending_usd = math.fsum((starting_usd, realized_usd, -commissions_usd, -spread_usd))
    assert ending_usd == pytest.approx(
        100_000.0 + 100_000 / 151.01 - 2_500 / 149.99 - 2_500 / 151.01,
        rel=1e-12,
    )

    statement = round_trip_statement(
        starting_usd=starting_usd,
        ending_usd=ending_usd,
        realized_price_pnl_quote_amount=realized_jpy,
        pair="USDJPY",
        close_as_of=T_CLOSE,
        graph=graph,
        rollover_lines=(),
        commissions_usd=commissions_usd,
        spread_usd=spread_usd,
        slippage_usd=0.0,
        market_impact_usd=0.0,
        rejection_costs_usd=0.0,
        explicit_interest_usd=0.0,
        terminal_pnl_usd=0.0,
        conversion_side="MID",
    )
    assert abs(check_identity(statement, tolerance=TOL)) <= TOL


# ================================================================================== #
# Case 3: USDCAD SHORT round trip through the inverse-pair conversion branch.         #
#                                                                                    #
#   qty 100,000 USD base; open SELL @ BID 1.3500 (bid 1.3500 / ask 1.3502)           #
#     spread = 0.0002 * 100,000 = 20.00 CAD; commission 10.00 CAD                    #
#   close BUY @ ASK 1.3480 (bid 1.3478 / ask 1.3480)                                 #
#     realized = (open_bid - close_ask) * qty = (1.3500 - 1.3480)*100,000 = +200 CAD #
#     spread = 20.00 CAD; commission 10.00 CAD                                       #
#   closing mid = (1.3478 + 1.3480)/2 = 1.3479; CAD -> USD = 1 / 1.3479 (inversion)  #
# ================================================================================== #
def test_usdcad_short_round_trip_inverse_pair():
    graph = make_graph()
    model = make_exec_model(graph)

    open_est = model.estimate(
        symbol="USDCAD", side="SELL", quantity=100_000, price=1.3500,
        context=fill_ctx(1.3500, 1.3502, T_OPEN, commission_quote=10.0),
    )
    close_est = model.estimate(
        symbol="USDCAD", side=close_side_for("SHORT"), quantity=100_000, price=1.3480,
        context=fill_ctx(1.3478, 1.3480, T_CLOSE, commission_quote=10.0),
    )
    assert open_est.price == pytest.approx(1.3500)
    assert close_est.price == pytest.approx(1.3480)  # short close buys at ASK

    realized_cad = price_pnl_quote(
        position_side="SHORT",
        open_fill_price=open_est.price,
        close_fill_price=close_est.price,
        quantity=100_000,
    )
    assert realized_cad == pytest.approx(200.0, abs=1e-9)  # (1.3500 - 1.3480) * 100,000

    # inverse-pair branch: CAD -> USD multiplies by 1 / USDCAD mid
    assert graph.rate("CAD", "USD", T_CLOSE) == pytest.approx(1 / 1.3479, rel=1e-12)
    realized_usd = graph.convert(realized_cad, "CAD", "USD", T_CLOSE)
    assert realized_usd == pytest.approx(200 / 1.3479, rel=1e-12)

    commissions_usd = open_est.commission + close_est.commission
    spread_usd = open_est.spread_cost + close_est.spread_cost
    assert spread_usd == pytest.approx(20 / 1.3501 + 20 / 1.3479, rel=1e-12)

    starting_usd = 100_000.0
    # ending = 100,000 + 200/1.3479 (realized, closing quote)
    #          - (10+20)/1.3501 (open-side costs, open quote)
    #          - (10+20)/1.3479 (close-side costs, closing quote)
    ending_usd = math.fsum((starting_usd, realized_usd, -commissions_usd, -spread_usd))
    assert ending_usd == pytest.approx(100_000.0 + 170 / 1.3479 - 30 / 1.3501, rel=1e-12)

    statement = round_trip_statement(
        starting_usd=starting_usd,
        ending_usd=ending_usd,
        realized_price_pnl_quote_amount=realized_cad,
        pair="USDCAD",
        close_as_of=T_CLOSE,
        graph=graph,
        rollover_lines=(),
        commissions_usd=commissions_usd,
        spread_usd=spread_usd,
        slippage_usd=0.0,
        market_impact_usd=0.0,
        rejection_costs_usd=0.0,
        explicit_interest_usd=0.0,
        terminal_pnl_usd=0.0,
        conversion_side="MID",
    )
    assert abs(check_identity(statement, tolerance=TOL)) <= TOL


# --- exposure by underlying currency ------------------------------------------------ #
def test_exposure_reported_per_underlying_currency():
    graph = make_graph()
    # after buying 10,000 EURUSD at the 1.1002 ASK:
    #   long  EUR  +10,000
    #   short USD  -10,000 * 1.1002 = -11,002.00
    exposures = currency_exposures(pair="EURUSD", position_qty=10_000, fill_price=1.1002)
    assert exposures[0].currency == "EUR" and exposures[0].native_amount == pytest.approx(10_000.0)
    assert exposures[1].currency == "USD" and exposures[1].native_amount == pytest.approx(-11_002.0)

    usd_view = exposure_usd_by_currency(exposures, graph=graph, as_of=T_OPEN)
    # open-time EURUSD mid = 1.1001 -> EUR leg = 10,000 * 1.1001 = 11,001.00 USD
    assert usd_view["EUR"] == pytest.approx(11_001.0, rel=1e-12)
    assert usd_view["USD"] == pytest.approx(-11_002.0, rel=1e-12)
    # net USD exposure right after opening = -1.00 = exactly the spread just paid
    assert math.fsum(usd_view.values()) == pytest.approx(-1.0, abs=1e-9)


# --- missing rollover schedule blocks accounting (fail closed) ----------------------- #
def test_missing_rollover_schedule_blocks_accounting():
    graph = make_graph()
    carry_without_eurusd = FxRolloverCarry(
        schedule=RolloverSchedule(
            entries={
                ("USDJPY", "LONG"): RolloverLeg(value=0.3, units=SWAP_POINTS, quote_currency="JPY"),
            },
            provenance=SYNTHETIC_TEST_ONLY,
        )
    )
    with pytest.raises(RolloverScheduleUnavailable):
        # the accounting pipeline cannot produce its rollover term: the raise
        # propagates and no statement is ever assembled
        rollover_lines = carry_without_eurusd.cashflows(
            instrument_symbol="EURUSD",
            position_qty=10_000,
            interval_start_utc=T_OPEN,
            interval_end_utc=T_CLOSE,
            context={"holidays": set(), "pip_size": 0.0001},
        )
        round_trip_statement(
            starting_usd=100_000.0,
            ending_usd=100_002.50,
            realized_price_pnl_quote_amount=8.0,
            pair="EURUSD",
            close_as_of=T_CLOSE,
            graph=graph,
            rollover_lines=rollover_lines,
            commissions_usd=2.0,
            spread_usd=4.0,
            slippage_usd=0.0,
            market_impact_usd=0.0,
            rejection_costs_usd=0.0,
            explicit_interest_usd=0.0,
            terminal_pnl_usd=0.0,
            conversion_side="MID",
        )


def test_explicit_zero_terms_close_exactly():
    # flat account: all terms explicitly zero -> identity closes at 0.0
    statement = FxAccountingStatement(
        starting_usd=50_000.0,
        ending_usd=50_000.0,
        realized_price_pnl_usd=0.0,
        terminal_pnl_usd=0.0,
        rollover_cashflows_usd=0.0,
        explicit_interest_usd=0.0,
        commissions_usd=0.0,
        spread_usd=0.0,
        slippage_usd=0.0,
        market_impact_usd=0.0,
        rejection_costs_usd=0.0,
    )
    assert check_identity(statement, tolerance=TOL) == 0.0
