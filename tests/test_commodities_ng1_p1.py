"""COMMODITIES-NG1 P1 gate tests (offline; no network).

Every assertion is hand-computed on synthetic fixtures (exact CS
algebra, exact divergence literals, degenerate dual-book ledgers, DST
clock arithmetic, PIT instants) or re-verifies a committed P1 artifact
against the committed P0 substrate (cost-contract consistency, fee-fact
digest pins, real-calendar decision grid).  No scored computation and
no outcome numbers anywhere.
"""

from __future__ import annotations

import csv
import json
import math
import os
import sys
from datetime import date, datetime, timedelta, timezone

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

RUN_DIR = os.path.join(REPO_ROOT, "research", "control",
                       "commodities_ng1_run")

from research.accounting import (  # noqa: E402  (root kernel module)
    AccountingFieldError,
    TERMINAL_POLICY,
    build_accounting_reconciliation,
    map_to_canonical,
)
from research.assets.commodities_ng1 import clock as K  # noqa: E402
from research.assets.commodities_ng1 import costs as C  # noqa: E402
from research.assets.commodities_ng1 import kernel as KX  # noqa: E402
from research.assets.commodities_ng1.cot_census import (  # noqa: E402
    CotLookupRefused, pit_guard, release_instant as p0_release_instant,
)


def _load(name):
    with open(os.path.join(RUN_DIR, name), encoding="utf-8") as fh:
        return json.load(fh)


def _bar(d, high, low, close, adj=None):
    return {"date": d, "high": high, "low": low, "close": close,
            "adj_close": close if adj is None else adj}


# --------------------------------------------------------------------- #
# 1. Corwin-Schultz synthetic OHLC (exact algebra)
# --------------------------------------------------------------------- #

def test_cs_exact_spread_two_identical_days():
    # H=L*10/9 on both days => beta = 2*ln(10/9)^2, gamma = ln(10/9)^2,
    # and alpha reduces EXACTLY to ln(10/9):
    #   (sqrt(2b)-sqrt(b))/K with b=2g equals L*(2+sqrt(2));
    #   sqrt(g/K) equals L*(sqrt(2)+1); difference = L*(1) = L.
    # S = 2*(e^L - 1)/(1 + e^L) with e^L = 10/9 => 2/19 exactly.
    bars = [_bar(date(2026, 1, 5), 100.0, 90.0, 95.0),
            _bar(date(2026, 1, 6), 100.0, 90.0, 95.0)]
    windows, excluded = C.corwin_schultz_daily_spreads(bars)
    assert excluded == 0
    assert len(windows) == 1
    assert abs(windows[0]["spread_frac"] - 2.0 / 19.0) < 1e-12
    assert windows[0]["clipped"] is False


def test_cs_negative_alpha_clipped_at_zero():
    # Overnight gap DOWN between two narrow-range days: gamma (2-day
    # max/min range) dominates beta => alpha < 0 => clipped at 0.
    bars = [_bar(date(2026, 1, 5), 100.0, 99.5, 99.8),
            _bar(date(2026, 1, 6), 90.0, 89.5, 89.8)]
    windows, _ = C.corwin_schultz_daily_spreads(bars)
    assert windows[0]["alpha"] < 0.0
    assert windows[0]["spread_frac"] == 0.0
    assert windows[0]["clipped"] is True


def test_percentile_linear_definition_hand_computed():
    # numpy 'linear' convention: p = q*(n-1); v[8] + 0.1*(v[9]-v[8]).
    vals = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    assert abs(C.percentile_linear(vals, 0.9) - 0.91) < 1e-12
    assert C.percentile_linear([2.0 / 19.0], 0.9) == 2.0 / 19.0


def test_cs_refuses_malformed_bars():
    with pytest.raises(C.CostMeasurementRefused):
        C.corwin_schultz_daily_spreads(
            [_bar(date(2026, 1, 5), 90.0, 100.0, 95.0),   # high < low
             _bar(date(2026, 1, 6), 100.0, 90.0, 95.0)])
    with pytest.raises(C.CostMeasurementRefused):
        C.corwin_schultz_daily_spreads(
            [_bar(date(2026, 1, 5), 100.0, 90.0, 95.0)])


# --------------------------------------------------------------------- #
# 2. Roll cross-check (hand-constructed mean reversion)
# --------------------------------------------------------------------- #

def test_roll_cross_check_hand_constructed():
    # closes [100,99,100,99,100]: dp = [-1,+1,-1,+1], mean 0;
    # paired products (dp[1:], dp[:-1]) sum to -3 over m=3 pairs;
    # unbiased cov divides by m-1 = 2 => cov = -1.5 exactly;
    # s = 2*sqrt(1.5) price units; frac = s / mean_close (99.6).
    bars = [_bar(date(2026, 1, d), 0, 0, c) for d, c in
            ((5, 100.0), (6, 99.0), (7, 100.0), (8, 99.0), (9, 100.0))]
    out = C.roll_spread_cross_check(bars)
    assert out["cov_lag1"] == -1.5
    assert out["identifiable"] is True
    assert abs(out["spread_frac"] - 2.0 * math.sqrt(1.5) / 99.6) < 1e-12
    assert abs(out["constant_bps_full_spread"]
               - 1e4 * 2.0 * math.sqrt(1.5) / 99.6) < 1e-9


def test_roll_not_identifiable_recorded_none():
    # monotone increasing series: dp = [+1,+1,+1], all products +1
    # => cov > 0 => Roll spread not identifiable; recorded None.
    bars = [_bar(date(2026, 1, d), 0, 0, 100.0 + d) for d in (5, 6, 7, 8)]
    out = C.roll_spread_cross_check(bars)
    assert out["identifiable"] is False
    assert out["constant_bps_full_spread"] is None
    assert "not identifiable" in out["reason"]


# --------------------------------------------------------------------- #
# 3. Share-base (split) boundary handling
# --------------------------------------------------------------------- #

def _split_series():
    dates = [date(2020, 1, 2), date(2020, 1, 3), date(2020, 1, 6),
             date(2020, 1, 7)]
    a = [_bar(d, c + 1.0, c - 1.0, c, adj=ad) for d, c, ad in
         zip(dates, [100.0, 100.0, 50.0, 50.0],
             [100.0, 100.0, 100.0, 100.0])]
    b = [_bar(d, 101.0, 99.0, 100.0) for d in dates]
    return a, b


def test_split_event_detected():
    a, _ = _split_series()
    events = C.split_events(a)
    assert len(events) == 1
    assert events[0]["boundary_date"] == "2020-01-06"
    assert events[0]["implied_share_base_change"] == 1.0   # 1:2 reverse


def test_cs_excludes_split_straddling_window():
    a, _ = _split_series()
    events = C.split_events(a)
    windows, excluded = C.corwin_schultz_daily_spreads(
        a, exclude_boundary_dates=C._split_boundaries(events))
    # windows (2,3), (6,7) kept; the (3,6) window straddles the 1:2
    # reverse split and is excluded.
    assert excluded == 1
    assert [str(w["window_end"]) for w in windows] == \
        ["2020-01-03", "2020-01-07"]


def test_tracking_divergence_uses_split_continuous_surface():
    # Leg A does a 1:2 reverse split; leg B never splits.  On the
    # split-continuous adjusted surface both legs are flat => zero
    # divergence; a RAW-surface reading would report a -50% artifact.
    a, b = _split_series()
    div = C.tracking_divergence(a, b, "AAAA", "BBBB")
    assert div["growth_a"] == 1.0
    assert div["growth_b"] == 1.0
    assert div["divergence_total"] == 0.0
    assert div["divergence_annualized"] == 0.0


# --------------------------------------------------------------------- #
# 4. Tracking divergence on a synthetic pair (exact literals)
# --------------------------------------------------------------------- #

def test_tracking_divergence_synthetic_pair_hand_computed():
    # 4 common sessions => 3 daily return steps per leg.
    dates = [date(2026, 1, 2), date(2026, 1, 5), date(2026, 1, 6),
             date(2026, 1, 7)]
    a = [_bar(d, 0, 0, 0, adj=round(100.0 * 1.01 ** i, 10))
         for i, d in enumerate(dates)]
    b = [_bar(d, 0, 0, 0, adj=round(100.0 * 1.005 ** i, 10))
         for i, d in enumerate(dates)]
    div = C.tracking_divergence(a, b, "AAA", "BBB")
    # hand-computed: 1.01^3 = 1.030301; 1.005^3 = 1.015075125
    assert abs(div["growth_a"] - 1.030301) < 1e-8
    assert abs(div["growth_b"] - 1.015075125) < 1e-9
    assert abs(div["divergence_total"]
               - (1.030301 - 1.015075125)) < 1e-8
    # annualization exponent 365.25/common_days (Julian year);
    # 2026-01-02 -> 2026-01-07 is 5 calendar days.
    assert div["common_days"] == 5
    assert abs(div["annualized_return_a"]
               - (1.030301 ** (365.25 / 5) - 1.0)) < 1e-6
    assert div["annualized_return_a"] > div["annualized_return_b"]


def test_tracking_divergence_refuses_disjoint_calendars():
    a = [_bar(date(2026, 1, 2), 0, 0, 100.0)]
    b = [_bar(date(2026, 2, 2), 0, 0, 100.0)]
    with pytest.raises(C.CostMeasurementRefused):
        C.tracking_divergence(a, b, "AAA", "BBB")


# --------------------------------------------------------------------- #
# 5. Dual-book kernel (degenerate + costs + root-module compatibility)
# --------------------------------------------------------------------- #

CONSTS = {"half_spread_frac": 0.0005,          # 10 bps full spread
          "expense_annual": 0.0036525,          # 365.25/yr on 100k => 1$/day
          "tracking_divergence_annual": 0.007305}  # => 2$/day


def _degenerate_trade(days=0, fills=("F1",)):
    return {"trade_id": "T1", "leg": "GLDX", "direction": 1,
            "notional_usd": 100_000.0, "entry_price": 100.0,
            "exit_price": 101.0, "days_held": days, "fills": list(fills),
            "closed": False}


def test_kernel_degenerate_one_fill_one_cost_event_one_mark():
    # ONE fill, ONE cost event (the fill), ONE mark: gross =
    # 100000*(101/100 - 1); the only cost is the single fill charge
    # 100000*0.0005*2.0 = 100.0 (days_held 0 => no accrual);
    # NET = gross - 100.0.  Dual-book equality is exact.
    expected_gross = 100_000.0 * (101.0 / 100.0 - 1.0)
    ledger = KX.dual_book_ledger([_degenerate_trade()], {"GLDX": CONSTS})
    assert ledger["fills"] == 1
    assert ledger["gross"]["total"] == pytest.approx(expected_gross,
                                                     abs=1e-6)
    assert ledger["costs"]["2.0"]["commissions_total"] == \
        pytest.approx(100.0, abs=1e-6)
    assert ledger["costs"]["2.0"]["slippage_total"] == 0.0
    assert ledger["net"]["2.0"]["total"] == \
        pytest.approx(expected_gross - 100.0, abs=1e-6)
    assert ledger["gross_closed_total"] == 0.0
    assert ledger["gross_terminal_total"] == \
        pytest.approx(expected_gross, abs=1e-6)   # open mark force-
    # closed at the last observable bar under the ROOT terminal policy
    assert ledger["terminal_policy"] == TERMINAL_POLICY
    rec = KX.reconcile_ledger(ledger)
    assert rec["dual_book_equality"] is True
    assert rec["identity_ok"] is True
    r = rec["reconciliation"]
    assert r["ending_equity"] == pytest.approx(expected_gross - 100.0,
                                               abs=1e-6)
    assert r["terminal_pnl"] == pytest.approx(expected_gross, abs=1e-6)
    assert r["commissions"] == pytest.approx(100.0, abs=1e-6)
    assert abs(r["residual"]) <= r["tolerance"]


def test_kernel_round_trip_charges_cost_once_per_fill():
    # 2 fills => EXACTLY 2 charges, never re-scaled: 2 x 100 = 200 at
    # tier 2.0; the ladder is {50, 75, 100} per fill.
    trade = _degenerate_trade(fills=("F1", "F2"))
    ledger = KX.dual_book_ledger([trade], {"GLDX": CONSTS})
    assert ledger["fills"] == 2
    assert ledger["costs"]["1.0"]["commissions_total"] == \
        pytest.approx(100.0, abs=1e-6)
    assert ledger["costs"]["1.5"]["commissions_total"] == \
        pytest.approx(150.0, abs=1e-6)
    assert ledger["costs"]["2.0"]["commissions_total"] == \
        pytest.approx(200.0, abs=1e-6)
    assert ledger["net"]["2.0"]["total"] == \
        pytest.approx(1000.0 - 200.0, abs=1e-6)


def test_kernel_drag_accrual_hand_computed():
    # expense 0.0036525/yr => 365.25 USD/yr on 100k => 1.00 USD/day;
    # tracking 0.007305/yr => 2.00 USD/day; 30 days => 90.0 USD total,
    # identical across ALL tiers (tier-independent instrument fact).
    trade = _degenerate_trade(days=30)
    costs = KX.trade_costs(trade, CONSTS)
    assert costs["drag_expense"] == pytest.approx(30.0, abs=1e-9)
    assert costs["drag_tracking"] == pytest.approx(60.0, abs=1e-9)
    assert costs["drag_total"] == pytest.approx(90.0, abs=1e-9)
    ledger = KX.dual_book_ledger([trade], {"GLDX": CONSTS})
    for tier in ("1.0", "1.5", "2.0"):
        assert ledger["costs"][tier]["slippage_total"] == \
            pytest.approx(90.0, abs=1e-9)
    assert ledger["net"]["2.0"]["total"] == \
        pytest.approx(1000.0 - 100.0 - 90.0, abs=1e-9)   # 810.0


def test_kernel_root_module_compatibility():
    # Canonical rows flow through the ROOT module's explicit adapter.
    ledger = KX.dual_book_ledger([_degenerate_trade()], {"GLDX": CONSTS})
    row = ledger["canonical_rows"][0]
    assert map_to_canonical(row) == pytest.approx(
        ledger["net"]["2.0"]["total"], abs=1e-6)
    # The inherited fail-closed contract: a row with neither PnL field
    # is an AccountingFieldError, never a silent 0.
    with pytest.raises(AccountingFieldError):
        map_to_canonical({"trade_id": "x"})
    # The root identity evaluates the ledger as-is.
    r = build_accounting_reconciliation(
        starting_equity=0.0,
        ending_equity=ledger["net"]["2.0"]["total"],
        closed_price_pnl=ledger["gross_closed_total"],
        terminal_pnl=ledger["gross_terminal_total"],
        funding_cashflows=0.0,
        commissions=ledger["costs"]["2.0"]["commissions_total"],
        slippage=ledger["costs"]["2.0"]["slippage_total"],
        rejection_costs=0.0)
    assert r["identity_ok"] is True


def test_kernel_refusal_paths_fail_closed():
    with pytest.raises(KX.KernelRefused):
        KX.fill_transaction_cost(1000.0, 0.0005, 2.5)     # unknown tier
    with pytest.raises(KX.KernelRefused):
        KX.fill_transaction_cost(0.0, 0.0005, 2.0)        # notional <= 0
    with pytest.raises(KX.KernelRefused):
        KX.fill_transaction_cost(1000.0, None, 2.0)       # no constant
    with pytest.raises(KX.KernelRefused):
        KX.drag_accrual(1000.0, -0.01, 5)                 # negative rate
    with pytest.raises(KX.KernelRefused):
        KX.dual_book_ledger([_degenerate_trade()], {})    # leg unknown
    with pytest.raises(KX.KernelRefused):
        KX.dual_book_ledger(
            [{**_degenerate_trade(), "fills": []}], {"GLDX": CONSTS})
    with pytest.raises(KX.KernelRefused):
        KX.price_pnl(0, 1000.0, 100.0, 101.0)             # direction


# --------------------------------------------------------------------- #
# 6. Weekly decision-grid clock: DST boundaries + real-calendar anchor
# --------------------------------------------------------------------- #

def test_release_instants_dst_boundaries_hand_computed():
    # EST winter: UTC-5 => 15:30 ET = 20:30Z; EDT summer: UTC-4 =>
    # 19:30Z.  2026 DST: spring-forward 2026-03-08, fall-back
    # 2026-11-01 (US rules).  The P0 rule object is the single source.
    for tue, friday, want in (
            (date(2026, 1, 13), date(2026, 1, 16),
             "2026-01-16T20:30:00+00:00"),
            (date(2026, 3, 10), date(2026, 3, 13),
             "2026-03-13T19:30:00+00:00"),   # EDT starts 2026-03-08
            (date(2026, 6, 9), date(2026, 6, 12),
             "2026-06-12T19:30:00+00:00"),
            (date(2026, 11, 3), date(2026, 11, 6),
             "2026-11-06T20:30:00+00:00")):  # EST starts 2026-11-01
        assert K.release_instant(tue).isoformat() == want
        assert K.release_instant(tue) == p0_release_instant(tue)
        assert friday.weekday() == 4


def test_release_instant_refuses_non_tuesday():
    with pytest.raises(CotLookupRefused):
        K.release_instant(date(2026, 6, 10))   # Wednesday canary class


def test_decision_grid_real_calendar_anchor():
    # Committed GLD session calendar around the 2026-06-09 report:
    # release Friday 2026-06-12 19:30Z (EDT); the next ETP session is
    # Monday 2026-06-15; the release day's own bar (16:00 ET close =
    # 20:00Z) is NOT readable at the release instant (V7 close+1).
    with open(os.path.join(RUN_DIR, "etp_eod", "GLD.csv"),
              encoding="utf-8") as fh:
        sessions = [date.fromisoformat(r["date"]) for r in
                    csv.DictReader(fh)]
    rows = K.weekly_decision_grid([date(2026, 6, 9)], sessions)
    g = rows[0]
    assert g["release_instant_utc"] == "2026-06-12T19:30:00+00:00"
    assert g["release_date"] == "2026-06-12"
    assert g["decision_session"] == "2026-06-15"
    assert g["release_date_bar_readable"] is False
    assert "2026-06-11" in g["bars_readable_at_decision"]
    assert "2026-06-12" not in g["bars_readable_at_decision"]
    assert g["cot_visible_at_release"][-1] == "2026-06-09"


def test_grid_refuses_exhausted_calendar():
    with pytest.raises(K.ClockRefused):
        K.weekly_decision_grid([date(2026, 6, 9)], [date(2026, 6, 10)])


# --------------------------------------------------------------------- #
# 7. Kernel-side PIT guard (wired to the P0 plane guard semantics)
# --------------------------------------------------------------------- #

def test_pit_withheld_before_release_visible_at_release():
    rel = K.release_instant(date(2026, 6, 9))
    before = rel - timedelta(seconds=1)
    assert pit_guard(date(2026, 6, 9), before)["pit_allowed"] is False
    assert pit_guard(date(2026, 6, 9), rel)["pit_allowed"] is True
    assert pit_guard(date(2026, 6, 9),
                     rel + timedelta(seconds=1))["pit_allowed"] is True


def test_kernel_pit_require_visible_refuses_withheld_report():
    rel = K.release_instant(date(2026, 6, 9))
    with pytest.raises(K.KernelPitRefused):
        K.kernel_pit_require_visible(date(2026, 6, 9),
                                     rel - timedelta(seconds=1))
    env = K.kernel_pit_require_visible(date(2026, 6, 9), rel)
    assert env["pit_allowed"] is True


def test_kernel_pit_view_matches_plane_guard_per_report():
    reports = [date(2026, 6, 2), date(2026, 6, 9)]
    use = K.release_instant(date(2026, 6, 9))
    visible = K.kernel_pit_visible_report_dates(reports, use)
    assert visible == [d for d in reports
                       if pit_guard(d, use)["pit_allowed"]]
    assert visible == reports          # both released by 2026-06-12
    use_early = K.release_instant(date(2026, 6, 2))   # prior Tue's week
    visible_early = K.kernel_pit_visible_report_dates(reports, use_early)
    assert visible_early == [date(2026, 6, 2)]   # 06-09 still withheld


# --------------------------------------------------------------------- #
# 8. Committed P1 artifacts vs the committed P0 substrate
# --------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def contract():
    return _load("p1_cost_contract.json")


@pytest.fixture(scope="module")
def gate():
    return _load("p1_gate.json")


@pytest.fixture(scope="module")
def fee_facts():
    return _load("fee_facts.json")["fees"]


def test_cost_contract_shape_and_coverage(contract):
    census = _load("p0_etp_census.json")["censuses"]
    eligible = sorted(s for s, c in census.items() if c["etp_leg_eligible"])
    assert contract["schema"] == "commodities_ng1_run/p1_cost_contract@1"
    assert sorted(contract["per_leg"]) == eligible
    assert contract["primary_tier"] == 2.0
    assert contract["tier_ladder"] == [1.0, 1.5, 2.0]


def test_cost_contract_per_leg_constants_complete(contract):
    for sym, leg in contract["per_leg"].items():
        sp = leg["spread"]
        assert sp["constant_frac_full_spread_p90"] > 0
        assert sp["windows"] >= 500
        assert sp["percentile"] == 0.90
        assert "windows_excluded_share_base_boundary" in sp
        assert "share_base_events" in sp
        rc = leg["roll_cross_check"]
        assert rc["method"] == "roll_1984_lag1_autocov"
        assert rc["n_delta"] > 0
        if not rc["identifiable"]:
            assert rc["constant_bps_full_spread"] is None
            assert "not identifiable" in rc["reason"]
        # per-fill half-spread == half of the measured FULL spread
        assert abs(leg["half_spread_frac_p90_per_fill"]
                   - sp["constant_frac_full_spread_p90"] / 2.0) < 1e-15


def test_cost_contract_gold_group_is_measured_census(contract):
    # Dispatch hint said "GLD/IAU/SGOL/SIVR"; the measured census
    # governs: SIVR is a SILVER leg (cot code 084691); the fourth gold
    # leg is BAR.  The group derivation is from p0_market_pairs.json.
    groups = contract["same_underlying_groups"]
    assert groups["088691"] == ["BAR", "GLD", "IAU", "SGOL"]
    assert groups["084691"] == ["SIVR", "SLV"]
    assert groups["067651"] == ["DBO", "USL", "USO"]
    assert len(contract["tracking_pairs"]) == 10


def test_cost_contract_tracking_proxy_assignment(contract):
    with_proxy = sorted(s for s, leg in contract["per_leg"].items()
                        if leg["tracking_proxy"]["status"]
                        == "MEASURED_SAME_UNDERLYING_PAIRS")
    assert with_proxy == sorted(contract["same_underlying_groups"]
                                ["067651"]
                                + contract["same_underlying_groups"]
                                ["084691"]
                                + contract["same_underlying_groups"]
                                ["088691"])
    for sym, leg in contract["per_leg"].items():
        tp = leg["tracking_proxy"]
        if tp["status"] != "MEASURED_SAME_UNDERLYING_PAIRS":
            assert tp["abs_divergence_annualized_mean"] is None
            assert "fail-closed" in tp["limitation"]


def test_cost_contract_gld_iau_divergence_matches_fee_gap():
    # Economic sanity anchor: GLD (0.40%) vs IAU (0.25%) differ by
    # 15 bps/yr of stated fees; the measured adjusted-surface
    # divergence must be of that order, NOT a split artifact.
    contract = _load("p1_cost_contract.json")
    pair = next(p for p in contract["tracking_pairs"]
                if p["pair"] == "GLD/IAU")
    assert abs(pair["divergence_annualized"]) < 0.01   # < 100 bp/yr


def test_cost_contract_constants_reproduce_from_committed_csv(contract):
    # Re-measure GLD from the committed RAW CSV: the contract value
    # must reproduce EXACTLY (determinism of the committed substrate).
    with open(os.path.join(RUN_DIR, "etp_eod", "GLD.csv"),
              encoding="utf-8") as fh:
        bars = [{"date": date.fromisoformat(r["date"]),
                 "high": float(r["high"]), "low": float(r["low"]),
                 "close": float(r["close"]),
                 "adj_close": float(r["adj_close"])}
                for r in csv.DictReader(fh)]
    cs = C.cs_stress_constant(bars)
    assert cs["constant_bps_full_spread_p90"] == \
        contract["per_leg"]["GLD"]["spread"][
            "constant_bps_full_spread_p90"]


def test_fee_facts_provenance_and_values(fee_facts):
    measured = {s: f for s, f in fee_facts.items()
                if f["status"] == "MEASURED_OFFICIAL_PAGE"}
    assert sorted(measured) == ["CANE", "CORN", "DBA", "DBC", "DBO",
                                "GLD", "IAU", "PDBC", "SLV", "SOYB",
                                "WEAT"]
    # hand-pinned official values (page sha256 in the evidence file)
    expected = {"GLD": 0.0040, "IAU": 0.0025, "SLV": 0.0050,
                "DBO": 0.0081, "DBC": 0.0089, "PDBC": 0.0074,
                "DBA": 0.0090, "CORN": 0.0100, "SOYB": 0.0083,
                "WEAT": 0.0117, "CANE": 0.0093}
    for sym, rate in expected.items():
        assert measured[sym]["expense_ratio_annual"] == rate
        assert measured[sym]["source_url"].startswith("https://")
        assert len(measured[sym]["page_sha256"]) == 64
    for sym, f in fee_facts.items():
        if f["status"] == "NOT_MEASURED":
            assert f["expense_ratio_annual"] is None
            assert f.get("reason"), sym
            assert f.get("attempted"), sym


def test_fee_fact_page_digests_verify_when_present(fee_facts):
    for sym, f in fee_facts.items():
        for att in ([{"page_file": f.get("page_file"),
                      "page_sha256": f.get("page_sha256")}]
                    if f["status"] == "MEASURED_OFFICIAL_PAGE"
                    else f.get("attempted", [])):
            pf, want = att.get("page_file"), att.get("page_sha256")
            if not pf or not want:
                continue
            path = os.path.join(RUN_DIR, pf)
            if not os.path.isfile(path):
                continue          # raw bytes gitignored: skip leg
            h = __import__("hashlib").sha256()
            with open(path, "rb") as fh:
                for chunk in iter(lambda: fh.read(1 << 20), b""):
                    h.update(chunk)
            assert h.hexdigest() == want, sym


def test_p1_gate_verdict_consistency(gate):
    assert gate["schema"] == "commodities_ng1_run/p1_gate@1"
    assert gate["cycle_id"] == "COMMODITIES-NG1"
    assert gate["task_id"] == "commodities-ng1-p1-kernel-costs"
    assert gate["final_verdict"] == "PASS"
    assert all(i["verdict"] == "PASS" for i in gate["items"].values())
    assert gate["test_command"].endswith(
        "python -m pytest tests/test_commodities_ng1_p1.py -q")
    vals = gate["items"]["item2_cost_constants"]["values"]
    assert vals["eligible_legs"] == 22
    assert vals["tracking_pairs_measured"] == 10
    assert len(vals["expense_facts_measured"]) == 11
    assert len(vals["expense_facts_fail_closed_disclosed"]) == 11
