"""SD4 — borrow locate, borrow fees and dividend cashflow goldens (owner: A5).

Every expected number is HAND-COMPUTED and written literally with the
arithmetic in comments.  unavailable locate => the short is REJECTED
(never filled free, rejection costs nothing); borrow fees accrue only
while a short is HELD; shorts owe the dividend on ex-date; longs receive
it.  Dividend/borrow events arrive as input records only.
"""

from __future__ import annotations

import pytest

from research.assets.common.carrying_cost import CashflowLine
from research.assets.stocks.accounting import (
    BorrowLocate,
    CostBreakdown,
    DividendEvent,
    FillRecord,
    FLOAT_IDENTITY_TOLERANCE_USD,
    IdentityLedger,
    compute_borrow_fee,
    submit_short_sale,
    StockBorrowDividendCarry,
)

T0 = "2026-03-02T14:30:00+00:00"   # entry day
TEX = "2026-03-10T14:30:00+00:00"  # dividend ex-date while short
T1 = "2026-03-12T14:30:00+00:00"   # cover day
CARRY_START = "2026-03-02T00:00:00+00:00"
CARRY_END = "2026-03-12T00:00:00+00:00"  # exactly 10 days later


def _fill(side: str, quantity: float, price: float, *, commission: float, spread: float,
          timestamp: str = T0, symbol: str = "AAPL") -> FillRecord:
    return FillRecord(
        symbol=symbol, side=side, quantity=quantity, price=price,
        timestamp_utc=timestamp,
        cost=CostBreakdown(commission=commission, spread=spread, slippage=0.0, market_impact=0.0),
    )


def _available_locate(symbol: str = "AAPL", rate: float = 0.036) -> BorrowLocate:
    return BorrowLocate(symbol=symbol, as_of_utc=T0, available=True, annual_rate=rate)


# --- golden 1: short round trip with borrow fee and dividend liability ------- #
def test_short_round_trip_with_borrow_fee_and_dividend_liability():
    ledger = IdentityLedger(starting_equity=10_000.00)

    # 1) Short entry with an AVAILABLE locate (PIT rate 3.6%):
    booked = submit_short_sale(
        ledger, _fill("SELL", 100, 49.99, commission=1.00, spread=1.00),
        _available_locate(rate=0.036), timestamp_utc=T0,
    )
    assert booked is True
    # cash = 10000 + 100*49.99 - (1.00 + 1.00) = 10000 + 4999 - 2 = 14997.00
    assert ledger.cash == pytest.approx(14997.00, abs=1e-6)

    # 2) Dividend ex-date while 100 shares are short: liability = 0.50 * 100 = 50.00
    line = ledger.apply_dividend(DividendEvent(symbol="AAPL", dividend_per_share=0.50, ex_date_utc=TEX))
    assert isinstance(line, CashflowLine)
    assert line.kind == "DIVIDEND" and line.is_paid
    assert line.amount == pytest.approx(-50.00, abs=1e-12)
    # cash = 14997 - 50 = 14947.00
    assert ledger.cash == pytest.approx(14947.00, abs=1e-6)

    # 3) Borrow fee accrual while held:
    #    fee = 50.00 (mark) * 100 (shares) * 0.036 (PIT rate) * 10 (days) / 360 = 5.00
    fee = compute_borrow_fee(price=50.00, quantity=100, annual_rate=0.036, days=10)
    assert fee == pytest.approx(5.00, abs=1e-9)
    fee_line = ledger.accrue_borrow_fee(symbol="AAPL", amount=fee, timestamp_utc=TEX)
    assert fee_line.kind == "BORROW" and fee_line.is_paid
    assert fee_line.amount == pytest.approx(-5.00, abs=1e-9)
    # cash = 14947 - 5 = 14942.00
    assert ledger.cash == pytest.approx(14942.00, abs=1e-6)

    # 4) Cover: BUY 100 @ 48.01, commission 1.00, spread 1.00
    #    realized = (49.99 - 48.01) * 100 = 198.00
    ledger.apply_fill(_fill("BUY", 100, 48.01, commission=1.00, spread=1.00, timestamp=T1))
    # cash = 14942 - 100*48.01 - 2 = 14942 - 4801 - 2 = 10139.00
    assert ledger.cash == pytest.approx(10139.00, abs=1e-6)

    terms = ledger.identity_terms()
    # delta = 10139 - 10000 = 139.00
    #       = realized 198.00 - commissions 2.00 - spread 2.00
    #         - borrow fees 5.00 - dividend liability 50.00
    assert terms.realized_price_pnl == pytest.approx(198.00, abs=1e-9)
    assert terms.commissions == pytest.approx(2.00, abs=1e-12)
    assert terms.spread == pytest.approx(2.00, abs=1e-12)
    assert terms.short_borrow_fees == pytest.approx(5.00, abs=1e-9)
    assert terms.short_dividend_liability == pytest.approx(50.00, abs=1e-12)
    assert terms.cash_dividends == 0.0
    assert terms.ending_equity - terms.starting_equity == pytest.approx(139.00, abs=1e-6)
    terms.assert_closes(FLOAT_IDENTITY_TOLERANCE_USD)


# --- golden 2: unavailable locate REJECTS the short; it costs nothing -------- #
def test_unavailable_locate_rejects_short_at_zero_cost():
    ledger = IdentityLedger(starting_equity=10_000.00)
    no_locate = BorrowLocate(symbol="AAPL", as_of_utc=T0, available=False, annual_rate=None)

    booked = submit_short_sale(
        ledger, _fill("SELL", 100, 49.99, commission=1.00, spread=1.00),
        no_locate, timestamp_utc=T0,
    )
    assert booked is False
    # NO fill was booked, NO cash moved, and the rejection itself costs nothing:
    assert ledger.fills == ()
    assert ledger.cash == 10_000.0
    assert len(ledger.rejections) == 1
    rejection = ledger.rejections[0]
    assert rejection.reason == "NO_LOCATE"
    assert rejection.cost == 0.0
    terms = ledger.identity_terms()
    assert terms.ending_equity - terms.starting_equity == 0.0
    assert terms.rejection_costs == 0.0
    terms.assert_closes(FLOAT_IDENTITY_TOLERANCE_USD)

    # The same order with a locate then fills — the blocker was the locate only:
    booked_after = submit_short_sale(
        ledger, _fill("SELL", 100, 49.99, commission=1.00, spread=1.00, timestamp=T1),
        _available_locate(), timestamp_utc=T1,
    )
    assert booked_after is True
    assert len(ledger.fills) == 1


def test_missing_locate_record_rejects_fail_closed():
    ledger = IdentityLedger(starting_equity=10_000.00)
    booked = submit_short_sale(
        ledger, _fill("SELL", 100, 49.99, commission=0.0, spread=0.0),
        None, timestamp_utc=T0,
    )
    assert booked is False
    assert ledger.rejections[0].reason == "MISSING_LOCATE"
    assert ledger.cash == 10_000.0


def test_locate_symbol_mismatch_rejects():
    ledger = IdentityLedger(starting_equity=10_000.00)
    wrong_symbol = _available_locate(symbol="MSFT")
    booked = submit_short_sale(
        ledger, _fill("SELL", 100, 49.99, commission=0.0, spread=0.0),
        wrong_symbol, timestamp_utc=T0,
    )
    assert booked is False
    assert ledger.rejections[0].reason == "LOCATE_SYMBOL_MISMATCH"


def test_locate_record_validation():
    # An AVAILABLE locate REQUIRES its PIT rate:
    with pytest.raises(ValueError, match="REQUIRES annual_rate"):
        BorrowLocate(symbol="AAPL", as_of_utc=T0, available=True, annual_rate=None)
    # An UNAVAILABLE locate must NOT carry a rate (no invented data):
    with pytest.raises(ValueError, match="must not carry annual_rate"):
        BorrowLocate(symbol="AAPL", as_of_utc=T0, available=False, annual_rate=0.05)


# --- golden 3: cash dividend receipt for longs -------------------------------- #
def test_long_dividend_receipt_golden():
    ledger = IdentityLedger(starting_equity=10_000.00)
    # BUY 100 @ 50.00, commission 1.00: cash = 10000 - 5000 - 1 = 4999.00
    ledger.apply_fill(_fill("BUY", 100, 50.00, commission=1.00, spread=0.0))
    assert ledger.cash == pytest.approx(4999.00, abs=1e-9)

    # Ex-date: receipt = 0.25 * 100 = 25.00 ; cash = 4999 + 25 = 5024.00
    line = ledger.apply_dividend(DividendEvent(symbol="AAPL", dividend_per_share=0.25, ex_date_utc=TEX))
    assert isinstance(line, CashflowLine)
    assert line.kind == "DIVIDEND"
    assert not line.is_paid  # a receipt
    assert line.amount == pytest.approx(25.00, abs=1e-12)
    assert ledger.cash == pytest.approx(5024.00, abs=1e-9)

    # SELL 100 @ 50.00, commission 1.00: cash = 5024 + 5000 - 1 = 10023.00
    ledger.apply_fill(_fill("SELL", 100, 50.00, commission=1.00, spread=0.0, timestamp=T1))
    terms = ledger.identity_terms()
    # delta = 23.00 = cash dividends 25.00 - commissions 2.00
    assert terms.cash_dividends == pytest.approx(25.00, abs=1e-12)
    assert terms.commissions == pytest.approx(2.00, abs=1e-12)
    assert terms.ending_equity - terms.starting_equity == pytest.approx(23.00, abs=1e-9)
    terms.assert_closes(FLOAT_IDENTITY_TOLERANCE_USD)


# --- golden 4: dividend applies only to positions HELD through the ex-date ---- #
def test_short_closed_before_ex_date_owes_nothing():
    ledger = IdentityLedger(starting_equity=10_000.00)
    # Short 100 @ 50.00 and cover at 50.00, zero costs: cash back to 10000, realized 0.
    assert submit_short_sale(
        ledger, _fill("SELL", 100, 50.00, commission=0.0, spread=0.0),
        _available_locate(), timestamp_utc=T0,
    )
    ledger.apply_fill(_fill("BUY", 100, 50.00, commission=0.0, spread=0.0, timestamp=TEX))
    assert ledger.position_qty("AAPL") == 0.0

    # The ex-date dividend arrives AFTER the cover: no position, no cashflow.
    line = ledger.apply_dividend(DividendEvent(symbol="AAPL", dividend_per_share=0.50, ex_date_utc=T1))
    assert line is None
    terms = ledger.identity_terms()
    assert terms.short_dividend_liability == 0.0
    assert terms.cash_dividends == 0.0
    assert terms.ending_equity - terms.starting_equity == 0.0
    terms.assert_closes()


# --- golden 5: PIT borrow rate sensitivity ------------------------------------- #
def test_borrow_fee_uses_the_pit_rate_of_its_locate():
    # Same notional 50.00 * 100 and 10 days; only the PIT rate differs:
    # 3.6%  -> 50 * 100 * 0.036 * 10 / 360 = 5.00
    # 7.2%  -> 50 * 100 * 0.072 * 10 / 360 = 10.00
    cheap = compute_borrow_fee(price=50.0, quantity=100, annual_rate=0.036, days=10)
    expensive = compute_borrow_fee(price=50.0, quantity=100, annual_rate=0.072, days=10)
    assert cheap == pytest.approx(5.00, abs=1e-9)
    assert expensive == pytest.approx(10.00, abs=1e-9)

    ledger = IdentityLedger(starting_equity=10_000.00)
    submit_short_sale(
        ledger, _fill("SELL", 100, 50.00, commission=0.0, spread=0.0),
        _available_locate(rate=0.072), timestamp_utc=T0,
    )
    ledger.accrue_borrow_fee(
        symbol="AAPL",
        amount=compute_borrow_fee(price=50.0, quantity=100, annual_rate=0.072, days=10),
        timestamp_utc=TEX,
    )
    assert ledger.bucket("short_borrow_fees") == pytest.approx(10.00, abs=1e-9)


def test_borrow_fee_accrues_only_while_the_short_is_held():
    ledger = IdentityLedger(starting_equity=10_000.00)
    with pytest.raises(ValueError, match="without an open short"):
        ledger.accrue_borrow_fee(symbol="AAPL", amount=5.0, timestamp_utc=T0)

    submit_short_sale(
        ledger, _fill("SELL", 100, 50.00, commission=0.0, spread=0.0),
        _available_locate(), timestamp_utc=T0,
    )
    # Two accrual events while held: 5.00 + 5.00 = 10.00 total
    ledger.accrue_borrow_fee(symbol="AAPL", amount=5.0, timestamp_utc=T0)
    ledger.accrue_borrow_fee(symbol="AAPL", amount=5.0, timestamp_utc=TEX)
    assert ledger.bucket("short_borrow_fees") == pytest.approx(10.00, abs=1e-12)
    # cash = 10000 + 5000 - 10 = 14990.00
    assert ledger.cash == pytest.approx(14990.00, abs=1e-9)

    ledger.apply_fill(_fill("BUY", 100, 50.00, commission=0.0, spread=0.0, timestamp=T1))
    with pytest.raises(ValueError, match="without an open short"):
        ledger.accrue_borrow_fee(symbol="AAPL", amount=5.0, timestamp_utc=T1)


def test_negative_borrow_fee_amount_is_rejected():
    ledger = IdentityLedger(starting_equity=10_000.00)
    submit_short_sale(
        ledger, _fill("SELL", 100, 50.00, commission=0.0, spread=0.0),
        _available_locate(), timestamp_utc=T0,
    )
    with pytest.raises(ValueError, match="amount must be >= 0"):
        ledger.accrue_borrow_fee(symbol="AAPL", amount=-5.0, timestamp_utc=T0)


# --- the frozen common carry interface ------------------------------------------ #
def test_carry_model_short_lines_match_goldens():
    carry = StockBorrowDividendCarry()
    lines = carry.cashflows(
        instrument_symbol="AAPL",
        position_qty=-100,
        interval_start_utc=CARRY_START,
        interval_end_utc=CARRY_END,  # exactly 10 days
        context={
            "borrow_rate_annual": 0.036,
            "price": 50.00,
            "dividend_events": (
                {"timestamp_utc": TEX, "dividend_per_share": 0.50},
            ),
        },
    )
    assert len(lines) == 2
    borrow = [line for line in lines if line.kind == "BORROW"]
    dividend = [line for line in lines if line.kind == "DIVIDEND"]
    # borrow = 50 * 100 * 0.036 * 10 / 360 = 5.00 paid ; dividend = 0.50 * 100 = 50.00 owed
    assert len(borrow) == 1 and len(dividend) == 1
    assert borrow[0].amount == pytest.approx(-5.00, abs=1e-9)
    assert borrow[0].timestamp_utc == CARRY_END
    assert dividend[0].amount == pytest.approx(-50.00, abs=1e-12)
    assert dividend[0].timestamp_utc == TEX
    assert all(line.instrument_symbol == "AAPL" for line in lines)


def test_carry_model_long_receipt_and_flat_positions():
    carry = StockBorrowDividendCarry()
    long_lines = carry.cashflows(
        instrument_symbol="AAPL",
        position_qty=100,
        interval_start_utc=CARRY_START,
        interval_end_utc=CARRY_END,
        context={
            "dividend_events": (
                {"timestamp_utc": TEX, "dividend_per_share": 0.25},
            ),
        },
    )
    # Longs never pay borrow; receipt = 0.25 * 100 = +25.00
    assert len(long_lines) == 1
    assert long_lines[0].kind == "DIVIDEND"
    assert long_lines[0].amount == pytest.approx(25.00, abs=1e-12)

    # Flat position: no cashflows at all.
    assert carry.cashflows(
        instrument_symbol="AAPL", position_qty=0,
        interval_start_utc=CARRY_START, interval_end_utc=CARRY_END,
        context={"dividend_events": ({"timestamp_utc": TEX, "dividend_per_share": 0.25},)},
    ) == ()

    # Long WITHOUT any dividend event: no borrow line, no lines.
    assert carry.cashflows(
        instrument_symbol="AAPL", position_qty=100,
        interval_start_utc=CARRY_START, interval_end_utc=CARRY_END,
        context={},
    ) == ()


def test_carry_model_short_fails_closed_without_rate_or_mark():
    carry = StockBorrowDividendCarry()
    with pytest.raises(ValueError, match="borrow_rate_annual"):
        carry.cashflows(
            instrument_symbol="AAPL", position_qty=-100,
            interval_start_utc=CARRY_START, interval_end_utc=CARRY_END, context={},
        )
    with pytest.raises(ValueError, match="price"):
        carry.cashflows(
            instrument_symbol="AAPL", position_qty=-100,
            interval_start_utc=CARRY_START, interval_end_utc=CARRY_END,
            context={"borrow_rate_annual": 0.036},
        )


def test_carry_model_id_is_explicit():
    assert StockBorrowDividendCarry().model_id == "STOCKS_BORROW_DIVIDEND_V1"
    assert StockBorrowDividendCarry(model_id="STOCKS_BORROW_DIVIDEND_TEST").model_id == \
        "STOCKS_BORROW_DIVIDEND_TEST"
