"""RATES-NG1 P1 tests (dispatch: rates-ng1-p1-kernel-costs).

Hand-computed assertions only; no network price pulls (the frozen
substrate is consumed via the plane adapter, verify-on-read):

1. kernel inheritance (work item 1): the degenerate dual-book case --
   ONE fill, ONE cost event, ONE mark -- reconciles to exact
   hand-computed numbers in BOTH books with dual-book ledger equality;
   cost-once-per-fill replay is refused; ``research.accounting``
   compatibility (map_to_canonical, AccountingFieldError, inherited
   terminal policy) is proven on real ledger rows.
2. cost estimator (work item 2): Corwin-Schultz on a synthetic
   constant-bracket OHLC with KNOWN spread recovers it EXACTLY
   (2h = 10 bps); flat-bar degenerate and negative-alpha floor cases
   hand-computed; Roll on an alternating close series is EXACTLY 2.0;
   percentile interpolation and ACT/365F drag conversion hand-computed.
3. clock (work item 3): hand-computed UTC instants on the four 2026
   DST boundary sessions; V7 bar-readable close+1 session rule; the
   auction day-event PIT anchoring refuses the same-day close.
4. cost contract (work item 2/4): the frozen contract's constants are
   reproduced from the plane-read RAW bars (p90 recomputation) and its
   fee facts match the issuer-official evidence with exact daily
   conversion.
"""

from __future__ import annotations

import json
import os
from datetime import date, datetime, timezone

import pytest

from research.accounting import (
    TERMINAL_POLICY,
    AccountingFieldError,
    map_to_canonical,
)
from research.assets.rates_ng1 import clock as ck
from research.assets.rates_ng1 import cost_model as cm
from research.assets.rates_ng1 import plane_adapter as pa
from research.assets.rates_ng1.kernel import (
    BOOKS,
    COST_LADDER_TIER,
    COST_FREQUENCY,
    CostOnceViolation,
    DualBookLedger,
    KernelError,
    UnknownBook,
)

WORKTREE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RUN_DIR = os.path.join(WORKTREE, "research", "control", "rates_ng1_run")
CONTRACT_PATH = os.path.join(RUN_DIR, "p1_cost_contract.json")


# --------------------------------------------------------------------- #
# 1. kernel: degenerate dual-book case, hand-computed                    #
# --------------------------------------------------------------------- #

def _degenerate_ledger() -> DualBookLedger:
    led = DualBookLedger("degenerate", starting_equity=10_000.00)
    # ONE fill: BUY 100 @ 100.00; spread 10 bps -> half-spread
    # 0.0005 * 100 * 100 = 5.00 charged ONCE (cost book only).
    led.apply_fill(fill_id="F1", ts="2026-03-06T21:00:00+00:00",
                   ticker="TLT", side="BUY", qty=100.0, price=100.00,
                   spread_cost=5.00)
    # ONE typed cost event: 1 day of expense drag on 10,000 notional
    # at the official 0.15%/yr -> 10000 * (0.0015/365) = 15/365.
    led.apply_expense_drag(ts="2026-03-09T21:00:00+00:00", days=1.0,
                           notional=10_000.00,
                           per_day_fraction=0.0015 / 365.0)
    # ONE mark: 101.00 -> price PnL = (101 - 100) * 100 = +100.00.
    led.apply_mark(ts="2026-03-09T21:00:00+00:00", ticker="TLT",
                   price=101.00)
    return led


def test_kernel_degenerate_dual_book_hand_computed():
    led = _degenerate_ledger()
    drag = 10_000.0 * (0.0015 / 365.0)          # = 15/365
    assert led.price_pnl() == 100.0             # exact hand value
    assert led.equity("price_only") == 10_100.0  # exact hand value
    # cost book: 10,000 + 100 - 5.00 - 15/365
    assert led.equity("cost_adjusted") == pytest.approx(
        10_000.0 + 100.0 - 5.0 - drag, rel=1e-12, abs=1e-12)
    # dual-book ledger equality (shared rows; cost delta = price delta
    # - total costs, exact within the scaled tolerance)
    eq = led.dual_book_equality()
    assert eq["equality_ok"] is True
    assert eq["price_only_delta"] == 100.0
    assert eq["cost_adjusted_delta"] == pytest.approx(
        100.0 - 5.0 - drag, rel=1e-12, abs=1e-12)
    assert eq["total_costs"] == pytest.approx(5.0 + drag, rel=1e-12,
                                              abs=1e-12)
    assert eq["sign_record"]["price_only"] == "positive"
    assert eq["sign_record"]["cost_adjusted"] == "positive"
    assert eq["sign_record"]["sign_inverted"] is False
    # both books reconcile via the SHARED identity
    for book in BOOKS:
        rec = led.reconcile(book)
        assert rec["identity_ok"] is True
        assert rec["terminal_policy"] == TERMINAL_POLICY
    pr = led.reconcile("price_only")
    cr = led.reconcile("cost_adjusted")
    assert pr["slippage"] == 0.0 and pr["commissions"] == 0.0
    assert cr["slippage"] == pytest.approx(5.0, rel=1e-12, abs=1e-12)
    assert cr["commissions"] == pytest.approx(drag, rel=1e-12, abs=1e-12)
    # cost events appear in the cost book ONLY
    assert led.book_view("price_only")["cost_events"] == []
    assert len(led.book_view("cost_adjusted")["cost_events"]) == 1
    # fills and marks are SHARED rows: identical across the books
    pv, cv = led.book_view("price_only"), led.book_view("cost_adjusted")
    assert pv["fills"] == cv["fills"] and pv["marks"] == cv["marks"]


def test_kernel_cost_once_replay_refused():
    led = _degenerate_ledger()
    with pytest.raises(CostOnceViolation):
        led.apply_fill(fill_id="F1", ts="2026-03-06T21:00:00+00:00",
                       ticker="TLT", side="SELL", qty=100.0, price=101.0,
                       spread_cost=5.0)
    # replaying did not mutate the ledger
    assert len(led.fills) == 1 and len(led.marks) == 1


def test_kernel_map_to_canonical_compatibility_inherited():
    led = _degenerate_ledger()
    drag = 10_000.0 * (0.0015 / 365.0)
    fill_row = led.fills[0]
    cost_row = led.cost_events[0]
    assert map_to_canonical(fill_row) == 0.0
    assert map_to_canonical(cost_row) == pytest.approx(-drag, rel=1e-12,
                                                       abs=1e-12)
    # inherited fail-closed behavior: no silent zero
    with pytest.raises(AccountingFieldError):
        map_to_canonical({"not_a_pnl": 1.0})


def test_kernel_serialize_law_constants_and_stability():
    led = _degenerate_ledger()
    ser = led.serialize()
    assert ser["schema"] == "rates_ng1/kernel@1"
    assert ser["cost_ladder_tier"] == 2.0
    assert ser["cost_frequency"] == "once_per_fill"
    assert ser["terminal_policy"] == TERMINAL_POLICY == \
        "FORCE_LIQUIDATE_AT_LAST_OBSERVABLE_BAR"
    # deterministic serialization -> stable digest
    assert led.sha256() == led.sha256()
    import hashlib
    payload = json.dumps(ser, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    assert led.sha256() == hashlib.sha256(payload).hexdigest()


def test_kernel_input_validation_fail_closed():
    led = DualBookLedger("v", 1000.0)
    with pytest.raises(KernelError):
        led.apply_fill(fill_id="X", ts="t", ticker="TLT", side="LONG",
                       qty=1.0, price=1.0)
    with pytest.raises(KernelError):
        led.apply_mark(ts="t", ticker="TLT", price=0.0)
    with pytest.raises(UnknownBook):
        led.book_view("financing_only")
    with pytest.raises(KernelError):
        led.apply_fill(fill_id="Y", ts="t", ticker="TLT", side="SELL",
                       qty=10.0, price=100.0)  # short below zero refused


# --------------------------------------------------------------------- #
# 2. cost estimators on synthetic bars with KNOWN answers                #
# --------------------------------------------------------------------- #

def test_cs_constant_bracket_recovers_known_spread_exactly():
    # H = mid*(1+h), L = mid*(1-h) with h = 0.0005 every day:
    # ln(H/L) = k constant -> beta = 2k^2, gamma = k^2
    # -> alpha = k*(2+sqrt2) - k*(sqrt2+1) = k
    # -> spread = 2(e^k - 1)/(e^k + 1) = 2h = 0.001 EXACTLY (10 bps).
    h = 0.0005
    n = 30
    highs = [100.0 * (1.0 + h)] * n
    lows = [100.0 * (1.0 - h)] * n
    out = cm.corwin_schultz_spread_series(highs, lows)
    assert out["pairs"] == n - 1 == 29
    assert out["estimable_pairs"] == 29
    assert out["floored"] == 0
    for key in ("mean", "p50", "p90"):
        assert out[key] == pytest.approx(0.001, abs=1e-12)
    # every daily estimate equals 2h
    assert all(s == pytest.approx(0.001, abs=1e-12)
               for s in out["spreads"])


def test_cs_flat_bars_zero_spread_and_negative_alpha_floor():
    # flat bars: H == L every day -> beta = gamma = 0 -> alpha = 0
    # -> spread exactly 0 for every pair.
    out = cm.corwin_schultz_spread_series([100.0] * 5, [100.0] * 5)
    assert out["spreads"] == [0.0, 0.0, 0.0, 0.0]
    assert out["floored"] == 0 and out["mean"] == 0.0
    # flat bars with ONE up-gap day: pair(100,101) has beta = 0 but
    # gamma = ln(101/100)^2 > 0 -> alpha < 0 -> floored to 0 (counted);
    # pair(101,101) is exactly 0.  Hand-computed: spreads [0, 0],
    # floored = 1.
    out2 = cm.corwin_schultz_spread_series([100.0, 101.0, 101.0],
                                           [100.0, 101.0, 101.0])
    assert out2["spreads"] == [0.0, 0.0]
    assert out2["floored"] == 1
    assert out2["estimable_pairs"] == 2


def test_cs_rejects_malformed_bars_fail_closed():
    # day 2 has high < low: pair(1,2) is not estimable; pair(0,1) is.
    out = cm.corwin_schultz_spread_series([10.0, 10.0, 6.0],
                                          [5.0, 9.0, 10.0])
    assert out["spreads"][0] is not None
    assert out["spreads"][1] is None          # high < low refused
    assert out["estimable_pairs"] == 1
    # a zero low is refused too: zero estimable pairs
    out2 = cm.corwin_schultz_spread_series([10.0, 10.0], [0.0, 5.0])
    assert out2["spreads"] == [None]
    assert out2["estimable_pairs"] == 0
    with pytest.raises(ValueError):
        cm.corwin_schultz_spread_series([1.0], [1.0, 2.0])


def test_roll_alternating_series_exact_spread_two():
    # closes alternate 100/101: d = [+1,-1,...] (63 values);
    # mean(d) = 1/63, mean(d[:-1]) = 0, mean(d_t*d_{t-1}) = -1
    # -> cov = -1 -> spread_price = 2*sqrt(1) = 2.0 EXACTLY (price
    # units); the fraction basis divides by the window mean close
    # (100*32 + 101*32)/64 = 100.5 -> 2/100.5; in bps:
    # 2/100.5 * 10^4 = 199.0049751243781... bps (hand-computed).
    closes = [100.0, 101.0] * 32
    out = cm.roll_effective_spread_windows(closes, window=63)
    assert out["windows"] == 1
    assert out["estimable_windows"] == 1
    assert out["undefined_cov"] == 0
    assert out["median_price_units"] == pytest.approx(2.0, abs=1e-9)
    assert out["median"] == pytest.approx(2.0 / 100.5, abs=1e-12)
    assert cm.bps(out["median"]) == pytest.approx(199.0049751243781,
                                                  rel=1e-9)


def test_roll_positive_autocovariance_undefined_not_imputed():
    # strictly rising closes: d_t = +1 constant -> cov = 0 (not < 0)
    # -> Roll undefined for the window; median None; nothing imputed.
    closes = [float(i) for i in range(1, 65)]
    out = cm.roll_effective_spread_windows(closes, window=63)
    assert out["windows"] == 1
    assert out["estimable_windows"] == 0
    assert out["undefined_cov"] == 1
    assert out["median"] is None
    assert out["median_price_units"] is None
    assert out["estimable_fraction"] == 0.0


def test_percentile_interpolation_hand_computed():
    assert cm.percentile([1.0, 2.0, 3.0, 4.0], 0.9) == \
        pytest.approx(3.7, abs=1e-9)
    assert cm.percentile([1.0, 3.0], 0.5) == 2.0
    assert cm.percentile([5.0], 0.0) == 5.0 and \
        cm.percentile([5.0], 1.0) == 5.0
    assert cm.percentile([3.0, 1.0, 2.0], 0.5) == 2.0  # unsorted input
    with pytest.raises(ValueError):
        cm.percentile([], 0.5)
    with pytest.raises(ValueError):
        cm.percentile([1.0], 1.5)


def test_expense_drag_act365_exact_and_sanity_band():
    assert cm.expense_drag_per_day(0.0015) == 0.0015 / 365.0
    assert cm.expense_drag_per_day(0.0) == 0.0
    with pytest.raises(ValueError):
        cm.expense_drag_per_day(0.06)     # above the 5% sanity band
    with pytest.raises(ValueError):
        cm.expense_drag_per_day(-0.001)   # negative fee refused


# --------------------------------------------------------------------- #
# 3. clock: DST boundaries, V7 close+1, auction PIT anchoring            #
# --------------------------------------------------------------------- #

def test_ny_close_utc_dst_boundaries_hand_computed():
    utc = timezone.utc
    # Spring forward 2026 (DST begins Sun 2026-03-08):
    assert ck.ny_close_utc(date(2026, 3, 6)) == \
        datetime(2026, 3, 6, 21, 0, tzinfo=utc)   # EST, UTC-5
    assert ck.ny_close_utc(date(2026, 3, 9)) == \
        datetime(2026, 3, 9, 20, 0, tzinfo=utc)   # EDT, UTC-4
    # Fall back 2026 (DST ends Sun 2026-11-01):
    assert ck.ny_close_utc(date(2026, 10, 30)) == \
        datetime(2026, 10, 30, 20, 0, tzinfo=utc)  # EDT, UTC-4
    assert ck.ny_close_utc(date(2026, 11, 2)) == \
        datetime(2026, 11, 2, 21, 0, tzinfo=utc)   # EST, UTC-5
    # string dates accepted
    assert ck.ny_close_utc("2026-03-06") == \
        ck.ny_close_utc(date(2026, 3, 6))


def test_decision_grid_v7_bar_readable_close_plus_one():
    sessions = ck.sessions_from_bars(
        ["2026-03-06", "2026-03-09", "2026-03-10"])
    # the Fri 2026-03-06 bar is first readable at the NEXT session's
    # NY close (Mon 2026-03-09, EDT -> 20:00Z), never at its own close
    rec = ck.decision_instant_for_bar("2026-03-06", sessions)
    assert rec["bar_date"] == "2026-03-06"
    assert rec["decision_session"] == "2026-03-09"
    assert rec["decision_utc"] == "2026-03-09T20:00:00+00:00"
    assert rec["decision_session"] != rec["bar_date"]
    # end-of-data bar has no successor: never readable (fail-closed)
    assert ck.decision_instant_for_bar("2026-03-10", sessions) is None
    # grid covers every session with a successor
    grid = ck.decision_grid(sessions)
    assert [g["decision_session"] for g in grid] == \
        ["2026-03-09", "2026-03-10"]
    # DST flip visible inside one grid week: 21:00Z (EST) vs 20:00Z (EDT)
    assert grid[0]["decision_utc"].endswith("20:00:00+00:00")
    assert ck.decision_instant_for_bar(
        "2026-03-05", ck.sessions_from_bars(["2026-03-05", "2026-03-06"])
    )["decision_utc"] == "2026-03-06T21:00:00+00:00"


def test_pit_day_event_anchor_next_session_same_day_refused():
    sessions = ck.sessions_from_bars(
        ["2026-03-06", "2026-03-09", "2026-03-10"])
    # Official auction announcement dated Fri 2026-03-06 (day-granular
    # census fact): conservative LATER PIT bound = end of that NY day
    # (23:59:59.999999 EST = 2026-03-07T04:59:59.999999Z; Mar 6 is
    # BEFORE the Sun 2026-03-08 DST switch, so UTC-5); the Fri 21:00Z
    # close is BEFORE the PIT instant -> refused; the first eligible
    # decision is Mon 2026-03-09's 20:00Z close.
    rec = ck.first_decision_after_pit("2026-03-06", sessions)
    assert rec["pit_instant_utc"] == \
        "2026-03-07T04:59:59.999999+00:00"
    assert rec["decision_session"] == "2026-03-09"
    assert rec["decision_utc"] == "2026-03-09T20:00:00+00:00"
    assert rec["same_day_close_eligible"] is False
    # a Saturday-dated announcement lands on the same Mon close
    rec_sat = ck.first_decision_after_pit("2026-03-07", sessions)
    assert rec_sat["decision_session"] == "2026-03-09"
    # exhausts past the last session -> None (fail-closed)
    assert ck.first_decision_after_pit("2026-03-10", sessions) is None


# --------------------------------------------------------------------- #
# 4. frozen cost contract: reproduction from the plane-read RAW bars     #
# --------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def contract() -> dict:
    if not os.path.isfile(CONTRACT_PATH):
        pytest.skip("p1_cost_contract.json not yet written by p1_run.py")
    with open(CONTRACT_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def test_contract_law_constants(contract):
    assert contract["schema"] == "rates_ng1_run/p1_cost_contract@1"
    assert contract["cost_ladder_tier"] == 2.0
    assert contract["cost_frequency"] == "once_per_fill"
    assert contract["stress_tier"]["quantile"] == 0.90
    assert sorted(contract["per_etp"]) == sorted(pa.ETP_TICKERS)


@pytest.mark.parametrize("ticker", sorted(pa.ETP_TICKERS))
def test_contract_stress_tier_reproduces_from_plane_raw_bars(contract,
                                                             ticker):
    rows = pa.RatesNG1Plane().etp_rows(ticker)
    highs = [float(r["high"]) for r in rows]
    lows = [float(r["low"]) for r in rows]
    dates = [str(r["date"]) for r in rows]
    cs = cm.corwin_schultz_spread_series(highs, lows)
    entry = contract["per_etp"][ticker]
    assert entry["stress_tier_bps"] == \
        pytest.approx(cm.bps(cs["p90"]), rel=1e-12)
    assert entry["spread_primary"]["cs_p50_bps"] == \
        pytest.approx(cm.bps(cs["p50"]), rel=1e-12)
    assert entry["spread_primary"]["estimable_pairs"] == \
        cs["estimable_pairs"]
    assert entry["spread_primary"]["alpha_floored_days"] == cs["floored"]
    assert entry["spread_primary"]["window"] == [dates[0], dates[-1]]


@pytest.mark.parametrize("ticker", sorted(pa.ETP_TICKERS))
def test_contract_fee_facts_official_and_exact(contract, ticker):
    entry = contract["per_etp"][ticker]
    er = entry["expense_drag"]
    assert er["er_annual"] == 0.0015
    assert er["drag_per_day_fraction"] == er["er_annual"] / 365.0
    assert er["er_evidence_url"].startswith("https://www.ishares.com/us/"
                                            "products/")
    assert ticker in er["er_page_title"]
    assert len(er["er_page_sha256"]) == 64
    assert er["er_source"] == "issuer_official_fund_page"
    # stress tier is the CS p90 (never a vendor-stated number)
    assert entry["stress_tier_bps"] == \
        entry["spread_primary"]["cs_p90_bps"]


def test_contract_substrate_provenance_pins(contract):
    with open(os.path.join(RUN_DIR, "substrate_manifest.json")) as fh:
        manifest = json.load(fh)
    with open(os.path.join(RUN_DIR, "p0_etp_census.json")) as fh:
        census = json.load(fh)
    for ticker in sorted(pa.ETP_TICKERS):
        entry = f"etp_eod/{ticker}.US.json"
        leg = contract["substrate_provenance"]["legs"][ticker]
        assert leg["sha256_plane_measured"] == \
            manifest["files"][entry]["sha256"]
        assert leg["sha256_plane_measured"] == census["tickers"][ticker][
            "sha256"]
        assert contract["substrate_provenance"][
            "p0_etp_census_cross_check"][ticker][
            "sha256_matches_p0_census"] is True
