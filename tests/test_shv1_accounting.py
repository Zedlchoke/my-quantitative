"""Hand-computed deterministic accounting fixtures (plan G3).

Scenario (single symbol BTCUSDT, tick 0.10):
  start cash 100,000
  T0 buy 0.5 @ ref 80,000  -> fee 20.00, slip 0.05, fill 80,000.10
  T1 mark 81,000           -> unrealized 499.95, equity 100,479.95
  T2 funding +0.0001 @81k  -> long pays 4.05, equity 100,475.90
  T3 sell 0.5 @ ref 81,000 -> fee 20.25, slip 0.05, fill 80,999.90
                             realized 499.90, flat equity 100,455.60
Fill convention: buy fills at ref + 1 tick, sell at ref - 1 tick
(cost_regime_manifest slippage_model: 1 tick adverse per fill).
"""

import math

import pytest

from research.shadow_v1.accounting import (
    CURRENT_CONSERVATIVE_COST,
    LINEAGE_COST,
    BookCostParams,
    AccountingError,
    InsufficientCashError,
    MarkGapError,
    SleeveAccount,
)

TICK = 0.10

T0 = "2026-01-05T00:15:00Z"
T1 = "2026-01-06T00:00:00Z"
T2 = "2026-01-07T08:00:00Z"
T3 = "2026-01-12T00:15:00Z"


def make_account(starting_cash=100_000.0):
    return SleeveAccount(
        sleeve_id="sleeve_test",
        starting_cash=starting_cash,
        books={
            LINEAGE_COST: BookCostParams(fee_rate=0.0004, slippage_ticks=2.0),
            CURRENT_CONSERVATIVE_COST: BookCostParams(
                fee_rate=0.0005, slippage_ticks=1.0
            ),
        },
        primary_book=CURRENT_CONSERVATIVE_COST,
    )


def approx(a, b, tol=1e-7):
    assert math.isclose(a, b, rel_tol=1e-9, abs_tol=tol), f"{a!r} != {b!r}"


def test_buy_fill_charges_fee_and_slippage_exactly_once():
    acct = make_account()
    fill = acct.apply_fill("BTCUSDT", "buy", 0.5, 80_000.0, TICK, T0, fill_id="f1")
    approx(fill.fee, 20.00)          # 0.5 * 80,000 * 0.0005
    approx(fill.slippage_amount, 0.05)  # 0.5 * 1 tick * 0.10
    approx(fill.fill_price, 80_000.10)  # ref + 1 tick (buy)
    approx(acct.cash, 100_000.0 - 0.5 * 80_000.10 - 20.00)
    snap = acct.equity_snapshot(T0)
    assert snap.status == "OK"
    approx(snap.equity, 100_000.0 - 20.00 - 0.05)  # identity: fee+slip once
    assert acct.fill_count == 1
    assert acct.closed_position_count == 0


def test_equity_identity_and_unrealized_at_moved_mark():
    acct = make_account()
    acct.apply_fill("BTCUSDT", "buy", 0.5, 80_000.0, TICK, T0)
    acct.update_marks({"BTCUSDT": 81_000.0}, T1)
    snap = acct.equity_snapshot(T1)
    approx(snap.equity, 100_479.95)  # 99,979.95 + 0.5*(81,000-80,000.10)... = +500.00
    approx(acct.unrealized_pnl(), 499.95)  # 0.5 * (81,000 - 80,000.10)
    # cash + qty*mark identity
    approx(acct.cash + 0.5 * 81_000.0, snap.equity)


def test_close_realizes_pnl_and_identity_holds():
    acct = make_account()
    acct.apply_fill("BTCUSDT", "buy", 0.5, 80_000.0, TICK, T0)
    acct.update_marks({"BTCUSDT": 81_000.0}, T1)
    fill = acct.apply_fill("BTCUSDT", "sell", 0.5, 81_000.0, TICK, T3, fill_id="f2")
    approx(fill.fill_price, 80_999.90)  # ref - 1 tick (sell)
    approx(fill.fee, 20.25)  # 0.5 * 81,000 * 0.0005
    approx(acct.realized_pnl, 499.90)  # 0.5 * (80,999.90 - 80,000.10)
    assert acct.closed_position_count == 1
    snap = acct.equity_snapshot(T3)
    assert snap.status == "OK"
    # no funding in this scenario: 100,000 - 20 (fee1) + 499.90 (realized,
    # slippage embedded via fill prices) - 20.25 (fee2)
    approx(snap.equity, 100_459.65)
    approx(acct.books[CURRENT_CONSERVATIVE_COST].fee, 40.25)
    approx(acct.books[CURRENT_CONSERVATIVE_COST].slippage, 0.10)


def test_funding_sign_and_once_booking():
    acct = make_account()
    acct.apply_fill("BTCUSDT", "buy", 0.5, 80_000.0, TICK, T0)
    acct.update_marks({"BTCUSDT": 81_000.0}, T1)
    res = acct.apply_funding("BTCUSDT", T2, 0.0001, 81_000.0)
    assert res.booked is True
    approx(res.cashflow, -4.05)  # positive rate: long (0.5) pays 0.0001*40,500
    assert acct.apply_funding("BTCUSDT", T2, 0.0001, 81_000.0).booked is False
    assert acct.apply_funding("BTCUSDT", T2, 0.0001, 81_000.0).reason == "already_booked"
    approx(acct.books[CURRENT_CONSERVATIVE_COST].funding_cashflow, -4.05)
    # negative rate inverts: long receives
    res2 = acct.apply_funding("BTCUSDT", "2026-01-07T16:00:00Z", -0.0001, 81_000.0)
    assert res2.booked is True
    approx(res2.cashflow, +4.05)
    approx(acct.books[CURRENT_CONSERVATIVE_COST].funding_cashflow, 0.0)
    snap = acct.equity_snapshot(T2)
    approx(snap.equity, 100_479.95)  # funding net zero; fees/slippage unchanged


def test_funding_outside_holding_window_not_booked():
    acct = make_account()
    acct.apply_fill("BTCUSDT", "buy", 0.5, 80_000.0, TICK, T0)
    # settlement BEFORE ts_opened
    early = acct.apply_funding("BTCUSDT", "2026-01-05T00:00:00Z", 0.0001, 80_000.0)
    assert early.booked is False and early.reason == "outside_holding_window"
    # settlement AT/after ts_closed: position already flat -> not booked
    acct.apply_fill("BTCUSDT", "sell", 0.5, 81_000.0, TICK, T3)
    late = acct.apply_funding("BTCUSDT", "2026-01-12T08:00:00Z", 0.0001, 81_000.0)
    assert late.booked is False and late.reason == "no_open_position"
    approx(acct.books[CURRENT_CONSERVATIVE_COST].funding_cashflow, 0.0)


def test_short_funding_receives_positive_rate():
    acct = make_account()
    acct.apply_fill("BTCUSDT", "sell", 0.5, 80_000.0, TICK, T0)
    acct.update_marks({"BTCUSDT": 80_000.0}, T0)
    res = acct.apply_funding("BTCUSDT", "2026-01-05T08:00:00Z", 0.0001, 80_000.0)
    assert res.booked is True
    approx(res.cashflow, +4.00)  # short receives 0.0001 * (0.5*80,000)


def test_missing_mark_is_fail_closed_gap_no_interpolation():
    acct = make_account()
    acct.apply_fill("BTCUSDT", "buy", 0.5, 80_000.0, TICK, T0)
    acct.update_marks({}, T1)  # mark missing
    gap = acct.equity_snapshot(T1)
    assert gap.status == "UNAVAILABLE_FAIL_CLOSED"
    assert gap.equity is None
    assert gap.missing_symbols == ("BTCUSDT",)
    assert acct.mark_gap is not None
    # drawdown unavailable during gap (never interpolated)
    dd = acct.drawdown()
    assert dd["current_drawdown_abs"] is None and dd["status"] == "UNAVAILABLE_FAIL_CLOSED"
    # no equity point written for the gap interval
    assert all(ts != T1 for ts, _ in acct.equity_history)
    # fills are refused while the gap is open (fail closed)
    with pytest.raises(MarkGapError):
        acct.apply_fill("ETHUSDT", "buy", 1.0, 3_000.0, 0.01, T1)
    # restore the mark -> gap clears, history resumes (no backfill of T1)
    acct.update_marks({"BTCUSDT": 81_000.0}, T2)
    assert acct.equity_snapshot(T2).status == "OK"
    assert [ts for ts, _ in acct.equity_history] == [T2]


def test_both_cost_books_same_quantities_different_fee_books():
    acct = make_account()
    acct.apply_fill("BTCUSDT", "buy", 0.5, 80_000.0, TICK, T0)
    acct.apply_fill("BTCUSDT", "sell", 0.5, 81_000.0, TICK, T3)
    # same quantities in one account by construction; the BOOKS differ:
    approx(acct.books[CURRENT_CONSERVATIVE_COST].fee, 40.25)  # rate 0.0005
    approx(acct.books[LINEAGE_COST].fee, 32.20)  # rate 0.0004
    approx(acct.books[CURRENT_CONSERVATIVE_COST].slippage, 0.10)  # 1 tick x2
    approx(acct.books[LINEAGE_COST].slippage, 0.20)  # 2 ticks x2
    # lineage equity view: same quantities, its own costs
    equity = acct.equity_snapshot().equity  # 100,459.65
    primary = acct.books[CURRENT_CONSERVATIVE_COST].cumulative_cost  # 40.35
    lineage = acct.books[LINEAGE_COST].cumulative_cost  # 32.40
    approx(primary, 40.35)
    approx(lineage, 32.40)
    approx(acct.equity_view(LINEAGE_COST), equity + (primary - lineage))
    approx(acct.equity_view(LINEAGE_COST), 100_467.60)


def test_counters_are_separate_never_conflated():
    acct = make_account()
    assert (acct.decision_count, acct.order_intent_count, acct.fill_count, acct.closed_position_count) == (0, 0, 0, 0)
    acct.record_decision()
    acct.record_order_intent()
    acct.apply_fill("BTCUSDT", "buy", 0.5, 80_000.0, TICK, T0)
    acct.record_decision()
    acct.record_order_intent()
    acct.apply_fill("BTCUSDT", "sell", 0.5, 81_000.0, TICK, T3)
    assert acct.decision_count == 2
    assert acct.order_intent_count == 2
    assert acct.fill_count == 2
    assert acct.closed_position_count == 1
    snapshot = acct.snapshot()
    # all four exposed separately in the read snapshot
    assert snapshot["decision_count"] == 2
    assert snapshot["order_intent_count"] == 2
    assert snapshot["fill_count"] == 2
    assert snapshot["closed_position_count"] == 1


def test_buy_beyond_cash_refuses_and_state_unchanged():
    acct = make_account(starting_cash=100.0)
    with pytest.raises(InsufficientCashError):
        acct.apply_fill("BTCUSDT", "buy", 0.01, 20_000.0, TICK, T0)
    approx(acct.cash, 100.0)
    assert acct.fill_count == 0
    assert acct.positions.get("BTCUSDT") is None


def test_short_beyond_equity_refuses_no_leverage():
    acct = make_account()
    with pytest.raises(InsufficientCashError):
        # 2 BTC gross notional 160,000 > 100,000 equity: no leverage path
        acct.apply_fill("BTCUSDT", "sell", 2.0, 80_000.0, TICK, T0)
    assert acct.fill_count == 0
    approx(acct.cash, 100_000.0)


def test_drawdown_tracked_over_valid_marks_only():
    acct = make_account()
    acct.apply_fill("BTCUSDT", "buy", 0.5, 80_000.0, TICK, T0)
    acct.update_marks({"BTCUSDT": 70_000.0}, T1)  # equity 94,979.95
    dd = acct.drawdown()
    approx(dd["current_drawdown_abs"], 100_000.0 - 94_979.95)
    approx(dd["max_drawdown_abs"], 5_020.05, tol=1e-6)
    approx(dd["max_drawdown_pct"], 5_020.05 / 100_000.0, tol=1e-9)
    acct.update_marks({"BTCUSDT": 90_000.0}, T2)  # recovery above start? no
    dd = acct.drawdown()
    approx(dd["max_drawdown_abs"], 5_020.05, tol=1e-6)  # max kept


def test_exposure_and_btc_beta_flat_book_zero():
    acct = make_account()
    exp = acct.exposure_snapshot(symbol_betas={"BTCUSDT": 1.0})
    assert exp["gross"] == 0.0 and exp["net"] == 0.0 and exp["btc_beta"] == 0.0
    acct.apply_fill("BTCUSDT", "buy", 0.5, 80_000.0, TICK, T0)
    acct.update_marks({"BTCUSDT": 80_000.0}, T0)
    exp = acct.exposure_snapshot(symbol_betas={"BTCUSDT": 1.0})
    approx(exp["gross"], 0.5 * 80_000.0 / 99_979.95)
    approx(exp["net"], exp["gross"])
    approx(exp["btc_beta"], exp["gross"])  # beta 1.0 on the only name


def test_invalid_inputs_rejected():
    acct = make_account()
    with pytest.raises(AccountingError):
        acct.apply_fill("BTCUSDT", "hoist", 0.5, 80_000.0, TICK, T0)
    with pytest.raises(AccountingError):
        acct.apply_fill("BTCUSDT", "buy", -0.5, 80_000.0, TICK, T0)


# ----------------------------------------------------------------------
# SIZING_AND_CAP_BASIS: start_of_rebalance_equity (Q-14 gross-basis fix)
# ----------------------------------------------------------------------
def test_gross_cap_basis_matches_sizing_basis_exact_boundary_completes():
    # Q-14 in miniature: leg 1 books costs (equity drops to 99,979.95);
    # leg 2 is an opening short sized on the START equity so gross-after
    # lands EXACTLY at 100,000. It completes on the supplied
    # start_of_rebalance_equity basis and refuses on the running
    # (cost-reduced) equity — exactly what the pre-fix guard measured.
    acct = make_account()
    acct.apply_fill("BTCUSDT", "buy", 0.5, 80_000.0, TICK, T0)
    approx(acct.equity_snapshot().equity, 100_000.0 - 20.0 - 0.05)  # 99,979.95
    fill = acct.apply_fill(
        "ETHUSDT", "sell", 20.0, 3_000.0, 0.01, T0, gross_cap_equity=100_000.0
    )
    approx(fill.fee, 30.0)  # 20 * 3,000 * 0.0005 (reference notional)
    approx(fill.fill_price, 2_999.99)  # ref - 1 tick (0.01), adverse
    assert acct.fill_count == 2
    approx(acct.positions["ETHUSDT"].qty, -20.0)
    # gross-after == the sizing basis exactly: BTC 40,000 + ETH 60,000
    approx(
        acct.exposure_snapshot()["gross"] * acct.equity_snapshot().equity,
        100_000.0,
    )
    # the SAME short WITHOUT the basis (current-equity fallback) refuses:
    acct2 = make_account()
    acct2.apply_fill("BTCUSDT", "buy", 0.5, 80_000.0, TICK, T0)
    with pytest.raises(InsufficientCashError):
        acct2.apply_fill("ETHUSDT", "sell", 20.0, 3_000.0, 0.01, T0)
    assert acct2.fill_count == 1
    assert "ETHUSDT" not in acct2.positions


def test_opening_short_without_cash_backing_still_refuses_despite_basis():
    # The basis fix must NOT weaken the ACTUAL-cash no-margin check:
    # fee_rate 2.0 -> fee = 1.0 * 50,000 * 2.0 = 100,000 while the short
    # proceeds credit only 49,999.90; cash_after = -50,000.10 < 0, so the
    # opening short refuses even though the supplied basis (50,000)
    # leaves exact gross headroom.
    acct = SleeveAccount(
        sleeve_id="sleeve_no_cash",
        starting_cash=0.0,
        books={"ONLY_BOOK": BookCostParams(fee_rate=2.0, slippage_ticks=1.0)},
        primary_book="ONLY_BOOK",
    )
    with pytest.raises(InsufficientCashError):
        acct.apply_fill(
            "BTCUSDT", "sell", 1.0, 50_000.0, TICK, T0, gross_cap_equity=50_000.0
        )
    assert acct.fill_count == 0
    approx(acct.cash, 0.0)
    assert acct.positions == {}


def test_gross_cap_basis_invalid_value_refuses_fail_closed():
    acct = make_account()
    for bad in (0.0, -1.0, float("nan"), float("inf"), "100000"):
        with pytest.raises(AccountingError):
            acct.apply_fill(
                "BTCUSDT", "sell", 0.1, 80_000.0, TICK, T0, gross_cap_equity=bad
            )
    assert acct.fill_count == 0
    approx(acct.cash, 100_000.0)
    assert acct.positions == {}
