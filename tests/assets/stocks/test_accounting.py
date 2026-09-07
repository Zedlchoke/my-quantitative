"""SD3 — canonical stock accounting identity tests (owner: A5).

Every golden number below is HAND-COMPUTED and written literally, with the
arithmetic shown in comments.  Floats close within the declared tolerance
(``FLOAT_IDENTITY_TOLERANCE_USD``); the exact-Decimal path closes to
``Decimal("0")``.  The suite writes nothing to the repository.
"""

from __future__ import annotations

import dataclasses
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

from research.assets.stocks.accounting import (
    CostBreakdown,
    DividendEvent,
    FillRecord,
    FLOAT_IDENTITY_TOLERANCE_USD,
    IdentityBreakError,
    IdentityLedger,
    IdentityTerms,
    ObservableEvent,
    OrderRejection,
    compute_borrow_fee,
    last_executable_event,
    assert_identity_exact,
    identity_residual_exact,
)
from research.assets.stocks.execution import (
    CommissionSchedule,
    EquityExecutionModel,
    ExecutionDecision,
    ImpactModel,
    SpreadPolicy,
)
from research.assets.stocks.portfolio import (
    OrderIntent,
    SharedCapitalReplay,
    positive_pnl_shares,
)

REPO_ROOT = Path(__file__).resolve().parents[3]

T0 = "2026-03-02T14:30:00+00:00"
T1 = "2026-03-03T14:30:00+00:00"


def _fill(side: str, quantity: float, price: float, *, commission: float, spread: float,
          slippage: float = 0.0, impact: float = 0.0, timestamp: str = T0, symbol: str = "AAPL") -> FillRecord:
    return FillRecord(
        symbol=symbol,
        side=side,
        quantity=quantity,
        price=price,
        timestamp_utc=timestamp,
        cost=CostBreakdown(
            commission=commission, spread=spread, slippage=slippage, market_impact=impact
        ),
    )


# --- golden 1: long round trip, commission + spread, identity to the cent ---- #
def test_long_round_trip_identity_closes_to_the_cent():
    ledger = IdentityLedger(starting_equity=10_000.00)

    # Entry: BUY 100 @ 50.01 (ask), commission 1.00, spread = 100 * (50.01-49.99)/2 = 1.00
    ledger.apply_fill(_fill("BUY", 100, 50.01, commission=1.00, spread=1.00))
    # cash = 10000 - 100*50.01 - (1.00 + 1.00) = 10000 - 5001 - 2 = 4997.00
    assert ledger.cash == pytest.approx(4997.00, abs=1e-6)

    # Exit: SELL 100 @ 50.99 (bid), commission 1.00, spread 1.00
    # realized = (50.99 - 50.01) * 100 = 98.00
    ledger.apply_fill(_fill("SELL", 100, 50.99, commission=1.00, spread=1.00, timestamp=T1))
    # cash = 4997 + 100*50.99 - 2 = 4997 + 5099 - 2 = 10094.00
    assert ledger.cash == pytest.approx(10094.00, abs=1e-6)

    terms = ledger.identity_terms()
    # delta = 10094 - 10000 = 94.00 = realized 98.00 - commissions 2.00 - spread 2.00
    assert terms.realized_price_pnl == pytest.approx(98.00, abs=1e-9)
    assert terms.commissions == pytest.approx(2.00, abs=1e-12)
    assert terms.spread == pytest.approx(2.00, abs=1e-12)
    assert terms.ending_equity - terms.starting_equity == pytest.approx(94.00, abs=1e-6)
    # Position is flat: terminal PnL and every other term are exactly zero.
    assert terms.terminal_pnl == 0.0
    assert terms.short_borrow_fees == 0.0
    assert terms.short_dividend_liability == 0.0
    assert terms.rejection_costs == 0.0
    terms.assert_closes(FLOAT_IDENTITY_TOLERANCE_USD)  # frozen tolerance
    assert abs(terms.residual) <= 1e-9


# --- golden 2: terminal valuation on the LAST EXECUTABLE event only ---------- #
def test_terminal_valuation_uses_last_executable_event_only():
    ledger = IdentityLedger(starting_equity=10_000.00)
    ledger.apply_fill(_fill("BUY", 100, 50.01, commission=1.00, spread=1.00))
    # cash = 10000 - 5001 - 2 = 4997.00 ; open long 100 @ avg 50.01

    events = (
        ObservableEvent(timestamp_utc=T0, price=52.00, executable=True),
        # A later print that is NOT executable (e.g. halted/closed) must be ignored:
        ObservableEvent(timestamp_utc=T1, price=55.00, executable=False),
    )
    terminal = ledger.finalize_terminal("AAPL", events)
    assert terminal.price == 52.00  # last EXECUTABLE, not simply last

    # terminal_pnl = 100 * (52.00 - 50.01) = 199.00
    terms = ledger.identity_terms()
    assert terms.terminal_pnl == pytest.approx(199.00, abs=1e-6)
    # ending equity = cash 4997 + 100*52 = 10197 ; delta = 197 = 199 - (1 + 1)
    assert terms.ending_equity == pytest.approx(10197.00, abs=1e-6)
    assert terms.ending_equity - terms.starting_equity == pytest.approx(197.00, abs=1e-6)
    terms.assert_closes(FLOAT_IDENTITY_TOLERANCE_USD)


def test_terminal_valuation_fails_closed_without_executable_event():
    ledger = IdentityLedger(starting_equity=10_000.00)
    ledger.apply_fill(_fill("BUY", 100, 50.01, commission=1.00, spread=1.00))
    only_halted = (ObservableEvent(timestamp_utc=T1, price=55.00, executable=False),)
    with pytest.raises(ValueError, match="no executable event"):
        last_executable_event(only_halted)
    with pytest.raises(ValueError):
        last_executable_event(())
    # The mark-to-market equity also fails closed while no mark is attached:
    with pytest.raises(ValueError, match="no terminal mark"):
        ledger.identity_terms()


# --- golden 3: short round trip identity (no carry yet — see SD4 file) ------- #
def test_short_round_trip_identity_closes():
    ledger = IdentityLedger(starting_equity=10_000.00)

    # Entry: SELL 100 @ 49.99 (bid), commission 1.00, spread 1.00
    ledger.apply_fill(_fill("SELL", 100, 49.99, commission=1.00, spread=1.00))
    # cash = 10000 + 100*49.99 - 2 = 10000 + 4999 - 2 = 14997.00 ; short avg 49.99
    assert ledger.cash == pytest.approx(14997.00, abs=1e-6)

    # Cover: BUY 100 @ 48.01 (ask), commission 1.00, spread 1.00
    # realized = (49.99 - 48.01) * 100 = 198.00
    ledger.apply_fill(_fill("BUY", 100, 48.01, commission=1.00, spread=1.00, timestamp=T1))
    # cash = 14997 - 100*48.01 - 2 = 14997 - 4801 - 2 = 10194.00
    assert ledger.cash == pytest.approx(10194.00, abs=1e-6)

    terms = ledger.identity_terms()
    # delta = 194.00 = realized 198.00 - commissions 2.00 - spread 2.00
    assert terms.realized_price_pnl == pytest.approx(198.00, abs=1e-9)
    assert terms.ending_equity - terms.starting_equity == pytest.approx(194.00, abs=1e-6)
    terms.assert_closes(FLOAT_IDENTITY_TOLERANCE_USD)


# --- golden 4: EXACT Decimal path for goldens -------------------------------- #
def test_exact_decimal_identity_closes_to_exactly_zero():
    exact_terms = {
        "starting_equity": "10000",
        "ending_equity": "10094",
        "realized_price_pnl": "98",
        "terminal_pnl": "0",
        "cash_dividends": "0",
        "commissions": "2",
        "spread": "2",
        "slippage": "0",
        "market_impact": "0",
        "short_borrow_fees": "0",
        "short_dividend_liability": "0",
        "rejection_costs": "0",
    }
    # lhs = 10094 - 10000 = 94 ; rhs = 98 - 2 - 2 = 94 -> residual EXACTLY 0
    assert identity_residual_exact(exact_terms) == Decimal("0")
    assert assert_identity_exact(exact_terms) == Decimal("0")

    off_by_a_penny = dict(exact_terms, ending_equity="10093.99")
    with pytest.raises(AssertionError, match="EXACT IDENTITY BREAK"):
        assert_identity_exact(off_by_a_penny)


# --- golden 5: rejection with a venue fee closes through rejection_costs ----- #
def test_rejection_with_venue_fee_closes_through_rejection_costs():
    ledger = IdentityLedger(starting_equity=10_000.00)
    ledger.record_rejection(
        OrderRejection(
            symbol="AAPL", side="BUY", quantity=100, reason="VENUE_REJECT",
            timestamp_utc=T0, cost=1.00,
        )
    )
    assert ledger.fills == ()
    assert len(ledger.rejections) == 1
    # cash = 10000 - 1.00 (venue reject fee) = 9999.00 ; delta = -1 = -rejection_costs
    terms = ledger.identity_terms()
    assert terms.rejection_costs == 1.00
    assert terms.ending_equity == pytest.approx(9999.00, abs=1e-12)
    terms.assert_closes(FLOAT_IDENTITY_TOLERANCE_USD)


def test_zero_cost_rejection_changes_nothing():
    ledger = IdentityLedger(starting_equity=10_000.00)
    ledger.record_rejection(
        OrderRejection(
            symbol="AAPL", side="SELL", quantity=100, reason="NO_LOCATE",
            timestamp_utc=T0, cost=0.0,
        )
    )
    assert ledger.cash == 10_000.0
    terms = ledger.identity_terms()
    assert terms.ending_equity - terms.starting_equity == 0.0
    terms.assert_closes()


# --- identity hygiene --------------------------------------------------------- #
def test_corrupted_ledger_breaks_identity_loudly():
    ledger = IdentityLedger(starting_equity=10_000.00)
    ledger.apply_fill(_fill("BUY", 100, 50.01, commission=1.00, spread=1.00))
    ledger.finalize_terminal("AAPL", (ObservableEvent(timestamp_utc=T1, price=52.00, executable=True),))
    terms = ledger.identity_terms()
    assert terms.ending_equity - terms.starting_equity == pytest.approx(197.0, abs=1e-6)
    ledger.cash += 100.0  # tamper: a missing ledger row
    with pytest.raises(IdentityBreakError, match="IDENTITY BREAK"):
        ledger.identity_terms().assert_closes(FLOAT_IDENTITY_TOLERANCE_USD)


def test_identity_terms_reject_negative_costs_and_nonfinite():
    with pytest.raises(ValueError, match="commissions must be >= 0"):
        IdentityTerms(
            starting_equity=100.0, ending_equity=100.0, realized_price_pnl=0.0,
            terminal_pnl=0.0, cash_dividends=0.0, commissions=-1.0, spread=0.0,
            slippage=0.0, market_impact=0.0, short_borrow_fees=0.0,
            short_dividend_liability=0.0, rejection_costs=0.0,
        )
    with pytest.raises(ValueError, match="finite"):
        IdentityTerms(
            starting_equity=100.0, ending_equity=float("inf"), realized_price_pnl=0.0,
            terminal_pnl=0.0, cash_dividends=0.0, commissions=0.0, spread=0.0,
            slippage=0.0, market_impact=0.0, short_borrow_fees=0.0,
            short_dividend_liability=0.0, rejection_costs=0.0,
        )


def test_average_cost_blend_and_cross_realization():
    ledger = IdentityLedger(starting_equity=10_000.00)
    # BUY 100 @ 50 then BUY 100 @ 60 (no costs): avg = (100*50 + 100*60)/200 = 55
    ledger.apply_fill(_fill("BUY", 100, 50.0, commission=0.0, spread=0.0))
    ledger.apply_fill(_fill("BUY", 100, 60.0, commission=0.0, spread=0.0, timestamp=T1))
    assert ledger.position_qty("AAPL") == 200.0
    # SELL 150 @ 70: realized = (70 - 55) * 150 = 2250 ; remaining long 50 @ avg 55
    ledger.apply_fill(_fill("SELL", 150, 70.0, commission=0.0, spread=0.0, timestamp=T1))
    assert ledger.position_qty("AAPL") == 50.0
    assert ledger.bucket("realized_price_pnl") == pytest.approx(2250.0, abs=1e-9)
    # SELL 100 @ 40: close 50 @ avg 55 (realized (40-55)*50 = -750), cross short 50 @ 40
    ledger.apply_fill(_fill("SELL", 100, 40.0, commission=0.0, spread=0.0, timestamp=T1))
    assert ledger.position_qty("AAPL") == -50.0
    # total realized = 2250 - 750 = 1500
    assert ledger.bucket("realized_price_pnl") == pytest.approx(1500.0, abs=1e-9)
    # Open short 50 @ avg 40 has no mark yet: reading identity terms now fails closed.
    # Mark at 40 (executable) -> terminal = (-50)*(40-40) = 0.
    ledger.finalize_terminal("AAPL", (ObservableEvent(timestamp_utc=T1, price=40.0, executable=True),))
    terms = ledger.identity_terms()
    assert terms.terminal_pnl == pytest.approx(0.0, abs=1e-9)
    # Short sale PROCEEDS stay in cash: cash = 10000 - 5000 - 6000 + 10500 + 4000 = 13500
    assert ledger.cash == pytest.approx(13500.0, abs=1e-9)
    # ending equity = cash 13500 + (-50)*40 = 11500 ; delta = 1500 = realized 1500
    assert terms.ending_equity == pytest.approx(11500.0, abs=1e-6)
    assert terms.ending_equity - terms.starting_equity == pytest.approx(1500.0, abs=1e-6)
    terms.assert_closes(FLOAT_IDENTITY_TOLERANCE_USD)


def test_dividend_to_flat_position_books_nothing():
    ledger = IdentityLedger(starting_equity=10_000.00)
    line = ledger.apply_dividend(DividendEvent(symbol="AAPL", dividend_per_share=0.50, ex_date_utc=T0))
    assert line is None
    assert ledger.cash == 10_000.0
    assert ledger.identity_terms().cash_dividends == 0.0


def test_borrow_fee_helper_rejects_bad_day_count_basis():
    # fee = price * quantity * rate * days / basis ; a zero basis fails closed
    with pytest.raises(ValueError, match="day_count_basis"):
        compute_borrow_fee(price=50.0, quantity=100.0, annual_rate=0.036, days=10.0, day_count_basis=0)


# --- the suite itself writes nothing to the repository ------------------------- #
def test_importing_stocks_modules_writes_nothing_to_the_worktree():
    before = subprocess.run(
        ["git", "status", "--porcelain=v1"], cwd=REPO_ROOT,
        capture_output=True, text=True, check=True,
    ).stdout
    probe = (
        "import importlib\n"
        "importlib.import_module('research.assets.stocks.accounting')\n"
        "importlib.import_module('research.assets.stocks.execution')\n"
        "importlib.import_module('research.assets.stocks.portfolio')\n"
        "print('imported-ok')\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", probe], cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    )
    assert "imported-ok" in completed.stdout
    after = subprocess.run(
        ["git", "status", "--porcelain=v1"], cwd=REPO_ROOT,
        capture_output=True, text=True, check=True,
    ).stdout
    assert after == before


def test_cost_breakdown_is_frozen_and_validated():
    cost = CostBreakdown(commission=1.0, spread=0.0, slippage=0.0, market_impact=0.0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        cost.commission = 2.0  # type: ignore[misc]
    with pytest.raises(ValueError):
        CostBreakdown(commission=-1.0, spread=0.0, slippage=0.0, market_impact=0.0)
    assert CostBreakdown.zero().total() == 0.0


# --- portfolio: shared-capital replay and concentration ------------------------- #
def _model() -> EquityExecutionModel:
    return EquityExecutionModel(
        cost_model_id="US_EQUITY_REPLAY_TEST_V1",
        commission=CommissionSchedule(per_share=0.0, min_per_order=1.00),
        spread=SpreadPolicy(proxy_spread_bps=None),
        impact=ImpactModel(coefficient=0.0, max_participation=0.01),
        slippage_bps=0.0,
        currency="USD",
    )


def _attempt(model, symbol, side, quantity, ref, bid, ask, timestamp):
    return model.attempt_fill(
        symbol=symbol, side=side, quantity=quantity, reference_price=ref,
        timestamp_utc=timestamp, session_open=True, halted=False, bid=bid, ask=ask,
    )


def test_two_arms_share_one_usd_account_and_identity_closes_at_both_levels():
    replay = SharedCapitalReplay(starting_equity=100_000.00)
    replay.register_arm("ARM_TREND")
    replay.register_arm("ARM_MR")
    model = _model()

    # Arm TREND: BUY 100 AAPL @ 50.00 (comm 1.00) and 100 MSFT... kept distinct:
    d1 = _attempt(model, "AAPL", "BUY", 100, 50.00, 49.995, 50.005, T0)
    assert d1.status == "FILLED"  # quotes straddle 50.00: half-spread 0.005/share
    replay.book_decision("ARM_TREND", d1)
    d2 = _attempt(model, "MSFT", "BUY", 100, 20.00, 19.995, 20.005, T0)
    replay.book_decision("ARM_TREND", d2)
    d3 = _attempt(model, "NVDA", "BUY", 100, 10.00, 9.995, 10.005, T0)
    replay.book_decision("ARM_TREND", d3)

    # Arm MR: BUY 200 AAPL @ 10.00 (comm 1.00) — same market, same cash pool.
    d4 = _attempt(model, "SPY", "BUY", 200, 10.00, 9.995, 10.005, T0)
    replay.book_decision("ARM_MR", d4)

    # Shared cash = 100000 - (100*50.005 + 1 + 0.5) - (100*20.005 + 1 + 0.5)
    #             - (100*10.005 + 1 + 0.5) - (200*10.005 + 1 + 1)
    #             = 100000 - 5002 - 2002 - 1002 - 2003 = 89991.00
    # (commission = min 1.00 per order; spread = qty * half-spread 0.005)
    assert replay.shared_cash() == pytest.approx(89_991.00, abs=1e-6)

    # Terminal marks: AAPL 55, MSFT 19, NVDA 11, SPY 11 (all executable).
    marks = {
        "AAPL": ObservableEvent(timestamp_utc=T1, price=55.00, executable=True),
        "MSFT": ObservableEvent(timestamp_utc=T1, price=19.00, executable=True),
        "NVDA": ObservableEvent(timestamp_utc=T1, price=11.00, executable=True),
        "SPY": ObservableEvent(timestamp_utc=T1, price=11.00, executable=True),
    }
    replay.finalize_terminal(marks)

    trend = replay.arm_terms("ARM_TREND")
    # TREND terminal = 100*(55-50.005) + 100*(19-20.005) + 100*(11-10.005)
    #               = 499.50 - 100.50 + 99.50 = 498.50 ; commissions 3.00 ; spread 1.50
    assert trend.terminal_pnl == pytest.approx(498.50, abs=1e-6)
    assert trend.commissions == pytest.approx(3.00, abs=1e-12)
    assert trend.spread == pytest.approx(1.50, abs=1e-9)
    # TREND ending = -8006 + 5500 + 1900 + 1100 = 494.00 = 498.50 - 3.00 - 1.50
    assert trend.ending_equity == pytest.approx(494.00, abs=1e-6)

    mr = replay.arm_terms("ARM_MR")
    # MR terminal = 200*(11-10.005) = 199.00 ; commissions 1.00 ; spread 1.00
    # -> ending = -2003 + 2200 = 197.00
    assert mr.terminal_pnl == pytest.approx(199.00, abs=1e-6)
    assert mr.ending_equity == pytest.approx(197.00, abs=1e-6)

    account = replay.account_terms()
    # account ending = 100000 + 494.00 + 197.00 = 100691.00
    # delta = 691.00 = terminal 697.50 - commissions 4.00 - spread 2.50
    assert account.ending_equity == pytest.approx(100_691.00, abs=1e-6)
    assert account.terminal_pnl == pytest.approx(697.50, abs=1e-6)
    assert account.commissions == pytest.approx(4.00, abs=1e-12)
    replay.assert_closed(FLOAT_IDENTITY_TOLERANCE_USD)  # per-arm AND account


def test_shared_capital_submit_intent_rejects_short_without_locate():
    replay = SharedCapitalReplay(starting_equity=10_000.00)
    replay.register_arm("ARM_A")
    model = _model()
    decision = replay.submit_intent(
        "ARM_A", OrderIntent(symbol="AAPL", side="SELL", quantity=100),
        model=model, reference_price=50.00, timestamp_utc=T0,
        session_open=True, halted=False, bid=49.99, ask=50.01,
        locate=None,  # short sale with NO locate record
    )
    assert decision.status == "NO_FILL" and decision.reason == "MISSING_LOCATE"
    assert replay.shared_cash() == 10_000.0
    replay.assert_closed()

    from research.assets.stocks.accounting import BorrowLocate
    unavailable = BorrowLocate(symbol="AAPL", as_of_utc=T0, available=False, annual_rate=None)
    decision = replay.submit_intent(
        "ARM_A", OrderIntent(symbol="AAPL", side="SELL", quantity=100),
        model=model, reference_price=50.00, timestamp_utc=T0,
        session_open=True, halted=False, bid=49.99, ask=50.01,
        locate=unavailable,
    )
    assert decision.status == "NO_FILL" and decision.reason == "NO_LOCATE"
    assert replay.shared_cash() == 10_000.0
    replay.assert_closed()


def test_shared_capital_locate_gated_short_then_cover_closes():
    replay = SharedCapitalReplay(starting_equity=10_000.00)
    replay.register_arm("ARM_A")
    model = _model()
    from research.assets.stocks.accounting import BorrowLocate, DividendEvent

    locate = BorrowLocate(symbol="AAPL", as_of_utc=T0, available=True, annual_rate=0.036)
    # SELL 100 @ 49.99 (bid): cash = 10000 + 4999 - (1.00 comm + 1.00 spread) = 14997.00
    d = replay.submit_intent(
        "ARM_A", OrderIntent(symbol="AAPL", side="SELL", quantity=100),
        model=model, reference_price=50.00, timestamp_utc=T0,
        session_open=True, halted=False, bid=49.99, ask=50.01, locate=locate,
    )
    assert d.status == "FILLED"
    assert replay.shared_cash() == pytest.approx(14_997.00, abs=1e-9)

    # Dividend while short: liability = 0.50 * 100 = 50.00 -> cash 14947.00
    replay.apply_dividend("ARM_A", DividendEvent(symbol="AAPL", dividend_per_share=0.50, ex_date_utc=T1))
    assert replay.shared_cash() == pytest.approx(14_947.00, abs=1e-9)

    # Cover BUY 100 @ 48.01 (ask): cash = 14947 - 4801 - 2 = 10144.00
    d = replay.submit_intent(
        "ARM_A", OrderIntent(symbol="AAPL", side="BUY", quantity=100),
        model=model, reference_price=48.00, timestamp_utc=T1,
        session_open=True, halted=False, bid=47.99, ask=48.01, locate=None,
    )
    assert d.status == "FILLED"
    assert replay.shared_cash() == pytest.approx(10_144.00, abs=1e-6)
    terms = replay.arm_terms("ARM_A")
    # delta = 10144 - 10000 = +144.00
    #       = realized (49.99 - 48.01) * 100 = 198.00 - commissions 2.00
    #         - spread 2.00 - dividend liability 50.00
    assert terms.realized_price_pnl == pytest.approx(198.00, abs=1e-9)
    assert terms.short_dividend_liability == pytest.approx(50.00, abs=1e-12)
    assert terms.ending_equity - 0.0 == pytest.approx(144.00, abs=1e-6)
    replay.assert_closed(FLOAT_IDENTITY_TOLERANCE_USD)


def test_concentration_shares_of_positive_pnl():
    # Hand-computed contributions (terms per symbol, all costs = commission 1.00):
    contributions = {
        "AAPL": {  # realized 0 + terminal 500 - 1 = +499
            "realized_price_pnl": 0.0, "terminal_pnl": 500.0, "cash_dividends": 0.0,
            "commissions": 1.0, "spread": 0.0, "slippage": 0.0, "market_impact": 0.0,
            "short_borrow_fees": 0.0, "short_dividend_liability": 0.0, "rejection_costs": 0.0,
        },
        "NVDA": {  # realized 0 + terminal 100 - 1 = +99
            "realized_price_pnl": 0.0, "terminal_pnl": 100.0, "cash_dividends": 0.0,
            "commissions": 1.0, "spread": 0.0, "slippage": 0.0, "market_impact": 0.0,
            "short_borrow_fees": 0.0, "short_dividend_liability": 0.0, "rejection_costs": 0.0,
        },
        "MSFT": {  # realized 0 + terminal -100 - 1 = -101 (not positive: excluded)
            "realized_price_pnl": 0.0, "terminal_pnl": -100.0, "cash_dividends": 0.0,
            "commissions": 1.0, "spread": 0.0, "slippage": 0.0, "market_impact": 0.0,
            "short_borrow_fees": 0.0, "short_dividend_liability": 0.0, "rejection_costs": 0.0,
        },
    }
    shares = positive_pnl_shares(contributions)
    # positive total = 499 + 99 = 598 ; AAPL 499/598, NVDA 99/598, MSFT absent
    assert set(shares) == {"AAPL", "NVDA"}
    assert shares["AAPL"] == pytest.approx(499 / 598, abs=1e-12)
    assert shares["NVDA"] == pytest.approx(99 / 598, abs=1e-12)
    assert sum(shares.values()) == pytest.approx(1.0, abs=1e-12)
    # Nothing positive -> empty (no division by zero):
    assert positive_pnl_shares({}) == {}


def test_concentration_through_the_replay_books():
    replay = SharedCapitalReplay(starting_equity=10_000.00)
    replay.register_arm("ARM_A")
    model = _model()
    for symbol, ref in (("AAPL", 50.00), ("NVDA", 10.00)):
        d = _attempt(model, symbol, "BUY", 100, ref, ref - 0.005, ref + 0.005, T0)
        replay.book_decision("ARM_A", d)
    replay.finalize_terminal({
        "AAPL": ObservableEvent(timestamp_utc=T1, price=55.00, executable=True),
        "NVDA": ObservableEvent(timestamp_utc=T1, price=11.00, executable=True),
    })
    shares = replay.arm_concentration("ARM_A")
    # AAPL: 100*(55-50.005) - 1.00 comm - 0.50 spread = 498.00
    # NVDA: 100*(11-10.005) - 1.00 comm - 0.50 spread = 98.00
    # positive total = 596.00 ; shares 498/596 and 98/596
    assert shares["AAPL"] == pytest.approx(498.00 / 596.00, abs=1e-9)
    assert shares["NVDA"] == pytest.approx(98.00 / 596.00, abs=1e-9)


def test_replay_rejects_unknown_arm_and_duplicate_registration():
    replay = SharedCapitalReplay(starting_equity=10_000.00)
    replay.register_arm("ARM_A")
    with pytest.raises(ValueError, match="already registered"):
        replay.register_arm("ARM_A")
    with pytest.raises(ValueError, match="unknown arm"):
        replay.arm_terms("ARM_B")
    with pytest.raises(ValueError, match="no arms"):
        SharedCapitalReplay(starting_equity=1.0).account_terms()


def test_replay_terminal_finalize_fails_closed_on_unmarked_open_position():
    replay = SharedCapitalReplay(starting_equity=10_000.00)
    replay.register_arm("ARM_A")
    d = _attempt(_model(), "AAPL", "BUY", 100, 50.00, 49.995, 50.005, T0)
    replay.book_decision("ARM_A", d)
    with pytest.raises(ValueError, match="terminal marks missing"):
        replay.finalize_terminal({})
