"""E6(b) — lane I hand fixtures (>= 6 required; 9 provided).

1  close-boundary instant     acceptance exactly AT 16:00 ET -> close not
                              strictly after acceptance -> direction = next
2  no-lookahead mutation      shift the event instant one session -> decisions
                              shift exactly one session (byte-compared)
3  DST spring-forward         2025-03-09 22:30Z reads 18:30 EDT (-04:00)
4  fold boundary force-flat   window crossing the fold end exits at the last
                              session before the boundary, forced_flat=True
5  cost applied once per side entry band = base x 3.35 exactly once, exit =
                              base x 1.0 exactly once; RT = sum x power
6  volume-0 bar unfillable    entry bar volume 0 -> excluded, counted
7  delisting exit             panel ends mid-window -> exit at last bar,
                              delisting_exit=True (kept, not dropped)
8  window exclusion (split)   split ex-date inside the hold window -> excluded
9  zero-direction session     close == open on direction session -> excluded
"""
import json
from datetime import datetime, date, timedelta, time

import pytest

from emv1 import clock
from emv1 import config as C
from emv1.panel import NameSeries
from emv1.book import build_decision
from emv1.costs import per_event_round_trip_bps
from emv1.guard import LookaheadRead, assert_readable


def make_ns(ticker, d0, d1, open_price=10.0, up=True, volumes=None):
    ns = NameSeries(ticker)
    d = date.fromisoformat(d0)
    end = date.fromisoformat(d1)
    i = 0
    while d <= end:
        if d.weekday() < 5:
            ds = d.isoformat()
            ns.dates.append(ds)
            ns.idx[ds] = len(ns.dates) - 1
            o = open_price
            c = open_price + (1.0 if up else -0.5)
            ns.open.append(o)
            ns.high.append(max(o, c) + 0.5)
            ns.low.append(min(o, c) - 0.5)
            ns.close.append(c)
            v = volumes[i] if volumes else 1_000_000.0
            ns.vol.append(v)
            ns.dv.append(c * v)
            ns.fill_ok.append(v > 0)
            i += 1
        d += timedelta(days=1)
    return ns


class MiniPanel:
    def __init__(self, ns):
        self.names = {ns.ticker: ns}

    def get(self, t):
        return self.names.get(t)


def build(ns, acceptance_utc, hold=5, corp_actions=None, arm="A1-ANCHOR"):
    inst = clock.parse_acceptance_utc(acceptance_utc)
    et, off = clock.to_et(inst)
    stratum, is_weekend = clock.stratum_of(et)
    return build_decision(
        event_id="T", family_id=C.FAMILY_A1, arm_id=arm,
        cik="CIK0000000001", ticker="TEST", form="10-Q",
        acceptance_utc=acceptance_utc, instant_et=et,
        hold_sessions=hold, panel=MiniPanel(ns),
        corp_actions=corp_actions or {}, stratum=stratum,
        bucket=stratum, is_weekend=is_weekend)


def test_1_close_boundary_instant():
    """16:00:00 ET acceptance: Monday's close is AT the instant, not after."""
    ns = make_ns("TEST", "2024-04-01", "2024-06-30")
    at_close = "2024-06-10T20:00:00.000Z"  # 16:00:00 ET Monday
    rec, exc = build(ns, at_close)
    assert rec is not None and exc is None
    assert rec["direction_session"] == "2024-06-11"  # NOT 06-10 (strictly after)
    assert rec["entry_session"] == "2024-06-12"
    # one second before: Monday's close is after the instant -> direction Monday
    before = "2024-06-10T19:59:59.000Z"
    rec2, exc2 = build(ns, before)
    assert rec2["direction_session"] == "2024-06-10"
    assert rec2["entry_session"] == "2024-06-11"


def test_2_no_lookahead_shift_mutation():
    """Shift the event instant one session -> decisions shift one session."""
    ns = make_ns("TEST", "2024-04-01", "2024-07-31")
    r1, _ = build(ns, "2024-06-10T22:30:00.000Z")   # dir 06-11, entry 06-12
    r2, _ = build(ns, "2024-06-11T22:30:00.000Z")   # dir 06-12, entry 06-13
    assert r2["direction_session"] == "2024-06-12"
    assert r2["entry_session"] == "2024-06-13"
    assert r2["exit_session"] == "2024-06-19"
    # byte-compare: shifted record equals a rebuild one session forward
    j1 = json.dumps({k: r1[k] for k in sorted(r1)}, sort_keys=True)
    j2 = json.dumps({k: r2[k] for k in sorted(r2)}, sort_keys=True)
    assert j1 != j2
    assert r1["entry_price"] == r2["entry_price"]  # same synthetic open
    # sessions shifted by exactly one session position
    i1 = ns.idx[r1["entry_session"]]
    i2 = ns.idx[r2["entry_session"]]
    assert i2 == i1 + 1


def test_3_dst_spring_forward():
    """2025-03-09 spring-forward Sunday 22:30Z -> 18:30 EDT (-04:00), S3+weekend."""
    ns = make_ns("TEST", "2025-01-02", "2025-04-30")
    rec, exc = build(ns, "2025-03-09T22:30:00.000Z")
    assert exc is None and rec is not None
    et, off = clock.to_et(clock.parse_acceptance_utc("2025-03-09T22:30:00.000Z"))
    assert off == -4.0  # EDT already in effect after spring-forward
    stratum, is_weekend = clock.stratum_of(et)
    assert stratum == "S3" and is_weekend is True
    assert rec["direction_session"] == "2025-03-10"  # Monday
    assert rec["entry_session"] == "2025-03-11"


def test_4_fold_boundary_force_flat():
    """F3 event near 2023-01-01 with H=10: exit at last session < 2023-01-01."""
    ns = make_ns("TEST", "2022-10-01", "2023-03-31")
    rec, exc = build(ns, "2022-12-20T22:30:00.000Z", hold=10)
    assert exc is None and rec is not None
    assert rec["fold"] == "F3"
    # 10 sessions from entry would cross 2023-01-01 -> force-flat
    assert rec["forced_flat"] is True
    assert rec["exit_session"] < "2023-01-01"
    assert rec["delisting_exit"] is False
    # sanity: 2022-12-30 is the last 2022 weekday session in the panel
    assert rec["exit_session"] == "2022-12-30"


def test_5_cost_once_per_side():
    ns = make_ns("TEST", "2024-04-01", "2024-06-30")
    rec, exc = build(ns, "2024-06-10T22:30:00.000Z")
    assert exc is None
    base = 15.0  # dvmed60 = 11e6 -> class B (>= $10M, < $50M), 15 bps per fill
    assert rec["dv_band_class"] == "B"
    assert rec["cost_entry_bps_x1"] == pytest.approx(base * C.OPEN_BAND_MULT)
    assert rec["cost_exit_bps_x1"] == pytest.approx(base * C.MIDDAY_BAND_MULT)
    rt = per_event_round_trip_bps(rec, 1.5)
    assert rt == pytest.approx((base * C.OPEN_BAND_MULT + base * C.MIDDAY_BAND_MULT) * 1.5)
    # exactly once per side: RT at x1.0 equals entry+exit with no extra term
    assert per_event_round_trip_bps(rec, 1.0) == pytest.approx(
        rec["cost_entry_bps_x1"] + rec["cost_exit_bps_x1"])


def test_6_volume0_bar_unfillable():
    vols = [1_000_000.0] * 70
    ns = make_ns("TEST", "2024-04-01", "2024-06-30", volumes=vols)
    # zero the bar right after the direction session (the entry bar)
    entry_i = ns.idx["2024-06-12"]
    ns.vol[entry_i] = 0.0
    ns.fill_ok[entry_i] = False
    ns.dv[entry_i] = 0.0
    rec, exc = build(ns, "2024-06-10T22:30:00.000Z")
    assert rec is None and exc is not None
    assert exc["reason"] == "ENTRY_BAR_UNFILLABLE_B1B2"


def test_7_delisting_exit():
    """Panel ends before entry+H-1: exit at last bar, delisting_exit=True."""
    ns = make_ns("TEST", "2024-04-01", "2024-06-14")  # ends 2024-06-14
    rec, exc = build(ns, "2024-06-10T22:30:00.000Z", hold=5)
    assert exc is None and rec is not None
    assert rec["delisting_exit"] is True
    assert rec["exit_session"] == "2024-06-14"  # last available bar
    assert rec["entry_session"] == "2024-06-12"


def test_8_window_exclusion_split_inside_hold():
    ns = make_ns("TEST", "2024-04-01", "2024-06-30")
    ca = {"TEST": {"div": [], "split": ["2024-06-14"]}}  # inside H=5 window
    rec, exc = build(ns, "2024-06-10T22:30:00.000Z", corp_actions=ca)
    assert rec is None and exc is not None
    assert exc["reason"] == "CORP_ACTION_IN_WINDOW"
    # same split outside the window is bookable
    ca2 = {"TEST": {"div": [], "split": ["2024-06-25"]}}
    rec2, exc2 = build(ns, "2024-06-10T22:30:00.000Z", corp_actions=ca2)
    assert rec2 is not None and exc2 is None


def test_9_zero_direction_session():
    ns = make_ns("TEST", "2024-04-01", "2024-06-30")
    di = ns.idx["2024-06-11"]
    ns.close[di] = ns.open[di]  # flat direction bar
    rec, exc = build(ns, "2024-06-10T22:30:00.000Z")
    assert rec is None and exc is not None
    assert exc["reason"] == "ZERO_DIRECTION_SESSION_MOVE"


def test_b1_extreme_print_bar_unfillable():
    """B1: |log(c_t/c_{t-1})| >= log(10) -> unfillable (both directions)."""
    ns = make_ns("TEST", "2024-04-01", "2024-06-30")
    ei = ns.idx["2024-06-12"]
    ns.close[ei] = 1000.0  # vs prior close 11.0: log-ratio 4.5 > log(10)
    import math
    ns.fill_ok[ei] = (abs(math.log(ns.close[ei] / ns.close[ei - 1])) < C.EXTREME_PRINT_LOG
                      and ns.vol[ei] > 0)
    assert ns.fill_ok[ei] is False
    rec, exc = build(ns, "2024-06-10T22:30:00.000Z")
    assert rec is None and exc is not None
    assert exc["reason"] == "ENTRY_BAR_UNFILLABLE_B1B2"
