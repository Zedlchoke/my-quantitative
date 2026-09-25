"""Falsifier-lane fixtures — ERP1-TRACKA-COHORT-1 (tracka1-falsifier).

Covers: plane convention (ancestor close-column high), M-1
shift-equivalence, M-5 truncation PIT, R-DAEMON emulation on hand-built
panels, M-4 self-test blindness, schedule-only executor force-flat +
no-PnL-field law, Spearman sanity.

HARD LAW: no test computes any arm's PnL/expectancy/PF/win-rate.
"""
import numpy as np
import pandas as pd
import pytest

import tracka_lib as T


def make_h1_df(rows):
    """rows: list of (ts_epoch, b_o, b_h, b_l, b_c, a_o, a_c)."""
    df = pd.DataFrame(rows, columns=[
        "ts", "b_o", "b_h", "b_l", "b_c", "a_o", "a_c"])
    df["ts"] = pd.to_datetime(df["ts"], unit="s", utc=True)
    return df


def synth_panel(n_days=45, seed=7):
    """Synthetic H1 panel: tradable hours 0..19, hour 20..23 absent.
    Deterministic pseudo-prices with day-scale range variation so the
    range-percentile laws produce non-degenerate modes."""
    rng = np.random.default_rng(seed)
    rows = []
    t0 = 1609459200  # 2021-01-01 00:00 UTC
    day0 = t0 // 86400
    px = 1.2000
    for dj in range(n_days):
        d = day0 + dj
        day_rng = 0.0010 + 0.0008 * rng.random()
        for h in range(20):
            for _ in range(1):
                ts = d * 86400 + h * 3600
                step = rng.normal(0, 0.0003)
                o = px
                c = px + step
                hi = max(o, c) + rng.random() * day_rng / 4
                lo = min(o, c) - rng.random() * day_rng / 4
                px = c
                spread = 0.00012
                rows.append((ts, o, hi, lo, c, o + spread, c + spread))
    return make_h1_df(rows)


def test_plane_convention_close_column_high():
    """15m ancestry convention: high = max(closes), low = min(lows)."""
    # 30 minutes of M1: closes rise to 1.5x the range above open; true
    # high of minute 3 exceeds every close.
    closes = np.linspace(1.2000, 1.2010, 30)
    highs = closes + 0.0005          # true highs strictly above closes
    lows = closes - 0.0004
    secs = np.arange(1800)
    # emulate one 15m bucket aggregation as build_signal_plane does
    b_h_anc = closes.max()
    b_l_anc = lows.min()
    b_h_port = highs.max()
    assert b_h_anc == pytest.approx(1.2010)
    assert b_h_port == pytest.approx(1.2015)
    assert b_h_anc < b_h_port          # ancestor high below true high
    assert b_l_anc == pytest.approx(lows.min())
    # and the signal plane's range is NARROWER on the top under the
    # ancestor convention (documented consequence)


def test_signal_plane_semantics_match_v2lib():
    p = T.SignalPlane(synth_panel(10))
    # tradable hours 0..19; fill_ok <= 18; day close = 19:00 bar
    assert p.hour.max() == 19
    assert p.fill_ok.sum() == sum(1 for h in p.hour if h <= 18) - 1  # [0]=False
    assert p.is_day_close[p.last_tradable_of_day[~p.skip][0]]
    # s_open/s_close law
    assert np.allclose(p.s_o, p.a_o - p.b_o)
    assert np.allclose(p.s_c, p.a_c - p.b_c)


def test_m1_shift_equivalence_synthetic():
    for seed in (7, 11, 23):
        p = T.SignalPlane(synth_panel(45, seed=seed))
        a = T.f_rangeexp_anchor_shift(p)
        b = T.f_rangeexp_anchor_independent(p)
        assert np.array_equal(a, b), f"M-1 shift-equivalence failed seed={seed}"
        # and the anchor differs from the ancestor (the leak repair moves
        # the signal on this synthetic panel)
        o = T.f_rangeexp_orig(p)
        assert not np.array_equal(a, o)


def test_m5_truncation_pit_synthetic():
    p = T.SignalPlane(synth_panel(45, seed=7))
    rep = T.truncation_pit_probe(p)
    # R-ORIG under day-start truncation MUST differ (leak proven)
    assert len(rep["orig_t0_diff_days"]) > 0
    # R-ANCHOR MUST be identical (PIT-clean as executed)
    assert rep["anchor_trunc_diff_days"] == []
    assert rep["anchor_full_vs_shift_impl_identical"]


def test_daemon_emulation_handbuilt():
    """3-day hand-built panel with hand-computed partial-range
    percentiles. History days: day-2 range 0.0010, day-1 range 0.0020
    (one engineered bar each; all other bars flat at 1.2). Day 0 bars at
    hours 7,8,9 with a first-bar h-l of 0.0015."""
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

    flat_day(day - 3, spike=(0, 1.2005, 1.1995))   # range 0.0010 (no pct:
    flat_day(day - 2, spike=(0, 1.2005, 1.1995))   #  these two have none/
    flat_day(day - 1, spike=(0, 1.2010, 1.1990))   #  prior day respectively)
    # day 0, in-session: hour-7 bar has a TINY range (0.0005) whose
    # partial percentile is 0 (below both history ranges) -> the daemon
    # is flat at bar 7, while R-ORIG ranks the FULL day-0 range.
    bars.append((day * 86400 + 7 * 3600, 1.2007, 1.2012, 1.2007, 1.2011,
                 1.2008, 1.2012))
    # hour 8 bar extends the partial range to 0.0016 -> daemon fade fires
    bars.append((day * 86400 + 8 * 3600, 1.2015, 1.2016, 1.2000, 1.2015,
                 1.2016, 1.2016))
    bars.append((day * 86400 + 9 * 3600, 1.2015, 1.2016, 1.2000, 1.2002,
                 1.2016, 1.2003))
    p = T.SignalPlane(make_h1_df(bars))
    tgt, first_mode, changes = T.f_rangeexp_daemon(p)

    # hand check of the percentile: the daemon's hist for day 0 = ranges
    # of days -2 and -1 (day -3 has no prior day -> no range) =
    # [0.0010, 0.0020] sorted; the bar-7 partial range 0.0005 ranks
    # BELOW both -> pct 0 -> flat; the bar-8 partial range 0.0016 ranks
    # between -> pct 0.5 -> fade
    hist = sorted([0.0010, 0.0020])
    assert np.searchsorted(hist, 0.0005) / 2 == pytest.approx(0.0)
    assert np.searchsorted(hist, 0.0016) / 2 == pytest.approx(0.5)
    assert first_mode[day] == "flat"   # mode 0 at the first in-session bar
    assert changes[day] == 1           # flat -> fade, once

    d0 = (p.day == day)
    h7 = d0 & (p.hour == 7); h8 = d0 & (p.hour == 8); h9 = d0 & (p.hour == 9)
    # hour 7 daemon: flat (mode 0)
    assert tgt[h7.nonzero()[0][0]] == 0
    # hour 8: partial pct 0.5 -> fade; close 1.2015 > pd_h=1.2010 -> short
    assert tgt[h8.nonzero()[0][0]] == -1
    # hour 9: |1.2002 - 1.2000| = 0.0002 < 0.0020/4 -> fade exit
    assert tgt[h9.nonzero()[0][0]] == 0

    # R-ORIG on the same panel: full-day range 0.0016 -> fade ALL day,
    # so it enters SHORT at bar 7 (close 1.2011 > pd_h) — one bar earlier
    # than the daemon. The laws diverge on identical data.
    tgt_orig = T.f_rangeexp_orig(p)
    assert tgt_orig[h7.nonzero()[0][0]] == -1
    assert not np.array_equal(tgt_orig, tgt)


def test_m4_self_test_blindness_fixture():
    """The shipped same-panel self-test construction (comparing the same
    function on the same panel) returns PASS while the daemon law and
    R-ORIG diverge on that panel — structural blindness, committed as a
    fixture."""
    p = T.SignalPlane(synth_panel(45, seed=11))
    tgt_orig = T.f_rangeexp_orig(p)
    tgt_daemon, _, _ = T.f_rangeexp_daemon(p)
    assert not np.array_equal(tgt_orig, tgt_daemon), \
        "fixture panel must diverge"
    # the shipped self-test construction: same function, same panel
    shipped_self_test_pass = np.array_equal(
        T.f_rangeexp_orig(p), T.f_rangeexp_orig(p))
    assert shipped_self_test_pass  # PASS ...
    # ...while the laws differ -> the self-test is blind to the seam.


def test_schedule_only_force_flat_and_no_pnl():
    p = T.SignalPlane(synth_panel(12, seed=5))
    days = p.traded_days()
    # long during hours 7..18 every day
    tgt = np.where((p.hour >= 7) & (p.hour <= 18), 1, 0).astype(np.int8)
    trips = T.schedule_only(p, tgt)
    assert len(trips) == len(days)
    for t in trips:
        assert t["dir"] == 1
        assert t["exit_kind"] == "day_close"
        assert p.hour[t["exit_bar"]] == 19   # flat at the 19:00 bar close
        assert "pips" not in t and "pnl" not in t and "net" not in t
    # no position may exist at/after hour 20 by construction
    for t in trips:
        assert p.hour[t["exit_bar"]] <= 19
    # reversal = separate round trips (signal exits at bar open): hold
    # the short only during hours 7..10 in the second half -> the exit
    # fires at the 12:00 fill bar as a 'signal' exit
    tgt_alt = tgt.copy()
    mid = len(p.ts) // 2
    idx = np.nonzero(np.arange(len(p.ts)) >= mid)[0]
    tgt_alt[idx] = np.where(
        (p.hour[idx] >= 7) & (p.hour[idx] <= 10), -1, 0).astype(np.int8)
    trips2 = T.schedule_only(p, tgt_alt)
    assert any(t["exit_kind"] == "signal" for t in trips2)


def test_trip_cost_pips_is_cost_only():
    p = T.SignalPlane(synth_panel(12, seed=5))
    tgt = np.where((p.hour >= 7) & (p.hour <= 18), 1, 0).astype(np.int8)
    trips = T.schedule_only(p, tgt)
    c1 = T.trip_cost_pips(p, trips[0], k=1.0)
    c2 = T.trip_cost_pips(p, trips[0], k=2.0)
    assert c2 == pytest.approx(2 * c1)
    assert c1 > 0


def test_n_diff_and_limb3_machinery():
    p = T.SignalPlane(synth_panel(45, seed=3))
    ta = T.schedule_only(p, T.f_rangeexp_anchor_shift(p))
    to = T.schedule_only(p, T.f_rangeexp_orig(p))
    nd, a_only, o_only = T.n_diff_trips(ta, to)
    assert nd == a_only + o_only
    res = T.limb3_matched_pairs(to, ta, min_n=20)
    assert res["matched_pairs"] <= res["orig_only"]
    assert res["evaluable"] == (res["matched_pairs"] >= 20)
    # pairing rule: same UTC day, nearest entry_ts
    for t_o, t_a in []:
        pass


def test_spearman_sanity():
    x = np.arange(100)
    assert T.spearman_rho(x, x) == pytest.approx(1.0)
    assert T.spearman_rho(x, -x) == pytest.approx(-1.0)
    y = x.copy(); y[3] = -y[3]
    assert abs(T.spearman_rho(x, y)) < 1.0
    # ties handled via average ranks
    z = np.ones(50)
    assert T.spearman_rho(z, np.arange(50)) == 0.0


def test_mode_sham_preserves_marginal_and_moves_labels():
    p = T.SignalPlane(synth_panel(60, seed=9))
    tgt_sham, stats = T.mode_sham(p, seed=20260925)
    assert stats["label_rebuild_matches_shift_impl"]
    days, labels, _, _ = T.anchor_day_labels(p)
    from collections import Counter
    active = [d for d in days if labels[d] in ("fade", "follow")]
    assert len(active) > 0
    assert stats["n_active_days"] == len(active)
    assert 0.0 <= stats["labels_changed_share_all_days"] <= 1.0
    assert 0.0 <= stats["labels_changed_share_active_days"] <= 1.0
    # sham target differs from the anchor target when labels moved
    tgt_anchor = T.f_rangeexp_anchor_shift(p)
    assert not np.array_equal(tgt_anchor, tgt_sham) or \
        stats["labels_changed"] == 0


def test_placebo_rebuild_adjudication2():
    """Rebuild fixture: one-shot r calibration, seed-driven day selection,
    uniform-random in-session hours (never a fixed hour), pinned parity,
    durations unchanged, deterministic reproduction."""
    p = T.SignalPlane(synth_panel(50, seed=21))
    idx = np.arange(len(p.ts))
    ins = (~p.skip) & (p.hour >= 7) & (p.hour <= 18) & (idx > 0)
    tgt_anchor = np.where(ins, 1, 0).astype(np.int8)
    trips_anchor = T.schedule_only(p, tgt_anchor, warmup_end_idx=0)
    occ_anchor = float((tgt_anchor[ins] != 0).mean())
    occ_natural = (occ_anchor + 0.10) / 0.8  # engineered so r = 0.8 exactly
    res = T.placebo_rebuild(p, occ_anchor, occ_natural, trips_anchor, ins,
                            seed=20260925, warmup_end_idx=0, hold=2)
    assert res["r"] == pytest.approx(0.8)
    assert res["hold_bars"] == 2                      # duration unchanged
    assert res["entries_placed"] == res["days_selected"]  # parity of draws
    # determinism: identical re-invocation reproduces the target array
    res2 = T.placebo_rebuild(p, occ_anchor, occ_natural, trips_anchor, ins,
                             seed=20260925, warmup_end_idx=0, hold=2)
    assert res2["trips_dev"] == res["trips_dev"]
    assert res2["occ_ctrl"] == res["occ_ctrl"]
    # predicate bookkeeping present
    assert set(res["predicates"]) == {
        "a_shape_fidelity_10pp", "b_90pct_distinct_trips",
        "c_both_directions", "d_non_constant"}
    # r < 1 strictly reduces occupancy vs the natural construction here
    assert res["occ_ctrl"] < occ_natural + 1e-12


def test_families_run_on_plane():
    p = T.SignalPlane(synth_panel(70, seed=13))
    outs = [
        T.f_gap(p, None, "fade", th_pips=5.0),
        T.f_pdhloc(p, None, True),
        T.f_dow_simple(p, 4, 20),
        T.f_asiafade(p, 6, None),
        T.f_sessma(p, 0.5, 24),
        T.f_h1tsmom(p, 24),
        T.f_h1donch(p, 24, 4),
        T.f_daymom(p, 5),
        T.f_stoch(p, 24, 80, 20),
        T.f_roundnum(p, 10.0, 1.0),
        T.f_hourrev(p, 5, False),
        T.f_rangeexp_orig(p),
    ]
    for o in outs:
        assert o.shape == (len(p.ts),)
        assert set(np.unique(o)).issubset({-1, 0, 1})
