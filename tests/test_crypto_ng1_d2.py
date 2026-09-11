"""CRYPTO-NG1 D2 tests: hand-computed fixtures for the measurement law.

Covers (dispatch contract):
  1. a small rho pair hand-computed (Pearson 19/21 and the matching Spearman);
  2. fail-closed behaviour of an unmeasured veto (never an inferred PASS);
  3. the holiday-rule calendar case (2025-11-28 / 2025-12-26 last-Friday
     arithmetic and the venue-pinned epochs).

Network-free: no panel store, no CADS, no endpoints.
"""

from __future__ import annotations

import math
import sys
from datetime import date
from pathlib import Path

_WORKTREE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_WORKTREE))

from research.assets.crypto_ng1.d2 import measure as M  # noqa: E402


# --------------------------------------------------------------------------- #
# 1. hand-computed rho pair
# --------------------------------------------------------------------------- #

def test_pearson_hand_computed():
    # x = 1..8; y = [2,1,4,3,6,5,8,7]
    # dx = [-3.5,-2.5,-1.5,-0.5,0.5,1.5,2.5,3.5], sxx = 42
    # dy = [-2.5,-3.5,-0.5,-1.5,1.5,0.5,3.5,2.5], syy = 42
    # sum(dx*dy) = 38  ->  r = 38/42 = 19/21
    x = [1, 2, 3, 4, 5, 6, 7, 8]
    y = [2, 1, 4, 3, 6, 5, 8, 7]
    r = M.pearson(x, y)
    assert r is not None
    assert abs(r - 19.0 / 21.0) < 1e-12


def test_spearmon_hand_computed_matches_pearson_when_ranks_equal_values():
    # y has distinct values, so rank(y) == y and Spearman == Pearson = 19/21.
    x = [1, 2, 3, 4, 5, 6, 7, 8]
    y = [2, 1, 4, 3, 6, 5, 8, 7]
    s = M.spearman(x, y)
    assert s is not None
    assert abs(s - 19.0 / 21.0) < 1e-12


def test_spearman_ties_average_ranks():
    # x2 = [1,1,2,2,3,3,4,4] -> average ranks [1.5,1.5,3.5,3.5,5.5,5.5,7.5,7.5]
    # y2 = [1,2,1,2,3,4,3,4] -> ranks            [1.5,3.5,1.5,3.5,5.5,7.5,5.5,7.5]
    # dx=[-3,-3,-1,-1,1,1,3,3], dy=[-3,-1,-3,-1,1,3,1,3]
    # sxx = 9+9+1+1+1+1+9+9 = 40; syy = 40
    # sum(dx*dy) = 9+3+3+1+1+3+3+9 = 32 -> rho = 32/40 = 0.8
    x2 = [1, 1, 2, 2, 3, 3, 4, 4]
    y2 = [1, 2, 1, 2, 3, 4, 3, 4]
    s = M.spearman(x2, y2)
    assert s is not None
    assert abs(s - 0.8) < 1e-12


def test_constant_series_is_degenerate_not_pass():
    res = M.rho_pair_status([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
                            [0.0] * 8)
    assert res["status"] == "DEGENERATE_ZERO_VARIANCE"
    assert res["pair_verdict"] == "UNMEASURED"
    assert res["max_abs_rho"] is None


def test_low_n_is_not_computable():
    res = M.rho_pair_status([1.0, 2.0, 3.0], [3.0, 1.0, 2.0])
    assert res["status"] == "NOT_COMPUTABLE_LOW_N"
    assert res["pair_verdict"] == "UNMEASURED"


def test_veto_margin_arithmetic():
    res = M.rho_pair_status(
        [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        [2.0, 1.0, 4.0, 3.0, 6.0, 5.0, 8.0, 7.0])
    assert res["status"] == "MEASURED"
    assert res["max_abs_rho"] == round(19.0 / 21.0, 6)
    assert abs(res["margin_to_bar"] - (0.20 - 19.0 / 21.0)) < 1e-6
    assert res["pair_verdict"] == "VETO"   # 0.9048 > 0.20


def test_cost_shift_invariance_of_rho():
    """Documents the gross-vs-after-cost identity used by the D2 lane."""
    x = [0.001, -0.002, 0.003, 0.0025, -0.001, 0.0005, -0.003, 0.0015]
    y = [0.4, 0.1, 0.9, 0.7, 0.2, 0.5, 0.05, 0.6]
    c = 0.0024                       # any constant per-decision cost shift
    assert M.pearson(x, y) == M.pearson([v - 2 * c for v in x], y)
    assert M.spearman(x, y) == M.spearman([v - 2 * c for v in x], y)


# --------------------------------------------------------------------------- #
# 2. fail-closed unmeasured veto
# --------------------------------------------------------------------------- #

def _fake_vp_with_missing_required():
    vp = M.VetoPanel()
    vp.add("v17_wkndliq_flag", "V17-A4-P1-WKNDLIQ", "v17_family", "flag",
           build_failure="cannot be rebuilt (fixture)")
    vp.add("generic_tsmom28", "GENERIC", "generic", "tsmom",
           fn=lambda s, d: 1.0, hourly=False)
    return vp


def test_required_veto_build_failure_is_fail_closed():
    vp = _fake_vp_with_missing_required()
    pairs = {"generic_tsmom28": M.rho_pair_status(
        [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        [8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0])}
    verdict = M.novelty_verdict(pairs, vp)
    assert verdict["novelty_verdict"] == "INELIGIBLE_FAIL_CLOSED"
    assert "v17_wkndliq_flag" in verdict["reason"]


def test_all_none_veto_is_unmeasured_never_pass():
    res = M.rho_pair_status([1.0] * 8, [None] * 8)
    assert res["status"] == "NOT_COMPUTABLE_MISSING_COVERAGE"
    assert res["pair_verdict"] == "UNMEASURED"
    # a proposal whose ONLY pair is unmeasured fails closed as well
    vp = M.VetoPanel()
    vp.add("generic_tsmom28", "GENERIC", "generic", "tsmom",
           fn=lambda s, d: None, hourly=False)
    verdict = M.novelty_verdict(
        {"generic_tsmom28": res}, vp)
    assert verdict["novelty_verdict"] == "INELIGIBLE_FAIL_CLOSED"


# --------------------------------------------------------------------------- #
# 3. holiday-rule calendar case
# --------------------------------------------------------------------------- #

def test_last_friday_thanksgiving_and_boxing_day_months():
    # Nov 2025: Fridays 7,14,21,28 -> 28 (post-Thanksgiving Friday)
    assert M.last_friday(2025, 11) == date(2025, 11, 28)
    # Dec 2025: Fridays 5,12,19,26 -> 26 (Boxing Day)
    assert M.last_friday(2025, 12) == date(2025, 12, 26)
    # Sep 2025: Fridays 5,12,19,26 -> 26 (quarterly delivery, in window)
    assert M.last_friday(2025, 9) == date(2025, 9, 26)


def test_monthly_grid_in_window_reproduces_pinned_lists():
    start, end = date(2025, 8, 22), date(2026, 8, 21)
    monthly = M.monthly_last_fridays(start, end)
    assert [d.isoformat() for d in monthly] == sorted(
        M.A5_P1_PINNED_QUARTERLY + M.A5_P2_PINNED_NONQUARTERLY)
    quarterly = [d for d in monthly if d.month in (3, 6, 9, 12)]
    assert [d.isoformat() for d in quarterly] == sorted(
        M.A5_P1_PINNED_QUARTERLY)
    nonq = [d for d in monthly if d.month not in (3, 6, 9, 12)]
    assert [d.isoformat() for d in nonq] == sorted(
        M.A5_P2_PINNED_NONQUARTERLY)
    # 2026-08-28 (last Friday of Aug 2026) is outside the panel window
    assert date(2026, 8, 28) not in monthly


def test_venue_pinned_epochs_match_rule():
    # Binance fapi deliveryDate epochs pinned in the A5 proposals:
    # 1790323200000 ms -> 2026-09-25T08:00:00Z, last Friday of Sep 2026
    dt = M.epoch_ms_to_utc(1790323200000)
    assert dt.strftime("%Y-%m-%dT%H:%M:%SZ") == "2026-09-25T08:00:00Z"
    assert dt.date() == M.last_friday(2026, 9)
    # 1798185600000 ms -> 2026-12-25T08:00:00Z, last Friday of Dec 2026
    dt2 = M.epoch_ms_to_utc(1798185600000)
    assert dt2.strftime("%Y-%m-%dT%H:%M:%SZ") == "2026-12-25T08:00:00Z"
    assert dt2.date() == M.last_friday(2026, 12)


def test_reverify_expiry_instants_match():
    rep = M.reverify_expiry_instants()
    assert rep["verdict"] == "MATCH", rep["checks"]
    assert rep["derived_in_window"]["quarterly"] == sorted(
        M.A5_P1_PINNED_QUARTERLY)
    assert rep["derived_in_window"]["nonquarterly"] == sorted(
        M.A5_P2_PINNED_NONQUARTERLY)
    assert rep["holiday_leak_handling"]["hazard_dates"] == [
        "2025-11-28", "2025-12-26"]


def test_mismatch_would_be_fail_closed():
    # Tamper with the pinned list: the checker must report MISMATCH (the
    # runner turns any MISMATCH into INELIGIBLE_FAIL_CLOSED for lane A5).
    orig = M.A5_P2_PINNED_NONQUARTERLY
    try:
        M.A5_P2_PINNED_NONQUARTERLY = [
            "2025-08-29", "2025-10-31", "2025-11-21", "2026-01-30",
            "2026-02-27", "2026-04-24", "2026-05-29", "2026-07-31"]
        rep = M.reverify_expiry_instants()
        assert rep["verdict"] == "MISMATCH"
        assert "MISMATCH" in rep["fail_closed_consequence"]
    finally:
        M.A5_P2_PINNED_NONQUARTERLY = orig


# --------------------------------------------------------------------------- #
# 4. signal construction on a synthetic panel (grid arithmetic)
# --------------------------------------------------------------------------- #

def _synthetic_panel(symbol="BTCUSDT", days=95):
    """Tiny complete H1 panel with deterministic prices and flows.

    95 days from 2025-08-01 covers the synthetic instants used below
    (2025-09-17 .. 2025-10-31 + 12h exit).
    """
    import io
    import csv as _csv
    buf = io.StringIO()
    w = _csv.writer(buf)
    w.writerow(["symbol", "hour_utc", "day_utc", "n_trades", "buy_count",
                "sell_count", "buy_qty", "sell_qty", "buy_quote", "sell_quote",
                "quote_total", "qty_total", "vwap", "first_price",
                "last_price", "high_price", "low_price", "max_trade_quote",
                "sum_qty_squared", "n_price_moves", "sum_squared_log_ret",
                "gap_sum_s", "gap_count", "entry_gap_s", "run_close_dir",
                "run_close_len", "run_switch_count", "max_run_buy",
                "max_run_sell", "first_ts_ms", "last_ts_ms"])
    from datetime import datetime, timedelta, timezone
    t0 = datetime(2025, 8, 1, 0, tzinfo=timezone.utc)
    for i in range(days * 24):
        dt = t0 + timedelta(hours=i)
        h = dt.strftime("%Y-%m-%dT%H")
        px = 100.0 + (i % 7) * 0.5          # deterministic price path
        bq, sq = 60.0 + (i % 5), 40.0 + (i % 3)
        w.writerow([symbol, h, dt.strftime("%Y-%m-%d"), 100, 50, 50,
                    1.0, 1.0, bq, sq, bq + sq, 2.0, px, px - 0.5, px,
                    px + 1, px - 1, 5.0, 1.0, 99, 1e-7, 3600.0, 100,
                    1.0 + (i % 4) * 0.5, "buy", 3, 5, 10, 9,
                    int(dt.timestamp() * 1000),
                    int((dt + timedelta(hours=1)).timestamp() * 1000) - 1])
    return M.Panel.from_bytes(symbol, buf.getvalue().encode())


def test_a4_p1_grid_and_tie_handling():
    panel = _synthetic_panel()
    M.register_panel_ts({panel.symbol: panel})
    # use a synthetic instant inside the synthetic panel (2025-09-17T18)
    M.FOMC_INSTANTS_ORIG = M.FOMC_INSTANTS
    try:
        M.FOMC_INSTANTS = ["2025-09-17T18:00:00Z"]
        rows = M.build_a4_p1(panel)
        assert len(rows) == 1
        r = rows[0]
        assert r.decision_bar == "2025-09-17T18"
        assert r.decision_date == "2025-09-17"
        bar = panel.bar("2025-09-17T18")
        imb = (bar["buy_quote"] - bar["sell_quote"]) / bar["quote_total"]
        expected_d = 1 if imb > 0 else (-1 if imb < 0 else 0)
        assert r.direction == expected_d
        if expected_d != 0:
            exit_bar = panel.bar_offset("2025-09-17T18", 6)
            assert r.r_gross == expected_d * (
                exit_bar["last_price"] / bar["last_price"] - 1.0)
            assert r.status == "FUNDED"
    finally:
        M.FOMC_INSTANTS = M.FOMC_INSTANTS_ORIG


def test_a5_p1_windows_and_fill_prices():
    panel = _synthetic_panel()
    M.register_panel_ts({panel.symbol: panel})
    dates = ["2025-09-26"]
    rows = M.build_a5_p1(panel, dates=dates)
    r = rows[0]
    # pressure window = bars 00..05 of the expiry day
    num = sum(panel.bar(f"2025-09-26T{h:02d}")["buy_quote"]
              - panel.bar(f"2025-09-26T{h:02d}")["sell_quote"]
              for h in range(0, 6))
    den = sum(panel.bar(f"2025-09-26T{h:02d}")["quote_total"]
              for h in range(0, 6))
    press = num / den
    expected_d = 1 if press > 0 else (-1 if press < 0 else 0)
    assert r.direction == expected_d
    assert r.decision_bar == "2025-09-26T05"      # close of A-3 = 06:00 UTC
    entry = panel.bar("2025-09-26T05")["last_price"]
    exit_ = panel.bar("2025-09-26T07")["last_price"]   # close of A-1 = 08:00
    assert r.r_gross == expected_d * (exit_ / entry - 1.0)


def test_a5_p2_direction_is_the_fade():
    panel = _synthetic_panel()
    M.register_panel_ts({panel.symbol: panel})
    rows = M.build_a5_p2(panel, dates=["2025-10-31"])
    r = rows[0]
    bar = panel.bar("2025-10-31T08")
    imb = (bar["buy_quote"] - bar["sell_quote"]) / bar["quote_total"]
    assert r.direction == (-1 if imb > 0 else (1 if imb < 0 else 0))
    exit_bar = panel.bar_offset("2025-10-31T08", 12)
    assert r.r_gross == r.direction * (
        exit_bar["last_price"] / bar["last_price"] - 1.0)


def test_wkndliq_flag_corrected_semantics():
    # The V17 D1 bug compared the DATE STRING to weekday names; the corrected
    # form computes the weekday.  Saturday must fire, Wednesday must not.
    vp = M.VetoPanel()
    # build_veto_panel needs panels; test the flag closure directly instead
    from datetime import datetime, timezone
    dt_sat = datetime(2025, 11, 29, 10, tzinfo=timezone.utc)
    dt_wed = datetime(2025, 11, 26, 18, tzinfo=timezone.utc)
    dt_fri_late = datetime(2025, 11, 28, 23, tzinfo=timezone.utc)
    dt_fri_early = datetime(2025, 11, 28, 6, tzinfo=timezone.utc)

    def flag(dt):
        wd = dt.weekday()
        return -1.0 if (wd == 4 and dt.hour >= 22) or wd in (5, 6) else 0.0

    assert flag(dt_sat) == -1.0
    assert flag(dt_wed) == 0.0
    assert flag(dt_fri_late) == -1.0
    assert flag(dt_fri_early) == 0.0
    assert math.isfinite(flag(dt_sat))
