"""STOCKS-SEARCH-V1 P0 targeted tests (plans/PLAN_stocks_search_v1.md §4, §3b).

Fixture-based and network-free: they verify the committed census machinery —
gate logic (fail-closed F1), per-configuration census counters, the zero-range
law, fold boundaries, the warmup law, bookability floors, cost bands and the
frozen clock — against hand-computed fixtures.  NO network, NO API key, NO
data plane.  A green run here never implies the data-dependent gates F2–F8
measured PASS; on the blocked path they are NOT_RUN (BLOCKED_SOURCE_OR_SCHEMA).
"""

from __future__ import annotations

import datetime
import importlib.util
import json
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pytest

WT = Path(__file__).resolve().parent.parent
P0 = WT / "research/control/stocks_search_v1_run/p0"

_spec = importlib.util.spec_from_file_location("p0_lib", P0 / "p0_lib.py")
L = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(L)


# ------------------------------------------------------------------ fixtures

def flat_series(n: int, close: float = 100.0, vol: float = 1e6):
    """A flat served-session series: open=close-0.5, high=close+1,
    low=close-1 (never degenerate), constant volume."""
    close_a = np.full(n, float(close))
    open_a = close_a - 0.5
    high_a = close_a + 1.0
    low_a = close_a - 1.0
    vol_a = np.full(n, float(vol))
    return open_a, high_a, low_a, close_a, vol_a


def cfg(config_id: str) -> dict:
    match = [c for c in L.enumerate_configs() if c["config_id"] == config_id]
    assert match, config_id
    return match[0]


# ------------------------------------------------------- 1. grid law (§5)

def test_grid_law_47_configurations():
    info = L.assert_grid_law()
    assert info["n_configs"] == 47
    assert info["family_counts"] == L.FAMILY_COUNTS
    assert info["n_configs"] <= info["cap"] == L.GRID_CAP
    configs = L.enumerate_configs()
    ids = [c["config_id"] for c in configs]
    assert ids == sorted(ids) and len(ids) == len(set(ids))
    assert all(c["config_id"].startswith("SSS-") for c in configs)
    # both-direction enumerations exist for GAP, DVOL-SHOCK, VOL-REGIME
    for fam, dirs in (("GAP", {"FADE", "CONFIRM"}),
                      ("DVOL-SHOCK", {"FADE", "CONFIRM"}),
                      ("VOL-REGIME", {"LOW", "HIGH"})):
        have = set()
        for c in configs:
            if c["family"] != fam:
                continue
            key = c["params"].get("direction")
            assert key is not None, c["config_id"]
            have.add(key.upper())
        assert have == dirs, (fam, have)


def test_warmup_never_below_252():
    """Warmup law: first eligible decision >= the 253rd served session."""
    assert L.WARMUP_SESSIONS == 252
    for c in L.enumerate_configs():
        assert c["warmup_need"] >= L.WARMUP_SESSIONS, c["config_id"]
    # a 252-session name fires NOTHING (only the 253rd session is eligible)
    o, h, lo, cl, v = flat_series(252)
    for c in L.enumerate_configs():
        fired, _book, drops = L.run_config_census(c, o, h, lo, cl, v)
        assert int(fired.sum()) == 0, c["config_id"]
        assert drops["warmup"] == 252, c["config_id"]


# --------------------------------------------------- 2. zero-range law (§5)

def test_zero_range_law_event_unwind_never_imputed():
    """A high==low bar on the RANGE component is NEVER imputed: the state is
    not fired and the degenerate bar is counted."""
    o, h, lo, cl, v = flat_series(260)
    # engineer BREAK (low pierces prior low 99) + RECLAIM (close > 99) at 258
    lo[258] = 98.5
    cl[258] = 99.5
    h[258] = 100.5
    v[258] = 2e6                      # participation spike: 2.0x >= 1.5x
    c = cfg("SSS-EVENT-UNWIND-K21-H5")
    fired, _book, drops = L.run_config_census(c, o, h, lo, cl, v, first_i=252)
    assert int(fired.sum()) == 1 and fired[258]
    assert drops["range_undefined"] == 0
    # now make the SAME bar degenerate (high == low): NOT FIRED, counted
    h[258] = 98.5
    fired2, _book2, drops2 = L.run_config_census(c, o, h, lo, cl, v, first_i=252)
    assert int(fired2.sum()) == 0
    assert drops2["range_undefined"] == 1     # degenerate bar censused
    assert drops2["break"] == 7               # the other 8 decisions fail BREAK
    assert drops2["break_no_reclaim"] == 0


def test_zero_range_law_clv_window_contaminated():
    """A degenerate bar ANYWHERE in the CLV/slope window makes P undefined ->
    NOT FIRED (fail-closed, never imputed); degenerate windows counted."""
    k = 5
    need = L.CLV_WINDOW + k
    n = 282
    c = cfg("SSS-CLV-RANGE-K5-H5")
    # rising close-location fraction -> CLV = 2*frac-1 rises -> positive slope
    cl = 100.0 + 0.01 * np.arange(n)
    frac = 0.25 + 0.5 * np.arange(n) / n
    d = 0.2
    lo = cl - frac * d
    h = cl + (1.0 - frac) * d
    o = cl - 0.5 * d * frac
    v = np.full(n, 1e6)
    fired1, _b1, d1 = L.run_config_census(c, o, h, lo, cl, v, first_i=252)
    assert int(fired1.sum()) == n - 252
    # inject ONE degenerate bar inside the slope window of the LAST session
    j = n - 1 - (need // 2)
    h[j] = lo[j]                       # high == low
    fired2, _b2, d2 = L.run_config_census(c, o, h, lo, cl, v, first_i=252)
    assert not fired2[n - 1]           # slope window contaminated -> NOT FIRED
    assert d2["range_undefined"] >= 1  # censused, never imputed
    assert int(fired2.sum()) < int(fired1.sum())


# ------------------------------------------- 3. census counters (hand-computed)

def test_event_unwind_hand_counted():
    n = 260
    o, h, lo, cl, v = flat_series(n)
    lo[258] = 98.5                     # BREAK: 98.5 < prior low 99
    cl[258] = 99.5                     # RECLAIM: 99.5 > 99
    h[258] = 100.5                     # RANGE: (99.5-98.5)/(100.5-98.5) = 0.5
    v[258] = 2e6                       # PARTICIPATION: 2.0x >= 1.5x
    c = cfg("SSS-EVENT-UNWIND-K21-H5")
    fired, book, drops = L.run_config_census(c, o, h, lo, cl, v, first_i=252)
    assert int(fired.sum()) == 1 and fired[258]
    assert drops["break"] == 7         # i in 252..257 and 259 fail the break
    assert drops["break_no_reclaim"] == 0 and drops["range"] == 0
    assert drops["dvol"] == 0 and drops["range_undefined"] == 0
    assert bool(book[258])             # close 99.5 >= $1; med60 dvol 1e8 >= $2M


def test_gap_fade_confirm_sides():
    """Threshold semantics pinned INCLUSIVE: fade FIRED iff gap <= P_pctl;
    confirm FIRED iff gap >= P_pctl; the big opposite-side gap never fires."""
    n = 256
    cl = 100.0 + 0.01 * np.arange(n)
    o = np.concatenate([[100.0], cl[:-1] * 1.0001])   # +1bp overnight gaps
    h, lo = cl + 0.1, cl - 0.1
    v = np.full(n, 1e6)
    down, up = cfg("SSS-GAP-P25-FADE-H1"), cfg("SSS-GAP-P25-CONFIRM-H1")
    # a -5% gap day: FADE fires (gap <= P25); CONFIRM does not
    o_dn = o.copy()
    o_dn[255] = cl[254] * 0.95
    f_fade, _b1, d1 = L.run_config_census(down, o_dn, h, lo, cl, v, first_i=252)
    f_conf, _b2, d2 = L.run_config_census(up, o_dn, h, lo, cl, v, first_i=252)
    assert bool(f_fade[255])
    assert int(f_fade.sum()) == 4            # +1bp days sit exactly ON P25
    assert not f_conf[255]
    assert int(f_conf.sum()) == 3 and d2["no_side"] == 1
    # a +5% gap day: CONFIRM fires; FADE does not
    o_up = o.copy()
    o_up[255] = cl[254] * 1.05
    f_fade2, _b3, _d3 = L.run_config_census(down, o_up, h, lo, cl, v, first_i=252)
    f_conf2, _b4, _d4 = L.run_config_census(up, o_up, h, lo, cl, v, first_i=252)
    assert not f_fade2[255]
    assert bool(f_conf2[255])
    assert int(f_conf2.sum()) == 4


def test_52w_high_bands():
    n = 260
    o, h, lo, cl, v = flat_series(n)
    cl[255:] = 95.0                    # 5% below the 100 high
    o[255:] = 94.5
    h[255:] = 96.0
    lo[255:] = 94.0
    b5, b2 = cfg("SSS-52W-HIGH-B5-H5"), cfg("SSS-52W-HIGH-B2-H5")
    f5, _b1, d5 = L.run_config_census(b5, o, h, lo, cl, v, first_i=252)
    f2, _b2, d2 = L.run_config_census(b2, o, h, lo, cl, v, first_i=252)
    # sessions 252..254 sit AT the high (proximity 0 -> inside every band);
    # sessions 255..259 sit 5% below (inside 5%, outside 2%)
    assert int(f5.sum()) == 8
    assert list(np.nonzero(f5)[0]) == list(range(252, 260))
    assert int(f2.sum()) == 3 and list(np.nonzero(f2)[0]) == [252, 253, 254]
    assert d2["outside_band"] == 5
    assert d5["outside_band"] == 0


def test_52w_high_zero_high_never_crashes_and_never_fires():
    """Real-data regression (r2, disclosed): zero-priced OTC shells carry a
    252-session adjusted high of exactly 0.0 — proximity is UNDEFINED there,
    the state NEVER fires, the bar is censused (history_undefined); r1
    crashed with ZeroDivisionError on this input."""
    n = 300
    cl = np.zeros(n)
    o = np.zeros(n)
    h = np.zeros(n)
    lo = np.zeros(n)
    v = np.full(n, 1e6)
    c = cfg("SSS-52W-HIGH-B2-H5")
    fired, book, drops = L.run_config_census(c, o, h, lo, cl, v)
    assert int(fired.sum()) == 0
    assert not book.any()
    assert drops["history_undefined"] == n - 252
    assert drops["outside_band"] == 0


def test_dvol_shock_direction_needs_price_side():
    n = 80
    o, h, lo, cl, v = flat_series(n)
    conf = cfg("SSS-DVOL-SHOCK-R1.5x-CONFIRM-H1")
    fade = cfg("SSS-DVOL-SHOCK-R1.5x-FADE-H1")
    # UP shock at i=70 (5x volume, +1% close): confirm fires, fade does not
    v[70], cl[70], h[70], o[70], lo[70] = 5e6, 101.0, 102.0, 100.5, 100.0
    fc, _b1, dc = L.run_config_census(conf, o, h, lo, cl, v, first_i=70)
    ff, _b2, df = L.run_config_census(fade, o, h, lo, cl, v, first_i=70)
    assert bool(fc[70]) and not ff[70]
    # DOWN shock at i=71 (5x volume, -2% close): fade fires, confirm does not
    v[71], cl[71], lo[71], o[71], h[71] = 5e6, 99.0, 98.5, 100.0, 100.5
    fc2, _b3, dc2 = L.run_config_census(conf, o, h, lo, cl, v, first_i=70)
    ff2, _b4, df2 = L.run_config_census(fade, o, h, lo, cl, v, first_i=70)
    assert not fc2[71] and bool(ff2[71])
    assert dc2["neutral_ret"] >= 1     # the fade-unfriendly side is censused
    # a 2x shock day is a 1.5x shock but NOT a 3.0x shock
    r3 = cfg("SSS-DVOL-SHOCK-R3.0x-CONFIRM-H1")
    v[72], cl[72], h[72], o[72], lo[72] = 2e6, 101.0, 101.5, 100.0, 99.5
    fc3, _b5, _dc3 = L.run_config_census(r3, o, h, lo, cl, v, first_i=70)
    assert not fc3[72]


def test_vol_regime_terciles_causal_never_full_sample():
    n = 600
    o, h, lo, cl, v = flat_series(n)
    # quiet 0..399 (tiny oscillation), volatile 400..599 (large oscillation)
    cl[:400] = 100.0 + 0.001 * np.sin(0.3 * np.arange(400))
    cl[400:] = 100.0 + 3.0 * np.sin(0.7 * np.arange(200))
    low = cfg("SSS-VOL-REGIME-L21-LOW-H5")
    high = cfg("SSS-VOL-REGIME-L21-HIGH-H5")
    fl, _b1, dl = L.run_config_census(low, o, h, lo, cl, v)
    fh, _b2, dh = L.run_config_census(high, o, h, lo, cl, v)
    first_i = 251 + 21
    assert dl["warmup"] == 0 and dh["warmup"] == 0
    assert dl["history_undefined"] == 0 and dh["history_undefined"] == 0
    # same-bar assignment on the trailing window only: the LOW tercile is
    # populated in the quiet region, the HIGH tercile in the volatile region
    assert fl[first_i:400].sum() > 0
    assert fh[400:].sum() > 0
    # the two directions never fire on the same session (middle = flat)
    assert not np.any(fl & fh)


# ------------------------------------------- 4. folds (F8 freeze, frozen first)

def test_fold_boundaries_calendar_thirds():
    b1, b2 = L.fold_boundaries()
    d0 = date.fromisoformat(L.WINDOW_START)
    d1 = date.fromisoformat(L.WINDOW_END)
    total = (d1 - d0).days
    assert date.fromisoformat(b1) - d0 == datetime.timedelta(days=total // 3)
    assert date.fromisoformat(b2) - d0 == datetime.timedelta(days=(2 * total) // 3)
    assert d0 < date.fromisoformat(b1) < date.fromisoformat(b2) < d1


def test_fold_assignment_semantics():
    b1, b2 = L.fold_boundaries()
    assert L.assign_fold(L.WINDOW_START, b1, b2) == "F1"
    assert L.assign_fold(b1, b1, b2) == "F1"            # F1 = [start, B1]
    assert L.assign_fold(b2, b1, b2) == "F2"            # F2 = (B1, B2]
    assert L.assign_fold(L.WINDOW_END, b1, b2) == "F3"  # F3 = (B2, end]


def test_regime_never_share_law():
    """2008Q4-2009 and 2020-03 never share a fold: distinct folds when both
    sit inside the window; moot when the window starts 2015+."""
    b1, b2 = L.fold_boundaries("2005-01-03", "2021-12-31")
    assert L.assign_fold("2008-12-15", b1, b2) != L.assign_fold("2020-03-15", b1, b2)
    assert L.never_share_law_ok(b1, b2, "2005-01-03", "2021-12-31") is True
    # frozen 2015+ window: 2008Q4-2009 predates it -> rule moot but holds
    fb1, fb2 = L.fold_boundaries()
    assert L.never_share_law_ok(fb1, fb2, L.WINDOW_START, L.WINDOW_END) is True
    # window whose in-window regimes land together still satisfies the law
    # only when one regime predates it; both inside one fold is impossible by
    # construction (calendar thirds put 2008 and 2020 nine years apart)
    with pytest.raises(ValueError):
        L.fold_boundaries("2020-01-01", "2019-01-01")


def test_committed_freeze_artifacts_match_law():
    fold = json.loads((P0 / "fold_freeze.json").read_text())
    assert fold["schema"] == "stocks_search_v1_fold_freeze@1"
    assert fold["window"] == [L.WINDOW_START, L.WINDOW_END]
    assert fold["boundaries"] == dict(zip(("B1", "B2"), L.fold_boundaries()))
    assert fold["folds"][0]["start"] == L.WINDOW_START
    assert fold["folds"][2]["end"] == L.WINDOW_END
    assert fold["q6_floor"]["floor"] == 30
    assert fold["q6_floor"]["measured"] is False   # census NOT_RUN on this path
    assert "2020-03" in fold["regime_law"]
    cc = json.loads((P0 / "census_configs.json").read_text())
    assert cc["grid"]["n_configs"] == 47
    assert len(cc["configs"]) == 47
    assert "zero_range_law" in cc["conventions"]
    assert cc["conventions"]["percentile_method"] == "linear"
    cb = json.loads((P0 / "cost_bands.json").read_text())
    assert cb["schedule"]["band_bps"] == {"A": 10, "B": 15, "C": 25}
    assert cb["schedule"]["bands_def"] == {"A": 50e6, "B": 10e6, "C": 2e6}
    ck = json.loads((P0 / "clock_contract.json").read_text())
    assert ck["decision"].startswith("at session t CLOSE")
    assert ck["fills"] == {"entry": "t+1 OPEN", "exit": "t+1+H OPEN"}
    gi = P0 / "raw" / ".gitignore"
    assert gi.exists() and "*" in gi.read_text()


# --------------------------------------------------------- 5. gate logic (F1)

def test_key_status_never_leaks_material():
    ks = L.key_status({"EODHD_API_KEY": "secret-material-123"})
    assert ks["present"] is True
    assert "secret-material-123" not in json.dumps(ks)
    ks2 = L.key_status({})
    assert ks2["present"] is False


def test_three_layer_gate_fail_closed():
    ok_reach = {"SPY": {"status": 200}, "QQQ": {"status": 200}}
    ok_served = {"SPY": {"status": 200, "has_adjusted_close": True,
                         "has_volume": True}}
    assert L.three_layer_gate(ok_reach, True, ok_served)["pass"] is True
    # one layer down -> gate FAILS (fail-closed, never an inferred PASS)
    assert L.three_layer_gate({**ok_reach, "X": {"status": 404}}, True,
                              ok_served)["pass"] is False
    assert L.three_layer_gate(ok_reach, False, ok_served)["pass"] is False
    bad_served = {"SPY": {"status": 200, "has_adjusted_close": False,
                          "has_volume": True}}
    assert L.three_layer_gate(ok_reach, True, bad_served)["pass"] is False
    assert L.three_layer_gate({}, True, ok_served)["pass"] is False
    assert L.three_layer_gate(ok_reach, True, {})["pass"] is False


def test_blocked_assembly_is_honest():
    gates = L.blocked_gates("EODHD_API_KEY absent", {"key": L.key_status({})})
    assert gates["F1"]["verdict"] == "FAIL"
    for gid in ("F2", "F3", "F4", "F5", "F6", "F7", "F8"):
        assert gates[gid]["verdict"] == "NOT_RUN"
        assert gates[gid]["detail"]["blocked_by"] == "F1"
        assert gates[gid]["detail"]["fail_closed"] is True
    assert gates["F9"]["verdict"] == "NOT_RUN"
    body = L.assemble_gate(gates)
    assert body["overall_verdict"] == "BLOCKED_SOURCE_OR_SCHEMA"
    assert body["outcome"] == "STOCKS_SEARCH_V1_BLOCKED_SOURCE_OR_SCHEMA"
    assert body["d2_status"] == "SKIPPED_BY_OWNER_AMENDMENT_3B"
    assert body["r0_status"] == "NOT_RUN"
    assert body["no_pnl_computed"] is True
    assert "R0 NOT_RUN (D2 skipped by owner amendment §3b)" in \
        body["relaxation_disclosure"]
    # the blocked gate never fabricates a measurement
    assert '"verdict": "PASS"' not in json.dumps(body)


def test_assembly_verdict_mapping():
    gates = {gid: L.verdict_row("PASS", "law", {}) for gid in
             ("F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9")}
    assert L.assemble_gate(gates)["overall_verdict"] == "PASS"
    gates["F8"] = L.verdict_row("FAIL", "law", {})
    assert L.assemble_gate(gates)["overall_verdict"] == "FAIL_FAIL_CLOSED"
    gates["F8"] = L.verdict_row("NOT_RUN", "law", {})
    assert L.assemble_gate(gates)["overall_verdict"] == "NOT_RUN_FAIL_CLOSED"


# ---------------------------------------------------------- 6. clock (F5)

def test_clock_legs_frozen():
    assert L.clock_legs(100, 5) == (100, 101, 106)
    assert L.clock_legs(10, 1) == (10, 11, 12)
    assert L.clock_legs(0, 20) == (0, 1, 21)
    with pytest.raises(ValueError):
        L.clock_legs(10, 0)
    hs = sorted({c["params"]["H"] for c in L.enumerate_configs()})
    assert hs == [1, 5, 10, 20]


def test_dst_never_duplicates_or_drops_a_session_date():
    """Sessions are ISO dates on the XNYS calendar; the 2026 spring-forward
    (Mar 8, America/New_York) changes UTC offsets, never the date set."""
    ny = ZoneInfo("America/New_York")
    sessions = ["2026-03-06", "2026-03-09", "2026-03-10"]  # Fri, Mon, Tue
    offsets = []
    for s in sessions:
        d = date.fromisoformat(s)
        noon = datetime.datetime(d.year, d.month, d.day, 12, tzinfo=ny)
        offsets.append(noon.utcoffset().total_seconds() / 3600)
    assert offsets[0] == -5.0 and offsets[1] == -4.0    # DST boundary crossed
    assert len(set(sessions)) == 3                       # no duplicates
    b1, b2 = L.fold_boundaries()
    assert L.assign_fold(sessions[0], b1, b2) == "F3"    # date-keyed, TZ-free


# ------------------------------------------------- 7. cost bands (F6, pinned)

def test_band_schedule_fail_closed():
    assert L.BAND_BPS == {"A": 10, "B": 15, "C": 25}
    assert L.BANDS_DEF == {"A": 50e6, "B": 10e6, "C": 2e6}
    assert L.resolve_band(50e6) == "A"
    assert L.resolve_band(49_999_999.0) == "B"
    assert L.resolve_band(10e6) == "B"
    assert L.resolve_band(9_999_999.0) == "C"
    assert L.resolve_band(2e6) == "C"
    assert L.resolve_band(1_999_999.0) == "SUBFLOOR"
    with pytest.raises(ValueError):
        L.resolve_band(float("nan"))
    with pytest.raises(ValueError):
        L.resolve_band(None)
    # stress ceiling law: worst band x 2 fills x stress 2.0 = 100 bps
    assert L.WORST_CASE_BPS_ROUNDTRIP == 100


# --------------------------------------------- 8. bookability floors (F4)

def test_bookability_floors_applied_at_fired_decisions():
    fired = np.array([False, True, True, False, True])
    adj_close = np.array([100.0, 0.5, 2.0, 100.0, 100.0])
    med60 = np.array([1e8, 3e6, 1e6, 1e8, 2e6])
    book = L._bookable(fired, adj_close, np.zeros(5), med60)
    assert [bool(b) for b in book] == [False, False, False, False, True]
    # non-finite med60 fails the floor (never defaults to bookable); the
    # $1-pass + med-pass cell (index 2) stays bookable
    med_bad = np.array([1e8, np.nan, 1e8, 1e8, 1e8])
    book2 = L._bookable(fired, adj_close, np.zeros(5), med_bad)
    assert [bool(b) for b in book2] == [False, False, True, False, True]


def test_event_unwind_floor_drops_counted():
    n = 260
    cl = np.full(n, 0.5)               # sub-$1 name
    lo, h, o = cl - 0.01, cl + 0.01, cl - 0.005
    v = np.full(n, 1e6)
    lo[258] = 0.40                     # break vs prior low 0.49
    cl[258] = 0.505                    # reclaim above 0.49
    h[258] = 0.51                      # range ~0.95
    v[258] = 4e6                       # participation: 0.505*4e6 vs med 5e5
    c = cfg("SSS-EVENT-UNWIND-K21-H5")
    fired, book, drops = L.run_config_census(c, o, h, lo, cl, v, first_i=252)
    assert int(fired.sum()) == 1
    assert drops["floor_price"] == 1   # $0.505 < $1.00
    assert drops["floor_dvol"] == 1    # med60 dvol 5e5 < $2M
    assert not book[258]


# ------------------------------------------- 9. band resolution ON fired set

def test_band_on_fired_population_and_share():
    n = 260
    o, h, lo, cl, v = flat_series(n)
    lo[258], cl[258], h[258], v[258] = 98.5, 99.5, 100.5, 2e6
    c = cfg("SSS-EVENT-UNWIND-K21-H5")
    fired, _book, _drops = L.run_config_census(c, o, h, lo, cl, v, first_i=252)
    dvol = cl * v
    med252 = L._rolling_median(dvol, 252)
    idx = np.nonzero(fired)[0]
    assert idx.tolist() == [258]
    assert [L.resolve_band(float(med252[i])) for i in idx] == ["A"]
    # fired-day share on this fixture: 1 fired / 8 eligible sessions
    assert abs(1 / (n - 252) - 0.125) < 1e-12


# -------------------------------------------- 10. redaction hygiene (F1 law)

def test_redact_strips_token_from_errors():
    dirty = ("HTTP GET https://eodhd.com/api/eod/SPY.US?api_token=SECRET"
             "&fmt=json failed")
    clean = L.redact(dirty)
    assert "SECRET" not in clean
    assert "api_token=REDACTED" in clean
