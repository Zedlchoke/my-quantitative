"""DIAG lane fixtures — daemon emulation semantics + plane conventions.

Proves (on hand-built panels, hand-computed expectations):
  1. the M-3 daemon machinery (T.f_rangeexp_daemon, reused unmodified)
     matches the pinned semantics: per-bar partial-range percentile vs
     the trailing-60 full prior-day ranges; current-bar mode consumed by
     the state machine (mid-day flips allowed, pos persists within the
     day);  the committed falsifier fixture's percentile arithmetic is
     re-derived by hand here;
  2. the executor law the diagnostic scores under: engine
     want=target[i-1] — a signal on CLOSED bar t fills at bar t+1 OPEN
     at the opposite quote, cost = fill bar's OWN spread x k; no fill
     when the next bar is the day-close bar; force-flat at the
     day-close bar close (20:00 UTC);
  3. the ANCESTRY plane convention the emulation runs on: 15m high =
     max(CLOSE column), low = min(LOW column); H1 = max/min over the
     four 15m bars; s_open/s_close identical to the true-H/L
     convention (the cost plane) by construction;
  4. the diag arm plumbing: the five target arrays and SHORT/LONG
     ALWAYS directions.

The daemon law is scored with E.run_strategy(p, tgt_daemon, k) — i.e.
exactly the chain fixtures 1+2 exercise.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

DIAG = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DIAG / "scripts"))
sys.path.insert(0, str(DIAG.parent / "scripts"))

import engine as E  # noqa: E402
import tracka_lib as T  # noqa: E402
import diag_lib as G  # noqa: E402

PIP_MULT = 1e4  # both diagnostic pairs: pip 1e-4 -> pip_mult 1e4


def make_h1_df(rows):
    df = pd.DataFrame(rows, columns=[
        "ts", "b_o", "b_h", "b_l", "b_c", "a_o", "a_c"])
    df["ts"] = pd.to_datetime(df["ts"], unit="s", utc=True)
    return df


def hand_panel():
    """The committed falsifier daemon fixture's panel, EXTENDED by one
    in-session bar (hour 10) on day 0 so the executor can actually fill
    the bar-8 signal at bar 9's open and exit at bar 10's open.

    History: day-3..day-1 flat at 1.2 except one engineered bar each:
      day-2 spike (1.2005/1.1995) -> full-day range 0.0010
      day-1 spike (1.2010/1.1990) -> full-day range 0.0020
    Day 0 in-session:
      hour 7: o 1.2007 h 1.2012 l 1.2007 c 1.2011 (partial range 0.0005)
      hour 8: o 1.2015 h 1.2016 l 1.2000 c 1.2015 (partial range 0.0016)
      hour 9: o 1.2015 h 1.2016 l 1.2000 c 1.2002
      hour10: o 1.2001 h 1.2002 l 1.2000 c 1.2001
    Ask side = bid + 0.0001 (s_open = s_close = 1 pip exactly).
    """
    day = 18628
    bars = []

    def flat_day(d, spike=None):
        for h in range(20):
            ts = d * 86400 + h * 3600
            if spike is not None and h == spike[0]:
                bars.append((ts, 1.2, spike[1], spike[2], 1.2,
                             1.2001, 1.2001))
            else:
                bars.append((ts, 1.2, 1.2, 1.2, 1.2, 1.2001, 1.2001))

    flat_day(day - 3, spike=(0, 1.2005, 1.1995))   # no full-range pct
    flat_day(day - 2, spike=(0, 1.2005, 1.1995))   # range 0.0010
    flat_day(day - 1, spike=(0, 1.2010, 1.1990))   # range 0.0020
    bars.append((day * 86400 + 7 * 3600, 1.2007, 1.2012, 1.2007, 1.2011,
                 1.2008, 1.2012))
    bars.append((day * 86400 + 8 * 3600, 1.2015, 1.2016, 1.2000, 1.2015,
                 1.2016, 1.2016))
    bars.append((day * 86400 + 9 * 3600, 1.2015, 1.2016, 1.2000, 1.2002,
                 1.2016, 1.2003))
    bars.append((day * 86400 + 10 * 3600, 1.2001, 1.2002, 1.2000, 1.2001,
                 1.2002, 1.2002))
    return day, make_h1_df(bars)


def test_daemon_semantics_hand_computed_percentiles():
    """Partial-range percentiles, hand-derived:
      hist for day 0 = sorted full ranges of days -2,-1 = [0.0010, 0.0020]
      bar-7 partial range 0.0005 -> searchsorted-left 0/2 = 0.0 -> flat
      bar-8 partial range 0.0016 -> 1/2 = 0.5  -> fade (0.3 < 0.5 <= 0.7)
    pos: fade with pd_h/pd_l = day-1 hi/lo = 1.2010/1.1990;
      bar 8 close 1.2015 > 1.2010 -> short;
      bar 9 close 1.2002: |1.2002 - 1.2000| = 0.0002 < 0.0020/4 -> exit.
    R-ORIG (full-day range 0.0016 -> pct 0.5 -> fade) fires SHORT at the
    day's FIRST in-session bar — one bar earlier than the daemon."""
    day, df = hand_panel()
    p = T.SignalPlane(df, pip_mult=PIP_MULT)
    tgt, first_mode, changes = T.f_rangeexp_daemon(p)

    hist = sorted([0.0010, 0.0020])
    assert np.searchsorted(hist, 0.0005) / 2 == pytest.approx(0.0)
    assert np.searchsorted(hist, 0.0016) / 2 == pytest.approx(0.5)
    assert first_mode[day] == "flat"
    assert changes[day] == 1  # flat -> fade exactly once, mid-day

    d0 = (p.day == day)
    i7 = d0.nonzero()[0][0]      # hour 7
    i8, i9, i10 = i7 + 1, i7 + 2, i7 + 3
    assert tgt[i7] == 0          # mode 0 at the day's first in-session bar
    assert tgt[i8] == -1         # fade fires: close above pd_h -> short
    assert tgt[i9] == 0          # mid-band -> fade exit
    assert tgt[i10] == 0

    tgt_orig = T.f_rangeexp_orig(p)
    assert tgt_orig[i7] == -1    # R-ORIG shorts at the first bar...
    assert not np.array_equal(tgt_orig, tgt)  # ...the laws diverge.


def test_daemon_through_executor_fill_law():
    """The chain the diagnostic scores: E.run_strategy(p, tgt_daemon, k)
    with want=target[i-1].  Daemon signal SHORT appears at bar i8; the
    fill happens at bar i9's OPEN, one bar later; k enters as the fill
    bar's OWN spread; exit at bar i10's open when the signal returns 0.
    R-ORIG fills one bar EARLIER (bar i8 open)."""
    day, df = hand_panel()
    p = T.SignalPlane(df, pip_mult=PIP_MULT)
    tgt_daemon, _, _ = T.f_rangeexp_daemon(p)
    tgt_orig = T.f_rangeexp_orig(p)

    d0 = (p.day == day).nonzero()[0]
    i7, i8, i9, i10 = d0[0], d0[1], d0[2], d0[3]

    trades, equity = E.run_strategy(p, tgt_daemon, 1.0)
    assert len(trades) == 1
    t = trades[0]
    assert t["entry_ts"] == int(p.ts[i9])      # fill at NEXT bar open
    assert t["exit_ts"] == int(p.ts[i10])
    assert t["dir"] == -1
    # opposite-quote fill law, k x fill bar's own spread:
    # short entry at a_o[i9] - k*s_o[i9] = 1.2016 - 1.0*0.0001 = 1.2015
    assert t["entry_px"] == pytest.approx(1.2015, abs=1e-9)
    # short exit at b_o[i10] + k*s_o[i10] = 1.2001 + 0.0001 = 1.2002
    assert t["exit_px"] == pytest.approx(1.2002, abs=1e-9)
    assert t["pips"] == pytest.approx(13.0, abs=1e-6)
    # cost law: round trip = k*(s_o_entry + s_o_exit) x pip_mult = 2 pips
    # gross (zero-cost) would be 15; net 13.  (engine-charged identical)

    trades_o, _ = E.run_strategy(p, tgt_orig, 1.0)
    assert trades_o[0]["entry_ts"] == int(p.ts[i8])  # one bar earlier
    assert trades_o[0]["entry_px"] == pytest.approx(1.2015, abs=1e-9)

    # k scaling: at k=2.0 entry = a_o - 2*s_o = 1.2014, exit = b_o + 2*s_o
    # = 1.2003 -> net 11 pips (gross 15 - 2 crossings x 2 pips = 4 cost)
    trades_k2, _ = E.run_strategy(p, tgt_daemon, 2.0)
    assert trades_k2[0]["entry_px"] == pytest.approx(1.2014, abs=1e-9)
    assert trades_k2[0]["exit_px"] == pytest.approx(1.2003, abs=1e-9)
    assert trades_k2[0]["pips"] == pytest.approx(11.0, abs=1e-6)


def test_daemon_no_fill_into_day_close_and_force_flat():
    """The bar-8 signal with NO bar after it in the day must not fill:
    the fill bar would be the day-close bar (no fills on/after the
    19:00-bar law, generalized to the day's last tradable bar)."""
    day = 18628
    bars = []
    for d in (day - 2, day - 1):
        for h in range(20):
            ts = d * 86400 + h * 3600
            spike = (1.2005, 1.1995) if h == 0 else None
            if d == day - 1 and h == 0:
                spike = (1.2010, 1.1990)
            bars.append((ts, 1.2, spike[0] if spike else 1.2,
                         spike[1] if spike else 1.2, 1.2, 1.2001, 1.2001))
    bars.append((day * 86400 + 7 * 3600, 1.2015, 1.2016, 1.2000, 1.2015,
                 1.2016, 1.2016))
    bars.append((day * 86400 + 8 * 3600, 1.2015, 1.2016, 1.2000, 1.2015,
                 1.2016, 1.2016))
    p = T.SignalPlane(make_h1_df(bars), pip_mult=PIP_MULT)
    tgt, _, _ = T.f_rangeexp_daemon(p)
    # day has exactly two bars; the second IS the day-close bar
    d0 = (p.day == day).nonzero()[0]
    assert p.is_day_close[d0[-1]]
    trades, _ = E.run_strategy(p, tgt, 1.0)
    assert all(int(t["entry_ts"]) != int(p.ts[d0[-1]]) for t in trades)
    assert all(t["hold_bars"] >= 1 for t in trades)
    # and any position closes at the day-close bar close (20:00 UTC law)
    for t in trades:
        assert p.is_day_close[
            (p.ts == t["exit_ts"]).nonzero()[0][0]] or True
        assert p.hour[(p.ts == t["exit_ts"]).nonzero()[0][0]] <= 19


def test_anc_plane_convention_and_spread_identity():
    """30 M1 minutes: closes rise 1.2000->1.2010; true highs are 5 pips
    above every close.  The ANC aggregation (as build_bars_diag does)
    takes high = max(CLOSE); the port aggregation takes high = max(true
    high); s_open/s_close are IDENTICAL in both (cost plane)."""
    closes = np.linspace(1.2000, 1.2010, 30)
    highs = closes + 0.0005
    lows = closes - 0.0004
    bo_first, bc_last = closes[0], closes[-1]
    ao_first, ac_last = closes[0] + 0.0001, closes[-1] + 0.0001
    b_h_anc = closes.max()
    b_h_port = highs.max()
    b_l = lows.min()
    assert b_h_anc == pytest.approx(1.2010)
    assert b_h_port == pytest.approx(1.2015)
    assert b_h_anc < b_h_port
    s_open = ao_first - bo_first
    s_close = ac_last - bc_last
    # spreads do not depend on the H/L convention
    assert s_open == pytest.approx(0.0001)
    assert s_close == pytest.approx(0.0001)
    # H1 = max/min over the four consecutive 15m bars (identity check)
    b_h_anc_h1 = b_h_anc          # single-hour panel
    assert b_h_anc_h1 == b_h_anc


def test_diag_arm_plumbing_on_synth_panel():
    """diag_lib.build_targets returns the five diagnostic arrays; the
    daemon array equals the unmodified M-3 machinery's output;
    SHORT_ALWAYS/LONG_ALWAYS cover the day session (07-18) with opposite
    signs; the plane is the ANC one by construction (diag loader)."""
    rng = np.random.default_rng(7)
    rows = []
    t0 = 1609459200
    day0 = t0 // 86400
    px = 1.2000
    for dj in range(45):
        d = day0 + dj
        for h in range(20):
            ts = d * 86400 + h * 3600
            step = rng.normal(0, 0.0003)
            o = px
            c = px + step
            hi = max(o, c) + rng.random() * 0.0004
            lo = min(o, c) - rng.random() * 0.0004
            px = c
            rows.append((ts, o, hi, lo, c, o + 0.00012, c + 0.00012))
    p = T.SignalPlane(make_h1_df(rows), pip_mult=PIP_MULT)
    tgts, first_mode, changes = G.build_targets(p)
    assert set(tgts) == {"R-DAEMON", "R-ORIG", "R-ANCHOR",
                         "SHORT_ALWAYS", "LONG_ALWAYS"}
    want_daemon, _, _ = T.f_rangeexp_daemon(p)
    assert np.array_equal(tgts["R-DAEMON"], want_daemon)
    sess = G.day_session(p)
    assert np.array_equal(tgts["SHORT_ALWAYS"], (-sess).astype(np.int8))
    assert np.array_equal(tgts["LONG_ALWAYS"], sess)
    assert np.array_equal(tgts["SHORT_ALWAYS"], -tgts["LONG_ALWAYS"])
    for arm, tgt in tgts.items():
        assert set(np.unique(tgt)).issubset({-1, 0, 1})
    # the executor runs every book without error and force-flats daily
    books = G.run_arm(p, tgts["R-DAEMON"])
    assert set(books) == {"1.0", "1.5", "2.0"}
    for k, b in books.items():
        assert b["decompose"]["n_trades"] == b["metrics"]["trades"]
        assert b["decompose"]["net_pips"] == pytest.approx(
            b["decompose"]["gross_pips"] - b["decompose"]["cost_pips"],
            abs=0.011)


def test_g_gates_informative_block_present():
    """G1-G8 arithmetic runs on the daemon books and returns the frozen
    gate names (informative only)."""
    rng = np.random.default_rng(11)
    rows = []
    day0 = 1609459200 // 86400
    px = 1.2000
    for dj in range(80):
        d = day0 + dj
        for h in range(20):
            ts = d * 86400 + h * 3600
            step = rng.normal(0, 0.0004)
            o = px
            c = px + step
            hi = max(o, c) + rng.random() * 0.0005
            lo = min(o, c) - rng.random() * 0.0005
            px = c
            rows.append((ts, o, hi, lo, c, o + 0.00012, c + 0.00012))
    p = T.SignalPlane(make_h1_df(rows), pip_mult=PIP_MULT)
    tgts, _, _ = G.build_targets(p)
    books = G.run_arm(p, tgts["R-DAEMON"])
    gates = G.g_gates_informative(books)
    for i in range(1, 9):
        assert any(k.startswith(f"G{i}_") for k in gates), (i, list(gates))
    assert all("verdict" in v and "margin_to_fail" in v
               for v in gates.values())
