"""G9 prep build tests — quote-CCY book, daily journal writer, DECLARED
cost kernel (tests/test_daily_exploratory.py).

SYNTHETIC FIXTURES ONLY: every number below is hand-computed on the
synthetic bars defined in this file; NO real panel is read anywhere, no
scored computation exists (OI-2 blocker; plan §0b G1). All expected
values were derived by hand in the comments next to each assertion
(Decimal-exact arithmetic; verified independently 2026-10-01).

Coverage ordered by the dispatch packet:
1. quote-CCY §6 identity on hand numbers — EURUSD trade (USD quote),
   USDJPY trade with explicit JPY->USD conversion rows, blocked signal
   (zero-event identity), multi-day hold with Wed x3 swap;
2. tier stress x1.5 / x2.0 (FILL_ACCOUNTING_SPEC §5);
3. BAR-SIDE-DIFFERENCE law (G5 co-owner decision 2026-10-01);
4. frozen band table hardcoding + validation-only role;
5. tamper detection on the hash chain;
6. leak-law counter-test (poisoned performance-named field MUST fail);
7. determinism (byte-identical re-run);
8. OI-1 next-business-day PIT law enforcement.
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))

from daily_exploratory import journal as jrn  # noqa: E402
from daily_exploratory.costkernel import (  # noqa: E402
    D1BAND_TABLE,
    NOT_COMPUTED_CELL_LABEL,
    DailyBar,
    DeclaredCostKernel,
)
from daily_exploratory.journal import (  # noqa: E402
    DailyJournalWriter,
    JournalIntegrityError,
    JournalValidationError,
    LeakLawViolation,
    next_business_day,
)
from daily_exploratory.quoteccy import QuoteCcyBook  # noqa: E402

OPENING_USD = "100000"

# ===========================================================================
# Synthetic bars (invented for the fixtures; NOT any real panel)
# ===========================================================================

# EURUSD — entry bar Mon 2026-05-04, exit bar Tue 2026-05-05.
EUR_BAR_1 = DailyBar("2026-05-04", bid_open=1.10000, ask_open=1.10020,
                     bid_close=1.10500, ask_close=1.10520)
EUR_BAR_2 = DailyBar("2026-05-05", bid_open=1.10500, ask_open=1.10520,
                     bid_close=1.10400, ask_close=1.10420)
# mids: mid_open(1) = 1.10010, mid_open(2) = 1.10510 (hand: (bid+ask)/2).

# USDJPY — entry bar Wed 2026-05-06, exit bar Tue 2026-05-12. Mid opens
# 156.25 and 160.00 chosen so the same-bar conversion rates 1/156.25 =
# 0.0064 and 1/160.00 = 0.00625 are exact decimals (hand-checkable).
JPY_BAR_WED = DailyBar("2026-05-06", bid_open=156.000, ask_open=156.500,
                       bid_close=156.400, ask_close=156.600)
JPY_BAR_TUE = DailyBar("2026-05-12", bid_open=159.750, ask_open=160.250,
                       bid_close=159.800, ask_close=160.200)

# NZDUSD — the G5 tail day 2025-03-03 raw quotes (async first prints):
# ASK_open 0.58345 vs BID_open 0.55975 -> open-side difference 414.6256
# bps of mid 0.57160 (reproduces the frozen table's max cell exactly).
NZD_TAIL_BAR = DailyBar("2025-03-03", bid_open=0.55975, ask_open=0.58345,
                        bid_close=0.58330, ask_close=0.58350)


def _pit(input_id: str, consumed: str, available: str, ok: bool = True) -> dict:
    return {
        "input_id": input_id,
        "consumed_bar_date": consumed,
        "available_time_utc": available,
        "value_digest": f"sha256:synthetic:{input_id}:{consumed}",
        "max_age_ok": ok,
    }


def _base_decision(symbol: str, ts_decision: str, pit_entries: list) -> dict:
    return {
        "ts_decision_utc": ts_decision,
        "fold_id": "FOLD-1",
        "cycle_id": "DAILY-EXPLORATORY-PREP-SYNTH",
        "sleeve_id": "DS-05",
        "symbol": symbol,
        "family_id": "A-TREND",
        "mech_key": "xsect_antiusd_rank",
        "feature_pit_snapshot": pit_entries,
        "direction_vote": 1,
        "desired_risk_units": 100000,
        "entry_reason_code": "SYNTH_FIXTURE",
        "eligibility_state": "ON",
    }


def _trade_row(book_rec, fq, order_kind: str, order_id: str) -> dict:
    """Map a book FillRecord + kernel FillQuote to a journal_row@1 trade
    row (the mapping the future engine will make)."""
    row = _base_decision(fq.symbol, book_rec.ts, [
        _pit(f"I-{fq.symbol}", "2026-05-01", "2026-05-04T00:00:00Z")
        if fq.symbol == "EURUSD" else
        _pit("I-JPY", "2026-05-05", "2026-05-06T00:00:00Z"),
    ])
    row.update({
        "record_kind": jrn.RECORD_KIND_TRADE,
        "outcome": jrn.OUTCOME_FILLED,
        "order_id": order_id,
        "order_kind": order_kind,
        "ts_fill_utc": book_rec.ts,
        "fill_price": float(fq.fill_price),
        "fill_side_quote": fq.fill_side_quote,
        "spread_pips_charged": fq.spread_band_cell_id,
        "slippage_beyond_spread": fq.slippage_band_id,
        "venue_model": "SYNTHETIC_FIXTURE",
        "commission": float(fq.commission_total),
        "cash_delta_quoteccy": float(book_rec.cash_delta_quote),
        "cash_delta_usd": float(book_rec.conversion.usd_amount),
        "fx_conversion": book_rec.conversion.to_jsonable(),
    })
    return row


# ===========================================================================
# 1. EURUSD round trip — hand-computed identity (quote CCY = USD)
# ===========================================================================

def test_eurusd_round_trip_identity_hand_numbers():
    """Hand derivation (tier 1.0, non-event slip 0.2 pip = 0.00002):

    entry BUY 100000 at ASK_open 1.10020 + 0.00002 -> fill 1.10022
      mid_at_fill 1.10010; spread_once = 1.10020-1.10010 = 0.00010/u
        -> 100000 x 0.00010 = 10.00
      slip = 100000 x 0.00002 = 2.00
      commission = 0.000035 x 100000 x 1.10022 = 3.5 x 1.10022 = 3.85077
      cash delta = -(100000 x 1.10022 + 3.85077) = -110025.85077
    swap Mon 2026-05-06? NO — entry Mon 05-04 17:00Z, Mon 22:00Z accrual
      x1: 100000 x 0.0001 x 1 = 10.00 (charged: u(Mon22-) != 0)
    exit SELL 100000 at BID_open 1.10500 - 0.00002 -> fill 1.10498
      mid_at_fill 1.10510; spread_once = 10.00; slip = 2.00
      commission = 3.5 x 1.10498 = 3.86743
      cash delta = +(100000 x 1.10498 - 3.86743) = +110494.13257
    gross vs mid = 100000 x (1.10510 - 1.10010) = 500.00
    LHS = 500 - 10 - 10 - 2 - 2 - 3.85077 - 3.86743 - 10 = 458.28180
    cash_final = -110025.85077 - 10 + 110494.13257 = 458.28180
    equity levels: 100000 -> 100458.28180. residual = 0 exactly.
    """
    kernel = DeclaredCostKernel("EURUSD", tier=1.0)
    book = QuoteCcyBook("EURUSD", kernel, opening_usd=OPENING_USD,
                        open_ts="2026-05-04T00:00:00Z", open_rate_to_usd="1.0")

    fq_in = kernel.price_fill(EUR_BAR_1, "BUY", 100000)
    assert fq_in.fill_price == Decimal("1.10022")
    assert fq_in.quoted_side_price == Decimal("1.10020")
    assert fq_in.mid_at_fill == Decimal("1.10010")
    assert fq_in.spread_once_total == Decimal("10.00")
    assert fq_in.slip_beyond_total == Decimal("2.00")
    assert fq_in.commission_total == Decimal("3.8507700")
    assert fq_in.crossing_identity_residual() == 0

    rec_in = book.apply_fill("2026-05-04T17:00:00Z", EUR_BAR_1, "BUY", 100000,
                             rate_to_usd="1.0")
    assert rec_in.cash_delta_quote == Decimal("-110025.8507700")

    # Monday 22:00Z accrual event x1 (u != 0 at E-)
    acc = book.accrue_swap("2026-05-04T22:00:00Z", multiplier=1,
                           rate_to_usd="1.0")
    assert acc is not None and acc.charge_quote == Decimal("10.0000")
    assert acc.wed_x3 is False

    # Open-position leg: identity at the Tue mid with the position still
    # open must hold BEFORE the exit (open leg = u x (m_T - m_entry)).
    # LHS = 500 - 10 - 2 - 3.85077 - 10 = 474.14923; level change
    # (cash -10035.85077 + 100000 x 1.10510) - 100000 = 474.14923.
    open_rep = book.check_identity("2026-05-05T00:00:00Z", "1.10510")
    assert open_rep.residual == 0 and open_rep.holds
    assert open_rep.identity_gross_vs_mid_sum == Decimal("500.0000")
    assert open_rep.equity_level_final_quote == Decimal("100474.1492300")

    fq_out = kernel.price_fill(EUR_BAR_2, "SELL", 100000)
    assert fq_out.fill_price == Decimal("1.10498")
    assert fq_out.spread_once_total == Decimal("10.00")
    assert fq_out.commission_total == Decimal("3.8674300")
    rec_out = book.apply_fill("2026-05-05T17:00:00Z", EUR_BAR_2, "SELL", 100000,
                              rate_to_usd="1.0")
    assert rec_out.cash_delta_quote == Decimal("110494.1325700")

    assert book.units == 0
    # cash level = 100000 opening - 110025.85077 - 10 + 110494.13257
    assert book.cash_quote == Decimal("100458.2818000")

    rep = book.check_identity("2026-05-05T17:00:00Z", "1.10510")
    assert rep.residual == 0 and rep.holds
    assert rep.identity_gross_vs_mid_sum == Decimal("500.0000")
    assert rep.identity_cost_sum_spread_once == Decimal("20.00")
    assert rep.identity_cost_sum_slip_beyond == Decimal("4.0000")
    assert rep.identity_cost_sum_commission == Decimal("7.7182000")
    assert rep.identity_cost_sum_swap == Decimal("10.0000")
    assert rep.equity_level_open_quote == Decimal("100000")
    assert rep.equity_level_final_quote == Decimal("100458.2818000")
    assert rep.n_fills == 2 and rep.n_swap_events == 1

    # Conversion-row law: USD-quoted book, identity rate 1.0 STILL logged,
    # exactly one conversion row per cash event (open + 2 fills + 1 swap).
    assert len(book.conversion_rows) == 4
    for c in book.conversion_rows:
        assert c.quote_ccy == "USD" and c.rate_to_usd == 1
        assert c.usd_amount == c.quote_amount
    # Par replay: all rates 1.0 -> divergence EXACTLY zero (at-par defect
    # mechanically closed for USD-quoted books).
    par = book.par_replay("2026-05-05T17:00:00Z", "1.10510", "1.0")
    assert par.divergence_abs == 0 and par.within_bound


def test_usdjpy_conversion_identity_and_wed3_swap():
    """Hand derivation (quote CCY = JPY; pip 0.01; slip 0.2 pip = 0.002):

    opening: 100000 USD at rate 1/156.25 = 0.0064 -> 15,625,000 JPY
    entry BUY 100000 USD Wed 2026-05-06 17:00Z at ASK 156.500 + 0.002:
      fill 156.502; mid 156.250; spread_once = 0.250/u -> 25,000 JPY
      slip 100000 x 0.002 = 200 JPY
      commission = 3.5 x 156.502 = 547.757 JPY
      cash delta = -(15,650,200 + 547.757) = -15,650,747.757 JPY
        -> USD: x 0.0064 = -100,164.7856448
    swap accruals while held (exit Tue 2026-05-12 17:00Z):
      Wed 05-06 22:00Z x3 = 3,000 | Thu x1 = 1,000 | Fri x0 | Sat none
      Sun 05-10 x1 = 1,000 | Mon 05-11 x1 = 1,000 | Tue 22:00Z after exit
      -> total 6 pip-nights = 100000 x 0.01 x 6 = 6,000 JPY
    exit SELL at BID 159.750 - 0.002 -> fill 159.748; mid 160.000;
      spread_once = 0.250/u -> 25,000 JPY; slip 200; commission
      = 3.5 x 159.748 = 559.118 JPY
      cash delta = +(15,974,800 - 559.118) = +15,974,240.882 JPY
        -> USD: x 0.00625 = +99,839.0055125
    gross vs mid = 100000 x (160.000 - 156.250) = 375,000 JPY
    LHS = 375,000 - 50,000 - 400 - 1,106.875 - 6,000 = 317,493.125
    cash_final = 15,625,000 - 15,650,747.757 - 6,000 + 15,974,240.882
               = 15,942,493.125 JPY; level change = 317,493.125. residual 0.
    par replay: realized = 100,000 - 100,164.7856448 - 38.4
                + 99,839.0055125 = 99,635.8198677 USD vs par 15,942,493.125
    divergence = 15,842,857.3051323 <= disclosed bound.
    """
    kernel = DeclaredCostKernel("USDJPY", tier=1.0)
    book = QuoteCcyBook("USDJPY", kernel, opening_usd=OPENING_USD,
                        open_ts="2026-05-06T00:00:00Z", open_rate_to_usd="0.0064")
    assert book.quote_ccy == "JPY"
    assert book.cash_quote == Decimal("15625000")

    # swap calendar iteration: entry Wed 17:00Z -> exit Tue 17:00Z
    import datetime as dt
    events = list(DeclaredCostKernel.iter_swap_events(
        dt.datetime(2026, 5, 6, 17, 0, tzinfo=dt.timezone.utc),
        dt.datetime(2026, 5, 12, 17, 0, tzinfo=dt.timezone.utc)))
    assert [(e[0].strftime("%Y-%m-%d"), e[1], e[2]) for e in events] == [
        ("2026-05-06", 3, True),   # Wed x3
        ("2026-05-07", 1, False),  # Thu
        ("2026-05-10", 1, False),  # Sun (Fri x0, Sat no event skipped)
        ("2026-05-11", 1, False),  # Mon
    ]
    assert sum(m for _, m, _ in events) == 6

    fq_in = kernel.price_fill(JPY_BAR_WED, "BUY", 100000)
    assert fq_in.fill_price == Decimal("156.502")
    assert fq_in.mid_at_fill == Decimal("156.250")
    assert fq_in.spread_once_total == Decimal("25000.000")
    assert fq_in.commission_total == Decimal("547.7570")
    rec_in = book.apply_fill("2026-05-06T17:00:00Z", JPY_BAR_WED, "BUY", 100000,
                             rate_to_usd="0.0064")
    assert rec_in.cash_delta_quote == Decimal("-15650747.7570")
    assert rec_in.conversion.usd_amount == Decimal("-100164.78564480")

    for (ev_ts, mult, _) in events:
        rec = book.accrue_swap(f"{ev_ts.strftime('%Y-%m-%d')}T22:00:00Z",
                               multiplier=mult, rate_to_usd="0.0064")
        assert rec is not None
    swap_total = sum(e.charge_quote for e in book.swap_events)
    assert swap_total == Decimal("6000.0000")
    assert [e.multiplier for e in book.swap_events] == [3, 1, 1, 1]
    assert [e.wed_x3 for e in book.swap_events] == [True, False, False, False]

    fq_out = kernel.price_fill(JPY_BAR_TUE, "SELL", 100000)
    assert fq_out.fill_price == Decimal("159.748")
    assert fq_out.spread_once_total == Decimal("25000.000")
    assert fq_out.commission_total == Decimal("559.1180")
    rec_out = book.apply_fill("2026-05-12T17:00:00Z", JPY_BAR_TUE, "SELL",
                              100000, rate_to_usd="0.00625")
    assert rec_out.cash_delta_quote == Decimal("15974240.8820")
    assert rec_out.conversion.usd_amount == Decimal("99839.00551250")

    assert book.units == 0
    assert book.cash_quote == Decimal("15942493.1250")

    book.mark("2026-05-12T17:00:00Z", "160.000", rate_to_usd="0.00625")
    rep = book.check_identity("2026-05-12T17:00:00Z", "160.000")
    assert rep.residual == 0 and rep.holds
    assert rep.identity_gross_vs_mid_sum == Decimal("375000.00")
    assert rep.identity_cost_sum_spread_once == Decimal("50000.000")
    assert rep.identity_cost_sum_slip_beyond == Decimal("400.0000")
    assert rep.identity_cost_sum_commission == Decimal("1106.8750")
    assert rep.identity_cost_sum_swap == Decimal("6000.0000")
    assert rep.equity_level_open_quote == Decimal("15625000")
    assert rep.equity_level_final_quote == Decimal("15942493.1250")

    # conversion-row law: open + 2 fills + 4 swaps + 1 mark = 8 rows, every
    # JPY event explicitly converted at its own same-bar rate.
    assert len(book.conversion_rows) == 8
    kinds = [c.event_kind for c in book.conversion_rows]
    assert kinds.count("FILL") == 2 and kinds.count("SWAP_ACCRUAL") == 4

    # par-convention replay cross-check with the disclosed bound
    par = book.par_replay("2026-05-12T17:00:00Z", "160.000", "0.00625")
    realized = (Decimal("100000") - Decimal("100164.78564480")
                - Decimal("38.4") + Decimal("99839.00551250"))
    assert par.final_usd_level_realization_convention == realized
    assert realized == Decimal("99635.81986770")
    assert par.final_usd_level_par_convention == Decimal("15942493.1250")
    assert par.divergence_abs == Decimal("15842857.30513230")
    assert par.within_bound


def test_blocked_signal_zero_event_identity():
    """A blocked signal writes NO cash/position event: the book over the
    blocked window is the trivial book and the identity holds at zero."""
    kernel = DeclaredCostKernel("NZDUSD", tier=1.0)
    book = QuoteCcyBook("NZDUSD", kernel, opening_usd=OPENING_USD,
                        open_ts="2026-05-07T00:00:00Z", open_rate_to_usd="1.0")
    rep = book.check_identity("2026-05-08T00:00:00Z", "0.58000")
    assert rep.n_fills == 0 and rep.n_swap_events == 0
    assert rep.residual == 0 and rep.holds
    assert rep.equity_level_final_quote == rep.equity_level_open_quote
    par = book.par_replay("2026-05-08T00:00:00Z", "0.58000", "1.0")
    assert par.divergence_abs == 0


# ===========================================================================
# 2. Tier stress x1.5 / x2.0 (FILL_ACCOUNTING_SPEC §5)
# ===========================================================================

def test_tier_stress_1p5_and_2p0():
    """Hand derivation (same EURUSD bars; entry Mon, exit Tue, Mon-night
    swap x1; every VARIABLE component scales with tau, the bar-quoted
    spread_once does NOT — the stress excess lands in slip_beyond so the
    spread-once identity holds at every tier):

    tau=1.5: fill_b = 1.10010 + 1.5x0.00012 = 1.100280
             fill_s = 1.10510 - 1.5x0.00012 = 1.104920
             spread_once 10.00 + 10.00 (bar-quoted, unscaled)
             slip = |fill-side| = 0.00008/u -> 8.00 + 8.00
             commission = 1.5 x 3.5 x fill: 5.776470 + 5.800830
             swap = 1.5 x 10 = 15.00
             LHS = 500 - 20 - 16 - 11.5773 - 15 = 437.4227
             cash = -110028 - 5.77647 - 15 + 110492 - 5.80083 = 437.4227
    tau=2.0: fill_b 1.100340, fill_s 1.104860; slip 14+14;
             commission 7.702380 + 7.734020; swap 20.00
             LHS = 500 - 20 - 28 - 15.4364 - 20 = 416.5636
    """
    for tau, fill_b, fill_s, slip_each, comm_in, comm_out, swap in [
        ("1.5", "1.100280", "1.104920", "8.0000", "5.7764700", "5.8008300", "15.0000"),
        ("2.0", "1.100340", "1.104860", "14.0000", "7.7023800", "7.7340200", "20.0000"),
    ]:
        kernel = DeclaredCostKernel("EURUSD", tier=float(tau))
        book = QuoteCcyBook("EURUSD", kernel, opening_usd=OPENING_USD,
                            open_ts="2026-05-04T00:00:00Z", open_rate_to_usd="1.0")
        fq_in = kernel.price_fill(EUR_BAR_1, "BUY", 100000)
        fq_out = kernel.price_fill(EUR_BAR_2, "SELL", 100000)
        assert fq_in.fill_price == Decimal(fill_b)
        assert fq_out.fill_price == Decimal(fill_s)
        # bar-quoted spread_once unchanged under stress; excess in slip
        assert fq_in.spread_once_total == Decimal("10.00")
        assert fq_out.spread_once_total == Decimal("10.00")
        assert fq_in.slip_beyond_total == Decimal(slip_each)
        assert fq_out.slip_beyond_total == Decimal(slip_each)
        assert fq_in.commission_total == Decimal(comm_in)
        assert fq_out.commission_total == Decimal(comm_out)
        for fq in (fq_in, fq_out):
            assert fq.crossing_identity_residual() == 0

        book.apply_fill("2026-05-04T17:00:00Z", EUR_BAR_1, "BUY", 100000,
                        rate_to_usd="1.0")
        acc = book.accrue_swap("2026-05-04T22:00:00Z", multiplier=1,
                               rate_to_usd="1.0")
        assert acc is not None and acc.charge_quote == Decimal(swap)
        book.apply_fill("2026-05-05T17:00:00Z", EUR_BAR_2, "SELL", 100000,
                        rate_to_usd="1.0")
        rep = book.check_identity("2026-05-05T17:00:00Z", "1.10510")
        assert rep.residual == 0 and rep.holds
        hand_lhs = (Decimal("500") - Decimal("20")
                    - 2 * Decimal(slip_each)
                    - Decimal(comm_in) - Decimal(comm_out) - Decimal(swap))
        assert rep.equity_level_final_quote - rep.equity_level_open_quote \
            == hand_lhs


# ===========================================================================
# 3. BAR-SIDE-DIFFERENCE law (G5 co-owner decision 2026-10-01)
# ===========================================================================

def test_bar_side_difference_is_diagnostic_never_a_cost():
    """The async open-side difference (full width) is REPORTED, never
    charged: the fill goes to the side's OWN open quote and the charge is
    the distance to mid (half), so the crossing lines still sum to
    |fill - mid| exactly.

    NZD 2025-03-03: bid_open 0.55975, ask_open 0.58345, mid 0.57160.
      full open-side difference = 0.02370 -> 414.6256 bps (the frozen
      O-FOLDS max cell, reproduced).
      BUY 100000: fill = 0.58345 + 0.00002 = 0.58347
      spread_once = (0.58345 - 0.57160) x 100000 = 1185.00  (NOT 2370.00
        — the full width would be the double charge the law forbids)
      slip = 2.00; identity 1185 + 2 == 100000 x |0.58347 - 0.57160|.
    """
    kernel = DeclaredCostKernel("NZDUSD", tier=1.0)
    fq = kernel.price_fill(NZD_TAIL_BAR, "BUY", 100000)
    assert fq.fill_price == Decimal("0.58347")
    assert fq.quoted_side_price == Decimal("0.58345")
    assert fq.spread_once_total == Decimal("1185.0000")
    assert fq.slip_beyond_total == Decimal("2.0000")
    assert fq.crossing_identity_residual() == 0
    assert abs(fq.spread_once_total - Decimal("2370.00")) != 0
    # diagnostic field: full-side width in bps, flagged non-executable
    assert fq.bar_side_difference_executable is False
    assert fq.bar_side_difference_bps == pytest.approx(
        (Decimal("0.58345") - Decimal("0.55975")) / Decimal("0.57160")
        * Decimal(10000), abs=Decimal("1e-12"))
    assert float(fq.bar_side_difference_bps) == pytest.approx(414.6256, abs=1e-3)

    # band validation (never a cost): the day validates against the frozen
    # O-FOLDS cell as the tabled max, flagged above p90 — as a REPORT.
    v = kernel.validate_bar_spread(NZD_TAIL_BAR, which="OPEN")
    assert v["cell_id"] == "D1BAND-NZDUSD-O-FOLDS"
    assert v["within_max"] is True
    assert v["gt_p90"] is True
    assert v["verdict"] == "VALIDATED_AGAINST_FROZEN_BAND"

    # identity still closes with the tail-day fill in the book
    book = QuoteCcyBook("NZDUSD", kernel, opening_usd=OPENING_USD,
                        open_ts="2025-03-03T00:00:00Z", open_rate_to_usd="1.0")
    book.apply_fill("2025-03-03T17:00:00Z", NZD_TAIL_BAR, "BUY", 100000,
                    rate_to_usd="1.0")
    rep = book.check_identity("2025-03-03T17:00:00Z", "0.58340")
    assert rep.residual == 0 and rep.holds

    # EURUSD has NO computed D1 band yet -> typed NOT_COMPUTED, never a
    # guessed cell, and the fill still prices from the bar's own side.
    eur_kernel = DeclaredCostKernel("EURUSD")
    fq_eur = eur_kernel.price_fill(EUR_BAR_1, "BUY", 1000)
    assert fq_eur.spread_band_cell_id == NOT_COMPUTED_CELL_LABEL
    v2 = eur_kernel.validate_bar_spread(EUR_BAR_1, which="OPEN")
    assert v2["verdict"] == "NOT_COMPUTED"


def test_frozen_band_table_hardcoded_from_g5():
    """The G5 §1.8 table is hardcoded verbatim with cell ids (spot-check
    the load-bearing cells + table size + sha pins)."""
    assert len(D1BAND_TABLE) == 24
    assert D1BAND_TABLE["D1BAND-NZDUSD-O-FOLDS"] == {
        "cell_id": "D1BAND-NZDUSD-O-FOLDS", "instrument": "NZDUSD",
        "side": "OPEN", "window": "FOLDS", "p50_bps": 2.6118,
        "p90_bps": 21.3272, "p95_bps": 32.7445, "max_bps": 414.6256,
        "n_days": 1031,
        "aggregate_sha256": "c681402b03e58502fcb7a22d7d7b26ccefcccf5117b20fa2ec82e2689a9782ed",
    }
    # probe-continuity control cell (exact reproduction claim, G5 §1.4)
    c = D1BAND_TABLE["D1BAND-NZDUSD-C-FULL"]
    assert (c["p50_bps"], c["p90_bps"], c["max_bps"], c["n_days"]) == (
        0.8822, 18.6544, 239.0719, 1553)
    # XAG derived for completeness only (OI-4 NOT_RUN stands) — present,
    # labeled by its instrument, never consumed by a slate leg here.
    assert "D1BAND-XAGUSD-O-FOLDS" in D1BAND_TABLE


# ===========================================================================
# 4. Journal: hash chain, blocked purity, PIT law, leak scan, determinism
# ===========================================================================

def _write_eurusd_journal(path) -> DailyJournalWriter:
    kernel = DeclaredCostKernel("EURUSD", tier=1.0)
    book = QuoteCcyBook("EURUSD", kernel, opening_usd=OPENING_USD,
                        open_ts="2026-05-04T00:00:00Z", open_rate_to_usd="1.0")
    rec_in = book.apply_fill("2026-05-04T17:00:00Z", EUR_BAR_1, "BUY", 100000,
                             rate_to_usd="1.0")
    book.accrue_swap("2026-05-04T22:00:00Z", multiplier=1, rate_to_usd="1.0")
    rec_out = book.apply_fill("2026-05-05T17:00:00Z", EUR_BAR_2, "SELL", 100000,
                              rate_to_usd="1.0")
    swap_json = [e.to_jsonable() for e in book.swap_events]

    writer = DailyJournalWriter(path, cycle_id="DAILY-EXPLORATORY-PREP-SYNTH",
                                fold_id="FOLD-1", run_label="synthetic-fixture")
    fq_in = kernel.price_fill(EUR_BAR_1, "BUY", 100000)
    fq_out = kernel.price_fill(EUR_BAR_2, "SELL", 100000)
    row_in = _trade_row(rec_in, fq_in, "OPEN", "ORD-0001")
    row_out = _trade_row(rec_out, fq_out, "CLOSE", "ORD-0002")
    row_out["swap_financing"] = swap_json

    blocked = _base_decision("NZDUSD", "2026-05-07T00:00:00Z", [
        _pit("I-NZD", "2026-05-06", "2026-05-07T00:00:00Z", ok=False),
        _pit("I-VIX", "2026-05-06", "2026-05-07T00:00:00Z", ok=True),
    ])
    blocked.update({
        "record_kind": jrn.RECORD_KIND_BLOCKED,
        "outcome": jrn.OUTCOME_BLOCKED_STALE,
        "blocked_reason_detail":
            "I-NZD serving staleness at decision: max_age_ok false",
    })

    writer.write_rows([row_in, row_out, blocked])
    return writer


def test_journal_chain_blocked_purity_and_leak_clean(tmp_path):
    path = tmp_path / "journal.jsonl"
    writer = _write_eurusd_journal(path)
    writer.close()

    report = DailyJournalWriter.verify_chain(path)
    assert report["ok"] and report["rows"] == 4  # header + 2 trades + 1 blocked

    lines = [l for l in path.read_text().splitlines() if l]
    header = __import__("json").loads(lines[0])
    assert header["record_kind"] == jrn.RECORD_KIND_HEADER
    assert header["schema"] == "journal_row@1"
    assert header["prev_row_sha256"] == jrn.GENESIS_PREV
    assert "RGC-INC-1_NO_PERF_FIELDS" in header["laws"]

    import json
    rows = [json.loads(l) for l in lines]
    # blocked row purity: fill fields ABSENT (never zero), decision block kept
    blocked = rows[3]
    assert blocked["outcome"] == jrn.OUTCOME_BLOCKED_STALE
    for absent in ("fill_price", "commission", "cash_delta_usd",
                  "fx_conversion", "swap_financing"):
        assert absent not in blocked
    assert blocked["feature_pit_snapshot"][0]["available_time_utc"] \
        .startswith("2026-05-07")  # next business day after consumed 05-06
    # leak-clean over the whole written file
    for r in rows:
        assert jrn.scan_keys_for_leaks(r) == []


def test_journal_tamper_detection(tmp_path):
    path = tmp_path / "journal.jsonl"
    w = _write_eurusd_journal(path)
    w.close()
    DailyJournalWriter.verify_chain(path)  # intact baseline

    # 1) edit a fill price digit in a trade row -> digest mismatch
    text = path.read_text()
    lines = text.splitlines()
    assert "1.10022" in lines[1]
    path.write_text("\n".join(
        lines[:1] + [lines[1].replace("1.10022", "1.10023")] + lines[2:]) + "\n")
    with pytest.raises(JournalIntegrityError, match="digest mismatch"):
        DailyJournalWriter.verify_chain(path)

    # 2) delete a middle row -> chain link broken
    path.write_text("\n".join([lines[0], lines[2], lines[3]]) + "\n")
    with pytest.raises(JournalIntegrityError, match="chain link"):
        DailyJournalWriter.verify_chain(path)

    # 3) swap two rows -> link broken
    path.write_text("\n".join([lines[0], lines[2], lines[1], lines[3]]) + "\n")
    with pytest.raises(JournalIntegrityError):
        DailyJournalWriter.verify_chain(path)

    # 4) restore -> verifies again
    path.write_text(text)
    assert DailyJournalWriter.verify_chain(path)["rows"] == 4


def test_leak_scan_counter_test_poisoned_field_must_fail(tmp_path):
    """RGC-INC-1 counter-test: a poisoned performance-named field anywhere
    in a row (top level OR nested) MUST fail the write."""
    path = tmp_path / "journal.jsonl"
    writer = _write_eurusd_journal(path)
    good = __import__("json").loads(
        [l for l in path.read_text().splitlines() if l][1])
    writer.close()

    for poison_key, poison_val in [
        ("net_pnl_usd", 1.0),
        ("gross_pnl", 2.0),
        ("pnl", 3.0),
        ("sharpe_ratio", 0.5),
        ("max_drawdown", 0.1),
        ("equity_delta", 7.0),
        ("equity_delta_quoteccy", 7.0),
        ("portfolio_return", 0.01),
        ("profit_factor", 1.2),
    ]:
        w2 = DailyJournalWriter(tmp_path / "poison.jsonl",
                                cycle_id="C", fold_id="F", run_label="r")
        bad = dict(good)
        bad[poison_key] = poison_val
        with pytest.raises(LeakLawViolation):
            w2.write_row(bad)
        w2.close()

    # nested poison (inside the outcome/guard block)
    w3 = DailyJournalWriter(tmp_path / "poison2.jsonl", cycle_id="C",
                            fold_id="F", run_label="r")
    bad = dict(good)
    bad["outcome_block"] = {"equity_delta": 1.0}
    with pytest.raises(LeakLawViolation):
        w3.write_row(bad)
    w3.close()

    # the scan itself: direct unit check
    assert jrn.scan_keys_for_leaks({"net_pnl_usd": 1}) == ["net_pnl_usd"]
    assert jrn.scan_keys_for_leaks({"a": [{"pf": 1}]}) == ["a[0].pf"]
    assert jrn.scan_keys_for_leaks(
        {"spread_once_total": 1, "cash_delta_usd": 2,
         "entry_reason_code": "X"}) == []


def test_journal_determinism_byte_identical_rerun(tmp_path):
    p1, p2 = tmp_path / "run1.jsonl", tmp_path / "run2.jsonl"
    _write_eurusd_journal(p1).close()
    _write_eurusd_journal(p2).close()
    assert p1.read_bytes() == p2.read_bytes()


def test_pit_next_business_day_law(tmp_path):
    """OI-1: available_time MUST be the next business day after the
    consumed D1 bar (weekend skip); violations fail the write."""
    assert next_business_day("2026-05-06") == "2026-05-07"  # Wed -> Thu
    assert next_business_day("2026-05-08") == "2026-05-11"  # Fri -> Mon
    assert next_business_day("2026-05-09") == "2026-05-11"  # Sat -> Mon

    kernel = DeclaredCostKernel("EURUSD", tier=1.0)
    book = QuoteCcyBook("EURUSD", kernel, opening_usd=OPENING_USD,
                        open_ts="2026-05-04T00:00:00Z", open_rate_to_usd="1.0")
    rec = book.apply_fill("2026-05-04T17:00:00Z", EUR_BAR_1, "BUY", 100000,
                          rate_to_usd="1.0")
    fq = kernel.price_fill(EUR_BAR_1, "BUY", 100000)
    good = _trade_row(rec, fq, "OPEN", "ORD-0001")

    w = DailyJournalWriter(tmp_path / "pit.jsonl", cycle_id="C",
                           fold_id="F", run_label="r")
    w.write_row(good)  # consumed Fri 2026-05-01 -> available Mon 05-04

    for bad_avail in ("2026-05-01T00:00:00Z",   # same day (lookahead)
                      "2026-05-02T00:00:00Z",   # Saturday
                      "2026-05-03T00:00:00Z",   # Sunday
                      "2026-05-05T00:00:00Z"):  # too late (not next bd)
        bad = dict(good)
        bad["order_id"] = "ORD-BAD"
        bad["feature_pit_snapshot"] = [
            _pit("I-EUR", "2026-05-01", bad_avail)]
        with pytest.raises(JournalValidationError, match="OI-1"):
            w.write_row(bad)
    w.close()


def test_journal_conversion_roundtrip_and_deferred_row(tmp_path):
    """cash_delta_usd must reconcile with the conversion row; a
    DEFERRED_COST_GUARD row may carry the DEFER order_kind + guard block
    (spec §8); a wrong usd delta fails."""
    kernel = DeclaredCostKernel("EURUSD", tier=1.0)
    book = QuoteCcyBook("EURUSD", kernel, opening_usd=OPENING_USD,
                        open_ts="2026-05-04T00:00:00Z", open_rate_to_usd="1.0")
    rec = book.apply_fill("2026-05-04T17:00:00Z", EUR_BAR_1, "BUY", 100000,
                          rate_to_usd="1.0")
    fq = kernel.price_fill(EUR_BAR_1, "BUY", 100000)
    good = _trade_row(rec, fq, "OPEN", "ORD-0001")

    w = DailyJournalWriter(tmp_path / "conv.jsonl", cycle_id="C",
                           fold_id="F", run_label="r")
    w.write_row(good)
    bad = dict(good)
    bad["order_id"] = "ORD-BAD"
    bad["cash_delta_usd"] = bad["cash_delta_usd"] + 1.0
    with pytest.raises(JournalValidationError, match="conversion row"):
        w.write_row(bad)

    deferred = _base_decision("EURUSD", "2026-05-05T00:00:00Z", [
        _pit("I-EUR", "2026-05-04", "2026-05-05T00:00:00Z")])
    deferred.update({
        "record_kind": jrn.RECORD_KIND_BLOCKED,
        "outcome": jrn.OUTCOME_DEFERRED_COST_GUARD,
        "order_kind": "DEFER",
        "blocked_reason_detail": "cost guard: trailing spend at cap",
        "cost_guard": {"window": "20d", "cap_usd": 50.0,
                       "trailing_spend_usd": 50.0},
        "pre_commit_estimate": {"est_spread_once": 10.0, "est_slip": 2.0,
                                "est_commission": 3.85, "est_total": 15.85},
    })
    w.write_row(deferred)  # lawful DEFER block

    netted = _base_decision("EURUSD", "2026-05-06T00:00:00Z", [
        _pit("I-EUR", "2026-05-05", "2026-05-06T00:00:00Z")])
    netted.update({
        "record_kind": jrn.RECORD_KIND_BLOCKED,
        "outcome": jrn.OUTCOME_NETTED_TO_ZERO,
        "blocked_reason_detail": "tie at zero: nonzero votes, net 0",
    })
    w.write_row(netted)

    # a DEFER order_kind on a NON-deferred blocked outcome is unlawful
    bad2 = dict(netted)
    bad2["order_kind"] = "DEFER"
    with pytest.raises(JournalValidationError, match="DEFER"):
        w.write_row(bad2)
    # blocked rows may never carry fill keys even with value 0
    bad3 = dict(netted)
    bad3["fill_price"] = 0.0
    with pytest.raises(JournalValidationError, match="fill"):
        w.write_row(bad3)
    w.close()
    assert DailyJournalWriter.verify_chain(tmp_path / "conv.jsonl")["rows"] == 4


def test_usdquote_book_rejects_nonunity_rate_and_bad_tier():
    kernel = DeclaredCostKernel("EURUSD")
    with pytest.raises(ValueError, match="USD-quoted"):
        QuoteCcyBook("EURUSD", kernel, opening_usd=OPENING_USD,
                     open_ts="2026-05-04T00:00:00Z", open_rate_to_usd="0.99")
    with pytest.raises(ValueError, match="STRESS_TIERS"):
        DeclaredCostKernel("EURUSD", tier=1.25)
    with pytest.raises(ValueError):
        DeclaredCostKernel("XYZUSD")
    # event-window slip is the 1.0 pip U3 band
    ev = DeclaredCostKernel("EURUSD", event_window=True)
    fq = ev.price_fill(EUR_BAR_1, "BUY", 100000)
    assert fq.fill_price == Decimal("1.10030")  # 1.10010 + 0.00010 + 0.0001
    assert fq.slippage_band_id.endswith("EVENT-DECLARED")


# ---------------------------------------------------------------------------
# Exploratory battery rule tests (DS-03 / DS-05) — synthetic inputs only.
# Corpus-parameter fidelity is asserted against the frozen constants; every
# expected value below is hand-computed in the comments. No real panel is
# read (RGC-INC-1: no performance field anywhere).
# ---------------------------------------------------------------------------

from daily_exploratory import rules as rls  # noqa: E402


class TestDS03CorpusFidelity:
    """USDJPY-S065 verbatim: NATGAS 10d ret > +15% khi Brent flat; long
    USDJPY 5 phien; stop 1xATR; grid B=3% (default) / C=5% / A=off."""

    def test_frozen_constants(self):
        assert str(rls.DS03_NG_TRIGGER) == "0.15"      # corpus "+15%"
        assert rls.DS03_NG_WINDOW == 10                # corpus "10d ret"
        assert rls.DS03_BRENT_WINDOW == 10
        assert str(rls.DS03_GRID["B"]) == "0.03"       # G1 node B 3%
        assert str(rls.DS03_GRID["C"]) == "0.05"       # G1 node C 5%
        assert rls.DS03_GRID["A"] is None              # null-control (off)
        assert rls.DS03_GRID_DEFAULT == "B"            # G7 frozen default
        assert rls.DS03_GRID_SELECTABLE == ("B", "C")  # A never selectable
        assert rls.DS03_HOLD_SESSIONS == 5             # "5 phien"
        assert str(rls.DS03_STOP_ATR_MULT) == "1"      # "stop 1xATR"
        assert rls.ATR_WINDOW == 14                    # declared ATR-14

    def _x(self, ng, br, atr="1.0"):
        return rls.DS03Inputs("T", Decimal(ng), Decimal(br), Decimal(atr))

    def test_entry_positive_when_natgas_breaks_and_brent_flat(self):
        # ng +16% > +15%, |brent +1%| < 3% -> entry at node B
        rule = rls.DS03Rule()
        assert rule.entry_signal(self._x("0.16", "0.01"), "B") is True

    def test_no_entry_below_trigger(self):
        # ng +15% exactly = NOT > +15% -> no entry (strict corpus inequality)
        assert rls.DS03Rule().entry_signal(self._x("0.15", "0.00"), "B") is False

    def test_brent_flat_gate_blocks_when_brent_runs(self):
        # brent +4%: node B (3%) blocks; node C (5%) admits; node A admits
        rule = rls.DS03Rule()
        x = self._x("0.20", "0.04")
        assert rule.entry_signal(x, "B") is False      # "neu Brent cung chay"
        assert rule.entry_signal(x, "C") is True
        assert rule.entry_signal(x, "A") is True       # null-control off

    def test_brent_negative_side_also_blocks(self):
        # brent -4% (|ret| 4%): channel NOT flat at node B
        assert rls.DS03Rule().entry_signal(self._x("0.20", "-0.04"), "B") is False

    def test_stop_level_one_atr_below_fill(self):
        # fill 150.00, ATR 2.0 -> stop 148.00 (1xATR)
        rule = rls.DS03Rule()
        lvl = rule.stop_level(Decimal("150.00"), self._x("0.20", "0.00", "2.0"))
        assert lvl == Decimal("148.00")

    def test_exits_due_stop_first_then_hold(self):
        rule = rls.DS03Rule()
        # low breaches stop -> STOP regardless of hold count
        assert rule.exits_due(2, Decimal("148.0"), Decimal("148.5")) == \
            (rls.EXIT_REASON_STOP, "low<=stop")
        # 5 held sessions, stop intact -> HOLD
        assert rule.exits_due(5, Decimal("148.5"), Decimal("148.0")) == \
            (rls.EXIT_REASON_HOLD, "5 phien")
        # 4 held sessions, stop intact -> no exit
        assert rule.exits_due(4, Decimal("148.5"), Decimal("148.0")) is None


class TestDS05CorpusFidelity:
    """EURUSD-S006 verbatim: rank 20d return of {EUR,GBP,AUD,NZD,CHF,JPY,
    CAD} vs USD; long EURUSD only when EUR rank 1-2; 2-consecutive-week
    consistency; exit out of top-3; stop 2xATR."""

    def test_frozen_constants(self):
        assert rls.DS05_RANK_WINDOW == 20             # corpus "20d"
        assert rls.DS05_ENTRY_RANK_MAX == 2           # "EUR rank 1-2"
        assert rls.DS05_EXIT_RANK_MAX == 3            # "roi khoi top-3"
        assert rls.DS05_CONSISTENCY_SESSIONS == 5     # 1 week = 5 sessions
        assert str(rls.DS05_STOP_ATR_MULT) == "2"     # "stop 2xATR"
        assert set(rls.DS05_CURRENCIES) == \
            {"EUR", "GBP", "AUD", "NZD", "CHF", "JPY", "CAD"}

    def _x(self, eur, gbp="0.01", jpy_pair="-0.02", atr="0.0100",
           hist=(1, 1, 1, 1, 1, 1)):
        # EUR strongest; JPY pair quoted USDJPY with pair-return -2% means
        # JPY vs USD +~2% via INVERSE_RET (approximate here for ranking)
        ret20 = {"EUR": Decimal(eur), "GBP": Decimal(gbp),
                 "AUD": Decimal("0.005"), "NZD": Decimal("0.004"),
                 "CHF": Decimal("-0.001"), "JPY": Decimal("0.02"),
                 "CAD": Decimal("0.003")}
        return rls.DS05Inputs("T", ret20, Decimal(atr), tuple(hist))

    def test_rank_order_strongest_is_1(self):
        x = self._x("0.03")
        ranks = x.ranks()
        assert ranks["EUR"] == 1                       # strongest vs USD
        assert x.eur_rank() == 1

    def test_rank_tie_break_lexicographic(self):
        ret20 = {c: Decimal("0.01") for c in rls.DS05_CURRENCIES}
        x = rls.DS05Inputs("T", ret20, Decimal("0.01"), tuple())
        # all tied: AUD 1, CAD 2, CHF 3, EUR 4 (lexicographic tie-break)
        assert x.eur_rank() == 4

    def test_entry_needs_rank_top2_now_and_one_week_earlier(self):
        rule = rls.DS05Rule()
        x = self._x("0.03", hist=(1, 1, 1, 1, 1, 1))   # now 1, week ago 1
        assert rule.entry_signal(x, rule.prior_week_rank(x)) is True
        # week-ago rank 3 -> consistency fails (coupling = entry law)
        x2 = self._x("0.03", hist=(3, 3, 3, 3, 3, 1))
        assert rule.entry_signal(x2, rule.prior_week_rank(x2)) is False
        # rank 3 now -> no entry regardless of history
        x3 = self._x("-0.01", hist=(1, 1, 1, 1, 1, 1))
        assert rule.entry_signal(x3, rule.prior_week_rank(x3)) is False

    def test_prior_week_rank_reads_six_back(self):
        rule = rls.DS05Rule()
        x = self._x("0.03", hist=(7, 1, 1, 1, 1, 2))   # h[-6] = 7
        assert rule.prior_week_rank(x) == 7
        x2 = self._x("0.03", hist=(1,))                # too short -> None
        assert rule.prior_week_rank(x2) is None

    def test_exit_when_out_of_top3(self):
        rule = rls.DS05Rule()
        assert rule.exit_signal(self._x("0.03")) is False   # rank 1
        weak = self._x("-0.05")                             # rank 7
        assert rule.exit_signal(weak) is True

    def test_stop_level_two_atr_below_fill(self):
        # fill 1.0500, ATR 0.0100 -> stop 1.0300 (2xATR)
        rule = rls.DS05Rule()
        lvl = rule.stop_level(Decimal("1.0500"), self._x("0.03", atr="0.0100"))
        assert lvl == Decimal("1.0300")


class TestReturnHelpers:
    """ret_over / inverse_ret_over on hand-built series."""

    def test_ret_over_own_calendar(self):
        dates = ["d1", "d2", "d3", "d4", "d5", "d6", "d7", "d8", "d9",
                 "d10", "d11"]
        vals = {f"d{i}": Decimal(100 + i) for i in range(1, 12)}
        # window 10 at d11: 111/101 - 1
        assert rls.ret_over(dates, vals, 10, "d11") == Decimal(111) / Decimal(101) - 1
        assert rls.ret_over(dates, vals, 10, "d5") is None   # insufficient history
        assert rls.ret_over(dates, vals, 10, "nope") is None  # absent date

    def test_inverse_ret_over(self):
        # USDJPY-style: value of JPY in USD rises when the pair falls.
        dates = ["d1", "d2", "d3", "d4", "d5", "d6", "d7", "d8", "d9",
                 "d10", "d11"]
        vals = {f"d{i}": Decimal(100 + i) for i in range(1, 12)}
        # inverse 10d ret at d11 = P[d1]/P[d11] - 1 = 101/111 - 1 (negative)
        assert rls.inverse_ret_over(dates, vals, 10, "d11") == \
            Decimal(101) / Decimal(111) - 1


class TestBatteryCalendarLaw:
    """Frozen fold calendar arithmetic (PLAN section 2.2)."""

    def test_fold_dates_verbatim(self):
        import daily_exploratory.battery as bt
        assert bt.FOLDS[0] == (1, "2022-09-30", "2023-03-30")
        assert bt.FOLDS[7] == (8, "2026-03-27", "2026-09-24")
        assert len(bt.FOLDS) == 8
        assert bt.LEARN == ("2021-10-01", "2022-09-22")
        assert bt.EMBARGO == ("2022-09-23", "2022-09-29")
        assert bt.WARMUP == ("2020-10-02", "2021-09-30")

    def test_freshness_law(self):
        import daily_exploratory.battery as bt
        # freshest consumable: newest bar servable at the decision session
        assert bt.freshest_consumable(
            ["2022-09-29", "2022-09-30"], "2022-10-03") == "2022-09-30"
        # serving-day within one business day (source holiday typed fresh)
        assert bt.age_ok("2022-09-30", "2022-10-03") is True
        # Friday bar serving Monday, decided Tuesday (Monday holiday):
        assert bt.age_ok("2022-09-30", "2022-10-04") is True
        # Thursday bar decided the following Tuesday: 2bd stale
        assert bt.age_ok("2022-09-29", "2022-10-04") is False
        # Friday bar serving Monday on a Monday-holiday Tuesday decision
        assert bt.age_ok("2022-12-23", "2022-12-27") is True

    def test_atr14_wilder_hand_case(self):
        import daily_exploratory.battery as bt
        from daily_exploratory.datainputs import D1Bar
        # 15 flat sessions: TR = 1 every day; SMA(14) seed = 1 -> ATR 1
        bars = {f"d{i}": D1Bar(f"d{i}", 10.0, 10.1, 9.9, 10.0, 9.95, 10.05)
                for i in range(15)}
        # mid_high-mid_low = 10.05-9.95 = 0.1 ... build exact TR=0.1 case:
        bars = {f"d{i}": D1Bar(f"d{i}", 10.0, 10.0, 10.0, 10.0, 9.95, 10.05)
                for i in range(15)}
        out = bt.atr14_wilder(bars, list(bars))
        # all TRs = 0.1 (high-low only, closes flat) -> ATR = 0.1 exactly
        assert out["d14"] == Decimal("0.1")
        assert out["d13"] == Decimal("0.1")            # first ATR at 14 TRs
        assert "d12" not in out                        # needs 14 TRs
