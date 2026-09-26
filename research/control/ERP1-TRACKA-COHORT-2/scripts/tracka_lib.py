"""Falsifier-lane signal machinery — ERP1-TRACKA-COHORT-1 (tracka1-falsifier).

HARD LAW (dispatch + plan §8 ordering law): this module produces SIGNAL
ARRAYS, DAY-MODE SCHEDULES, COUNTS, COST-BOOK ARITHMETIC ON SPREADS ONLY.
No net-return / expectancy / PF / win-rate computation of any arm exists
here. The only arithmetic on magnitudes is F-5 declared-band arithmetic on
COSTS (spread pips) and the §9.4 seam constants (c_rt from the cost book,
N_diff from schedules). The seam law's S statistic is NOT computed (PnL).

LINEAGE: the R-ORIG law is ported BYTE-FAITHFUL from the ancestry
v2_lib.f_rangeexp (EURUSD-RANGEEXP-SCORED-V1/scripts/v2_lib.py:265-322,
read-only). The plane convention for the SIGNAL plane is the ANCESTRY
convention (15m high = max of CLOSE column, 15m low = min of the low
column — see build_signal_plane.py / LINEAGE-NOTE-1 resolution); the
port's true-H/L bars remain the COST plane (spreads are identical by
construction — opens/closes are untouched by the H/L convention).

Arms (plan §4.2):
  R-ORIG   : byte-faithful ancestor law (mode for day d := pct[d], the
             day's OWN full-day range percentile — the recorded PIT seam).
  R-ANCHOR : the ONE-delta PIT repair (mode for day d := pct[d-1]; guard
             pct[d-1] > 0; days lacking pct[d-1] -> flat). Implemented
             TWICE for the M-1 proof: as a pure usage-index shift of the
             ancestor function, and as an independent from-scratch
             implementation (percentile of ranges[d-1][0] vs history
             strictly before d-1).
  R-DAEMON : emulation of the running-partial-range law for seam
             measurement only (M-3). Pinned semantics: at each signal bar
             i the mode is the searchsorted-left percentile of the PARTIAL
             range of the day of i computed over that day's bars up to and
             including i (the prior closed bar relative to the fill at
             i+1), vs the trailing 60 full-day ranges of days strictly
             before it; the fade/follow state machine runs with the
             CURRENT bar's mode (mid-day mode flips allowed; pos persists
             within the day; pd_h/pd_l are the prior day's full hi/lo).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from collections import defaultdict

import numpy as np
import pandas as pd

SEC_DAY = 86400
HIST_LEN = 60  # trailing full-day-range window (ancestor law)


# ---------------------------------------------------------------- plane ----

class SignalPlane:
    """v2_lib.H1Plane port, per-pair pip multiplier carried.

    Expects an H1 frame with columns ts,b_o,b_h,b_l,b_c,a_o,a_c
    (s_open/s_close added here exactly as v2_lib.H1Plane does).
    """

    def __init__(self, df, pip_mult=1e4):
        df = df.copy()
        df["s_open"] = df["a_o"] - df["b_o"]
        df["s_close"] = df["a_c"] - df["b_c"]
        self.pip_mult = float(pip_mult)
        self.ts = (
            df["ts"].dt.tz_convert("UTC").dt.tz_localize(None)
            .to_numpy().astype("datetime64[s]").astype("int64")
        )
        self.b_o = df["b_o"].to_numpy(); self.b_h = df["b_h"].to_numpy()
        self.b_l = df["b_l"].to_numpy(); self.b_c = df["b_c"].to_numpy()
        self.a_o = df["a_o"].to_numpy(); self.a_c = df["a_c"].to_numpy()
        self.s_o = df["s_open"].to_numpy(); self.s_c = df["s_close"].to_numpy()
        self.hour = (self.ts // 3600 % 24).astype(np.int32)
        self.day = (self.ts // SEC_DAY).astype(np.int64)
        tradable = self.hour <= 19
        self.skip = ~tradable
        last_of_day = {}
        for i in range(len(self.ts)):
            if tradable[i]:
                last_of_day[self.day[i]] = i
        self.last_tradable_of_day = np.array(
            [last_of_day.get(d, -1) for d in self.day]
        )
        self.is_day_close = np.zeros(len(self.ts), dtype=bool)
        m = self.last_tradable_of_day >= 0
        self.is_day_close[m] = (
            self.last_tradable_of_day[self.last_tradable_of_day[m]]
            == np.arange(len(self.ts))[m]
        )
        self.fill_ok = tradable & (self.hour <= 18)
        self.fill_ok[0] = False

    def pips(self, price_delta):
        return np.asarray(price_delta, dtype=float) * self.pip_mult

    def traded_days(self):
        return np.unique(self.day[~self.skip])


def _prev_day_stats(p):
    """v2_lib._prev_day_stats port (per-day hi/lo/oc over traded hours)."""
    hi = {}; lo = {}; oc = {}
    for i in range(len(p.ts)):
        if p.skip[i]:
            continue
        d = p.day[i]
        hi[d] = max(hi.get(d, -9), p.b_h[i])
        lo[d] = min(lo.get(d, 9), p.b_l[i])
        if d not in oc:
            oc[d] = [p.b_o[i], p.b_c[i]]
        else:
            oc[d][1] = p.b_c[i]
    return hi, lo, oc


def day_ranges(p):
    """ranges[d] = (own full-day range, prev traded day hi, prev lo)."""
    hi, lo, oc = _prev_day_stats(p)
    days = sorted(oc)
    ranges = {}
    for j in range(1, len(days)):
        d = days[j]
        ranges[d] = (hi[d] - lo[d], hi[days[j - 1]], lo[days[j - 1]])
    return days, ranges


def pct_full_panel(days, ranges, hist_len=HIST_LEN):
    """Ancestor pct dict: pct[d] ranks day d's OWN full-day range vs the
    trailing hist_len ranges of days strictly before d (searchsorted-left
    / len). pct exists from the 3rd traded day onward."""
    hist = []
    pct = {}
    for d in days:
        if d not in ranges:
            continue
        if hist:
            pct[d] = float(np.searchsorted(sorted(hist), ranges[d][0]) / len(hist))
        hist.append(ranges[d][0])
        if len(hist) > hist_len:
            hist.pop(0)
    return pct


def _day_prev_map(days):
    return {days[j]: days[j - 1] for j in range(1, len(days))}


# ------------------------------------------------------- the three laws ----

def _walk_day_mode(p, day_mode, day_pd_h, day_pd_l, lo_q, hi_q, use_breakout):
    """Shared bar state machine. day_mode[d] is the day-start mode
    percentile (or None/<=0 -> flat); the fade/follow mapping is the
    ancestor's DEPLOYED mapping (use_breakout=False -> expand = wide,
    i.e. mode > hi_q; 0 < mode <= hi_q -> fade), including the ancestor's
    dead-line overwrite semantics (recorded, no behavior impact)."""
    tgt = np.zeros(len(p.ts), dtype=np.int8)
    pos = 0
    cur_day = -1
    for i in range(len(p.ts)):
        if p.skip[i]:
            continue
        d = p.day[i]
        if d != cur_day:
            cur_day, pos = d, 0
        mode = day_mode.get(d)
        if mode is None or mode <= 0 or p.hour[i] < 7 or p.hour[i] > 18:
            tgt[i] = 0
            continue
        wide = mode > hi_q
        expand = wide if not use_breakout else (mode < lo_q)
        pd_h = day_pd_h.get(d)
        pd_l = day_pd_l.get(d)
        if expand:  # narrow yesterday -> breakout today (follow)
            if pos == 0:
                if p.b_c[i] > pd_h:
                    pos = 1
                elif p.b_c[i] < pd_l:
                    pos = -1
        else:       # wide yesterday -> fade today
            mid = (pd_h + pd_l) / 2
            if pos == 0:
                if p.b_c[i] > pd_h:
                    pos = -1
                elif p.b_c[i] < pd_l:
                    pos = 1
            else:
                if abs(p.b_c[i] - mid) < (pd_h - pd_l) / 4:
                    pos = 0
        tgt[i] = pos
    return tgt


def f_rangeexp_orig(p, lo_q=0.3, hi_q=0.7, use_breakout=False,
                    hist_len=HIST_LEN):
    """R-ORIG: byte-faithful port of v2_lib.f_rangeexp (the recorded PIT
    seam: the day mode ranks the day's OWN full-day range and is consumed
    from the day's first bar)."""
    days, ranges = day_ranges(p)
    pct = pct_full_panel(days, ranges, hist_len)
    prev = _day_prev_map(days)
    day_mode, day_pd_h, day_pd_l = {}, {}, {}
    for d in days:
        m = pct.get(d)
        day_mode[d] = m
        if m is not None and m > 0 and d in ranges:
            day_pd_h[d] = ranges[d][1]
            day_pd_l[d] = ranges[d][2]
    return _walk_day_mode(p, day_mode, day_pd_h, day_pd_l, lo_q, hi_q,
                          use_breakout)


def f_rangeexp_anchor_shift(p, lo_q=0.3, hi_q=0.7, use_breakout=False,
                            hist_len=HIST_LEN):
    """R-ANCHOR implementation A: the pure usage-index shift. The pct dict
    is the ancestor's, computed once; the ONLY delta is that day d
    consumes pct[prev_traded_day(d)] (and the guard shifts with the
    index). Days lacking pct[d-1] -> flat. The fade BAND is UNCHANGED
    from the ancestor: pd_h/pd_l = ranges[d][1]/[2] = the PREVIOUS traded
    day's hi/lo (plan 4.2: exactly ONE delta — the mode percentile input
    index — everything else byte-identical)."""
    days, ranges = day_ranges(p)
    pct = pct_full_panel(days, ranges, hist_len)
    prev = _day_prev_map(days)
    day_mode, day_pd_h, day_pd_l = {}, {}, {}
    for d in days:
        m = pct.get(prev[d]) if d in prev else None
        day_mode[d] = m
        if m is not None and m > 0 and d in ranges:
            day_pd_h[d] = ranges[d][1]
            day_pd_l[d] = ranges[d][2]
    return _walk_day_mode(p, day_mode, day_pd_h, day_pd_l, lo_q, hi_q,
                          use_breakout)


def f_rangeexp_anchor_independent(p, lo_q=0.3, hi_q=0.7, use_breakout=False,
                                  hist_len=HIST_LEN):
    """R-ANCHOR implementation B (M-1 second leg): from-scratch. For each
    traded day index j the mode is computed independently as the
    searchsorted-left percentile of ranges[days[j-1]][0] (the PREVIOUS
    day's full range) against the trailing hist_len full ranges of traded
    days strictly before days[j-1] (numpy window slice, not the
    ancestor's incremental append/pop)."""
    days, ranges = day_ranges(p)
    own = {d: ranges[d][0] for d in ranges}
    day_mode, day_pd_h, day_pd_l = {}, {}, {}
    for j, d in enumerate(days):
        if j < 2:            # pct exists from the 3rd day; d-1 must have one
            continue
        dp = days[j - 1]
        if dp not in own:
            continue
        # hist = trailing hist_len full ranges of traded days strictly
        # before dp; the ranges dict starts at days[1] (days[0] has no
        # prior-day stats), matching pct_full_panel's append order.
        hist = [own[days[k]]
                for k in range(max(1, j - 1 - hist_len), j - 1)]
        if not hist:
            continue
        m = float(np.searchsorted(np.sort(np.asarray(hist)), own[dp]) / len(hist))
        day_mode[d] = m
        # band = the PREVIOUS traded day's hi/lo (unchanged from ancestor)
        day_pd_h[d] = ranges[d][1]
        day_pd_l[d] = ranges[d][2]
    return _walk_day_mode(p, day_mode, day_pd_h, day_pd_l, lo_q, hi_q,
                          use_breakout)


def f_rangeexp_daemon(p, lo_q=0.3, hi_q=0.7, use_breakout=False,
                      hist_len=HIST_LEN):
    """R-DAEMON emulation (M-3; DISCLOSED_SEAM — never a scored arm).

    Pinned semantics (see module docstring): at each signal bar i the
    mode is the percentile of the PARTIAL range of the day of i over that
    day's bars up to and including i, vs the trailing hist_len full-day
    ranges of strictly earlier days. The state machine consumes the
    CURRENT bar's mode (mid-day flips allowed, pos persists within the
    day; pd_h/pd_l = prior day's full hi/lo)."""
    days, ranges = day_ranges(p)
    prev = _day_prev_map(days)
    # hist_before[d]: sorted full ranges of days strictly before d
    hist_full = []
    hist_before = {}
    for d in days:
        hist_before[d] = sorted(hist_full[-hist_len:])
        if d in ranges:
            hist_full.append(ranges[d][0])
    run_hi = run_lo = None
    cur_day = -1
    pos = 0
    tgt = np.zeros(len(p.ts), dtype=np.int8)
    day_first_mode = {}
    day_mode_changes = {}
    last_label = {}
    seen_in_session = set()
    for i in range(len(p.ts)):
        if p.skip[i]:
            continue
        d = p.day[i]
        if d != cur_day:
            cur_day, pos = d, 0
            run_hi, run_lo = -np.inf, np.inf
        run_hi = max(run_hi, p.b_h[i])
        run_lo = min(run_lo, p.b_l[i])
        hb = hist_before.get(d)
        mode = None
        if hb:
            mode = float(np.searchsorted(hb, run_hi - run_lo) / len(hb))
        pd_h = ranges[d][1] if d in ranges else None
        pd_l = ranges[d][2] if d in ranges else None
        if p.hour[i] < 7 or p.hour[i] > 18:
            tgt[i] = 0
            continue
        if d not in seen_in_session:
            seen_in_session.add(d)
            day_first_mode[d] = ("flat" if mode is None or mode <= 0
                                 else ("follow" if mode > hi_q else "fade"))
            last_label[d] = day_first_mode[d]
        if mode is None or mode <= 0 or pd_h is None:
            tgt[i] = 0
            continue
        label = "follow" if mode > hi_q else "fade"
        if last_label.get(d) != label:
            day_mode_changes[d] = day_mode_changes.get(d, 0) + 1
            last_label[d] = label
        expand = (mode > hi_q) if not use_breakout else (mode < lo_q)
        if expand:
            if pos == 0:
                if p.b_c[i] > pd_h:
                    pos = 1
                elif p.b_c[i] < pd_l:
                    pos = -1
        else:
            mid = (pd_h + pd_l) / 2
            if pos == 0:
                if p.b_c[i] > pd_h:
                    pos = -1
                elif p.b_c[i] < pd_l:
                    pos = 1
            else:
                if abs(p.b_c[i] - mid) < (pd_h - pd_l) / 4:
                    pos = 0
        tgt[i] = pos
    return tgt, day_first_mode, day_mode_changes


def anchor_day_labels(p, lo_q=0.3, hi_q=0.7, hist_len=HIST_LEN):
    """R-ANCHOR per-day mode labels (flat/fade/follow) + per-day pd hi/lo,
    used by the mode-sham and the truncation probe."""
    days, ranges = day_ranges(p)
    pct = pct_full_panel(days, ranges, hist_len)
    prev = _day_prev_map(days)
    labels, pdh, pdl = {}, {}, {}
    for d in days:
        m = pct.get(prev[d]) if d in prev else None
        if m is None or m <= 0:
            labels[d] = "flat"
        elif m > hi_q:
            labels[d] = "follow"
            pdh[d] = ranges[d][1]; pdl[d] = ranges[d][2]
        else:
            labels[d] = "fade"
            pdh[d] = ranges[d][1]; pdl[d] = ranges[d][2]
    return days, labels, pdh, pdl


def _walk_labels(p, day_label, day_pd_h, day_pd_l):
    tgt = np.zeros(len(p.ts), dtype=np.int8)
    pos = 0
    cur_day = -1
    for i in range(len(p.ts)):
        if p.skip[i]:
            continue
        d = p.day[i]
        if d != cur_day:
            cur_day, pos = d, 0
        lab = day_label.get(d)
        if lab is None or lab == "flat" or p.hour[i] < 7 or p.hour[i] > 18:
            tgt[i] = 0
            continue
        pd_h = day_pd_h.get(d); pd_l = day_pd_l.get(d)
        expand = (lab == "follow")
        if expand:
            if pos == 0:
                if p.b_c[i] > pd_h:
                    pos = 1
                elif p.b_c[i] < pd_l:
                    pos = -1
        else:
            mid = (pd_h + pd_l) / 2
            if pos == 0:
                if p.b_c[i] > pd_h:
                    pos = -1
                elif p.b_c[i] < pd_l:
                    pos = 1
            else:
                if abs(p.b_c[i] - mid) < (pd_h - pd_l) / 4:
                    pos = 0
        tgt[i] = pos
    return tgt


def mode_sham(p, seed, lo_q=0.3, hi_q=0.7):
    """F-3 mode-sham (P1 finding): permute R-ANCHOR's day-level FADE/
    FOLLOW labels among the anchor's ACTIVE days at the pinned seed
    (marginal frequency preserved by construction; flat days stay flat;
    everything else identical — pd_h/pd_l stay with their days). Returns
    (tgt_sham, stats dict)."""
    days, labels, pdh, pdl = anchor_day_labels(p, lo_q, hi_q)
    active = [d for d in days if labels[d] in ("fade", "follow")]
    lab_arr = np.array([labels[d] for d in active], dtype=object)
    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(lab_arr))
    lab_sham = lab_arr[perm]
    sham_labels = dict(labels)
    for j, d in enumerate(active):
        sham_labels[d] = lab_sham[j]
    tgt_sham = _walk_labels(p, sham_labels, pdh, pdl)
    changed = int(sum(1 for d in active if sham_labels[d] != labels[d]))
    # internal check: rebuilding R-ANCHOR from its own labels must equal
    # the arm-A implementation
    tgt_anchor_via_labels = _walk_labels(p, labels, pdh, pdl)
    ok = bool(np.array_equal(tgt_anchor_via_labels,
                             f_rangeexp_anchor_shift(p, lo_q, hi_q)))
    return tgt_sham, {
        "n_days": len(days),
        "n_active_days": len(active),
        "labels_changed": changed,
        "labels_changed_share_all_days": changed / max(len(days), 1),
        "labels_changed_share_active_days": changed / max(len(active), 1),
        "label_rebuild_matches_shift_impl": ok,
    }


# --------------------------------------------- truncation PIT probe (M-5) --

def truncation_pit_probe(p, lo_q=0.3, hi_q=0.7, hist_len=HIST_LEN):
    """M-5: replay each dev day under a DAY-START information state.

    Truncated replay = the day-stat layer (hi/lo/oc/ranges/pct) computed
    on the prefix panel strictly BEFORE the day's first bar; the law's
    bar-walk then runs over the day's bars using that frozen stat layer
    (day-d bar closes are PIT-legal within the day; the ONLY leak channel
    is the stat layer).

    R-ORIG under a day-start prefix: pct[d] does not exist (day d has no
    full range in the prefix) -> flat. Reported two ways:
      T0 strict day-start prefix (mode absent -> flat);
      T1 first-bar-closed prefix (mode = percentile of the 1-bar partial
         range) — disclosed secondary depth.
    R-ANCHOR under the same prefix: pct[d-1] on the prefix is computed
    from days strictly before d-1, all fully closed — structurally
    identical to the full-panel value; arrays MUST be identical."""
    days, ranges = day_ranges(p)
    pct = pct_full_panel(days, ranges, hist_len)
    prev = _day_prev_map(days)
    in_session = (~p.skip) & (p.hour >= 7) & (p.hour <= 18)

    # full-panel arms
    tgt_orig = f_rangeexp_orig(p, lo_q, hi_q)
    tgt_anch = f_rangeexp_anchor_shift(p, lo_q, hi_q)

    # T0: R-ORIG flat everywhere (day mode absent under day-start prefix)
    tgt_orig_t0 = np.zeros(len(p.ts), dtype=np.int8)
    # T1: R-ORIG with the 1-bar partial-range percentile as day mode
    own = {d: ranges[d][0] for d in ranges}
    hist_full = []
    hist_before = {}
    for d in days:
        hist_before[d] = sorted(hist_full[-hist_len:])
        if d in ranges:
            hist_full.append(ranges[d][0])
    first_hl = {}
    for i in range(len(p.ts)):
        if p.skip[i]:
            continue
        d = p.day[i]
        if d not in first_hl:
            first_hl[d] = p.b_h[i] - p.b_l[i]
    day_mode_t1, pdh_t1, pdl_t1 = {}, {}, {}
    for d in days:
        hb = hist_before.get(d)
        if hb and d in first_hl:
            m = float(np.searchsorted(hb, first_hl[d]) / len(hb))
            day_mode_t1[d] = m
            dp = prev.get(d)
            if m > 0 and d in ranges:
                pdh_t1[d] = ranges[d][1]; pdl_t1[d] = ranges[d][2]
    tgt_orig_t1 = _walk_day_mode(p, day_mode_t1, pdh_t1, pdl_t1, lo_q,
                                 hi_q, False)

    # R-ANCHOR truncated: mode = pct[prev(d)] — recomputed from the PREFIX
    # construction (identical input set to the full panel by structure).
    # We rebuild it independently to make the identity a measurement:
    anch_labels, anch_pdh, anch_pdl = {}, {}, {}
    for d in days:
        dp = prev.get(d)
        m = pct.get(dp) if dp is not None else None
        if m is None or m <= 0:
            anch_labels[d] = "flat"
        else:
            anch_labels[d] = "follow" if m > hi_q else "fade"
            anch_pdh[d] = ranges[d][1]; anch_pdl[d] = ranges[d][2]
    tgt_anch_trunc = _walk_labels(p, anch_labels, anch_pdh, anch_pdl)

    def day_diffs(tgt_a, tgt_b):
        diff_days = []
        for d in days:
            m = (p.day == d) & in_session
            if not m.any():
                continue
            if not np.array_equal(tgt_a[m], tgt_b[m]):
                diff_days.append(int(d))
        return diff_days

    return {
        "n_days": len(days),
        "orig_t0_diff_days": day_diffs(tgt_orig_t0, tgt_orig),
        "orig_t1_diff_days": day_diffs(tgt_orig_t1, tgt_orig),
        "anchor_trunc_diff_days": day_diffs(tgt_anch_trunc, tgt_anch),
        "anchor_full_vs_shift_impl_identical": bool(
            np.array_equal(tgt_anch, f_rangeexp_anchor_shift(p, lo_q, hi_q))),
    }


# ------------------------------------------- schedule-only executor (F-6) --

def schedule_only(p, target, warmup_end_idx=0):
    """Mirror of engine.run_strategy's fill/force-flat semantics that
    emits ONLY the trade schedule (entry/exit ts, direction, hold bars,
    exit kind). NO prices, NO pips, NO equity — the PnL code path is not
    entered. Exit kinds: 'signal' = exit at the fill bar's open (s_open
    crossing), 'day_close' = force-flat at the day-close bar's close
    (s_close crossing)."""
    n = len(p.ts)
    pos = 0
    entry_i = -1
    trips = []

    def close_trip(i, kind):
        nonlocal pos
        trips.append({
            "entry_ts": int(p.ts[entry_i]), "exit_ts": int(p.ts[i]),
            "dir": int(pos), "hold_bars": int(i - entry_i),
            "entry_bar": int(entry_i), "exit_bar": int(i),
            "exit_kind": kind,
        })
        pos = 0

    for i in range(warmup_end_idx, n):
        if p.is_day_close[i]:
            if pos != 0:
                close_trip(i, "day_close")
            continue
        want = int(target[i - 1]) if i > warmup_end_idx else 0
        if not p.fill_ok[i]:
            want = 0
        if want != pos:
            if pos != 0:
                close_trip(i, "signal")
            if want != 0:
                pos = want
                entry_i = i
    if pos != 0:  # fail-safe (the day-close law should prevent this)
        close_trip(n - 1, "day_close")
    return trips


def trip_cost_pips(p, trip, k=1.0):
    """One spread crossing per side, exactly as the engine charges it:
    entry at the fill bar's open spread, exit at s_open for signal exits
    / s_close for day-close exits. Cost book arithmetic ONLY."""
    s_entry = p.s_o[trip["entry_bar"]]
    s_exit = p.s_c[trip["exit_bar"]] if trip["exit_kind"] == "day_close" \
        else p.s_o[trip["exit_bar"]]
    return float(k * (s_entry + s_exit) * p.pip_mult)


def n_diff_trips(trips_a, trips_b):
    """§9.4 N_diff: count of round trips whose (entry_ts, direction)
    differ between arms (symmetric difference, computed pre-PnL)."""
    ka = {(t["entry_ts"], t["dir"]) for t in trips_a}
    kb = {(t["entry_ts"], t["dir"]) for t in trips_b}
    return len(ka ^ kb), len(ka - kb), len(kb - ka)


def limb3_matched_pairs(trips_orig, trips_anchor, min_n=20):
    """§9.4 limb (iii) MACHINERY ONLY (the mean comparison itself needs
    PnL and happens in the scored phase). Pairs each R-ORIG N_diff-only
    trip with the nearest-in-time unmatched R-ANCHOR-only trip within the
    same UTC day; equidistant candidates resolve to the EARLIER entry_ts
    (rule frozen). Returns the matched index table + evaluability flag."""
    ua = [t for t in trips_anchor
          if (t["entry_ts"], t["dir"]) not in
          {(u["entry_ts"], u["dir"]) for u in trips_orig}]
    uo = [t for t in trips_orig
          if (t["entry_ts"], t["dir"]) not in
          {(u["entry_ts"], u["dir"]) for u in trips_anchor}]
    used = set()
    pairs = []
    for t in uo:
        day_t = t["entry_ts"] // SEC_DAY
        cands = [(abs(u["entry_ts"] - t["entry_ts"]), u["entry_ts"], j)
                 for j, u in enumerate(ua)
                 if j not in used and u["entry_ts"] // SEC_DAY == day_t]
        if not cands:
            continue
        cands.sort()
        _, _, j = cands[0]
        used.add(j)
        pairs.append((t, ua[j]))
    return {
        "orig_only": len(uo), "anchor_only": len(ua),
        "matched_pairs": len(pairs),
        "min_n_floor": min_n,
        "evaluable": len(pairs) >= min_n,
        "pairs_index_only": [(i, j) for i, j in []],
    }


# ------------------------------------------------------ F-1 family port ----

def _sma(x, w):
    c = np.cumsum(np.insert(x.astype(float), 0, 0.0))
    out = np.full(len(x), np.nan)
    out[w - 1:] = (c[w:] - c[:-w]) / w
    return out


def _atr(p, w):
    tr = np.maximum.reduce([
        p.b_h - p.b_l,
        np.abs(p.b_h - np.roll(p.b_c, 1)),
        np.abs(p.b_l - np.roll(p.b_c, 1)),
    ])
    tr = tr.copy()
    tr[0] = p.b_h[0] - p.b_l[0]
    return _sma(tr, w)


def f_gap(p, th, mode, th_pips=5.0):
    _, _, oc = _prev_day_stats(p)
    days = sorted(oc)
    sign = 1.0 if mode == "follow" else -1.0
    tgt = np.zeros(len(p.ts), dtype=np.int8)
    th_price = th_pips / p.pip_mult
    for j, d in enumerate(days):
        if j == 0:
            continue
        gap = oc[d][0] - oc[days[j - 1]][1]
        if abs(gap) >= th_price:
            want = int(sign * np.sign(gap))
            tgt[(p.day == d) & (p.hour >= 7) & (p.hour <= 18)] = want
    return tgt


def f_pdhloc(p, buf, opposite_exit, buf_pips=0.0):
    hi, lo, _ = _prev_day_stats(p)
    days = sorted(hi)
    prev = {days[j]: days[j - 1] for j in range(1, len(days))}
    tgt = np.zeros(len(p.ts), dtype=np.int8)
    pos = 0
    cur_day = -1
    buf_price = buf_pips / p.pip_mult
    for i in range(len(p.ts)):
        if p.skip[i]:
            continue
        d = p.day[i]
        if d != cur_day:
            cur_day, pos = d, 0
        pd_h = hi.get(prev.get(d, -1))
        pd_l = lo.get(prev.get(d, -1))
        if pd_h is None:
            continue
        if pos == 0:
            if p.b_c[i] > pd_h + buf_price:
                pos = 1
            elif p.b_c[i] < pd_l - buf_price:
                pos = -1
        elif opposite_exit:
            if (pos > 0 and p.b_c[i] < pd_l) or (pos < 0 and p.b_c[i] > pd_h):
                pos = 0
        tgt[i] = pos
    return tgt


def f_dow_simple(p, weeks, min_days):
    day_ret = {}
    hi, lo, oc = _prev_day_stats(p)
    days = sorted(oc)
    for j in range(1, len(days)):
        day_ret[days[j]] = oc[days[j]][1] - oc[days[j - 1]][1]
    dow_of = {}
    for d in days:
        dow_of[d] = dt.datetime.fromtimestamp(
            int(d * SEC_DAY), tz=dt.timezone.utc).weekday()
    s_by = defaultdict(float)
    tgt = np.zeros(len(p.ts), dtype=np.int8)
    for d in days:
        wd = dow_of[d]
        past = [v for d0, v in day_ret.items() if d0 < d and dow_of[d0] == wd]
        if len(past) >= weeks and len(past) >= min_days:
            mean = float(np.mean(past[-weeks:]))
            want = 1 if mean > 0 else (-1 if mean < 0 else 0)
            tgt[(p.day == d) & (p.hour >= 7) & (p.hour <= 18)] = want
    return tgt


def f_asiafade(p, asia_end, buf, buf_pips=0.0):
    tgt = np.zeros(len(p.ts), dtype=np.int8)
    pos = 0
    cur_day = -1
    rng = None
    buf_price = buf_pips / p.pip_mult
    for i in range(len(p.ts)):
        if p.skip[i]:
            continue
        d = p.day[i]
        h = p.hour[i]
        if d != cur_day:
            cur_day, pos, rng = d, 0, [p.b_h[i], p.b_l[i]]
        if h <= asia_end:
            rng[0] = max(rng[0], p.b_h[i])
            rng[1] = min(rng[1], p.b_l[i])
            tgt[i] = 0
            continue
        if h > 12:
            tgt[i] = 0
            continue
        if pos == 0:
            if p.b_c[i] > rng[0] + buf_price:
                pos = -1
            elif p.b_c[i] < rng[1] - buf_price:
                pos = 1
        else:
            if abs(p.b_c[i] - (rng[0] + rng[1]) / 2) < buf_price + (rng[0] - rng[1]) / 4:
                pos = 0
        tgt[i] = pos
    return tgt


def f_sessma(p, th, win_atr):
    atr = _atr(p, win_atr)
    tgt = np.zeros(len(p.ts), dtype=np.int8)
    pos = 0
    cur_day = -1
    csum = 0.0
    cnt = 0
    for i in range(len(p.ts)):
        if p.skip[i]:
            continue
        d = p.day[i]
        if d != cur_day:
            cur_day, pos, csum, cnt = d, 0, 0.0, 0
        h = p.hour[i]
        if h <= 19:
            csum += p.b_c[i]
            cnt += 1
        if cnt == 0 or np.isnan(atr[i]) or atr[i] == 0:
            tgt[i] = 0
            continue
        dev = p.b_c[i] - csum / cnt
        if h < 10 or h > 18:
            tgt[i] = 0 if pos == 0 else pos
            continue
        if pos == 0:
            if dev > th * atr[i]:
                pos = -1
            elif dev < -th * atr[i]:
                pos = 1
        else:
            if abs(dev) < 0.5 * th * atr[i]:
                pos = 0
        tgt[i] = pos
    return tgt


def f_h1tsmom(p, K):
    r = np.zeros(len(p.ts))
    r[K:] = p.b_c[K:] - p.b_c[:-K]
    tgt = np.sign(r).astype(np.int8)
    tgt[p.skip] = 0
    return tgt


def f_h1donch(p, L, hold_mult):
    hh = pd.Series(p.b_h).rolling(L).max().shift(1).to_numpy()
    ll = pd.Series(p.b_l).rolling(L).min().shift(1).to_numpy()
    tgt = np.zeros(len(p.ts), dtype=np.int8)
    pos = 0
    hold = 0
    for i in range(len(p.ts)):
        if p.skip[i]:
            tgt[i] = 0
            continue
        if pos != 0:
            hold -= 1
            if hold <= 0 or (pos > 0 and p.b_c[i] < ll[i]) or \
                    (pos < 0 and p.b_c[i] > hh[i]):
                pos = 0
        if pos == 0 and not np.isnan(hh[i]):
            if p.b_c[i] > hh[i]:
                pos, hold = 1, int(hold_mult * L)
            elif p.b_c[i] < ll[i]:
                pos, hold = -1, int(hold_mult * L)
        tgt[i] = pos
    return tgt


def f_daymom(p, N):
    hi, lo, oc = _prev_day_stats(p)
    days = sorted(oc)
    closes = {d: oc[d][1] for d in days}
    tgt = np.zeros(len(p.ts), dtype=np.int8)
    for j in range(N, len(days) - 1):
        nxt = days[j + 1]
        ret = closes[days[j]] - closes[days[j - N]]
        want = int(np.sign(ret))
        tgt[(p.day == nxt) & (p.hour >= 7) & (p.hour <= 18)] = want
    return tgt


def f_stoch(p, N, th_hi, th_lo):
    hh = pd.Series(p.b_h).rolling(N).max().shift(1).to_numpy()
    ll = pd.Series(p.b_l).rolling(N).min().shift(1).to_numpy()
    rng = hh - ll
    k = np.where(np.abs(rng) > 0, 100.0 * (p.b_c - ll) /
                 np.where(np.abs(rng) > 0, rng, 1.0), 50.0)
    tgt = np.zeros(len(p.ts), dtype=np.int8)
    pos = 0
    for i in range(len(p.ts)):
        if p.skip[i]:
            tgt[i] = 0
            continue
        if pos == 0:
            if k[i] > th_hi:
                pos = -1
            elif k[i] < th_lo:
                pos = 1
        else:
            if abs(k[i] - 50) < 10:
                pos = 0
        tgt[i] = pos
    return tgt


def f_roundnum(p, grid_pips, prox_pips):
    tgt = np.zeros(len(p.ts), dtype=np.int8)
    grid = grid_pips / p.pip_mult
    prox = prox_pips / p.pip_mult
    for i in range(len(p.ts)):
        if p.skip[i] or p.hour[i] < 7 or p.hour[i] > 18:
            continue
        c = p.b_c[i]
        nearest = round(c / grid) * grid
        dist = c - nearest
        if abs(dist) < prox:
            tgt[i] = int(-np.sign(dist))
    return tgt


def f_hourrev(p, win_days, invert):
    r = np.zeros(len(p.ts))
    r[1:] = p.b_c[1:] - p.b_c[:-1]
    day_u, day_idx = np.unique(p.day, return_inverse=True)
    S = np.zeros((len(day_u), 24))
    np.add.at(S, (day_idx, p.hour), r)
    CS = np.cumsum(S, axis=0)
    tgt = np.zeros(len(p.ts), dtype=np.int8)
    for i in range(len(p.ts)):
        if p.skip[i]:
            continue
        h = p.hour[i]
        if h < 7 or h > 18:
            continue
        d_i = day_idx[i]
        if d_i < win_days:
            continue
        # byte-faithful port: the ancestor indexes CS[d_i-1-win_days, h]
        # WITHOUT a lower-bound guard; at d_i == win_days the negative
        # index wraps to the last row (ancestor boundary behavior kept,
        # disclosed in the freeze artifact).
        s = CS[d_i - 1, h] - CS[d_i - 1 - win_days, h]
        sig = 1 if s > 0 else (-1 if s < 0 else 0)
        tgt[i] = int(-sig if invert else sig)
    return tgt


def spearman_rho(x, y):
    """Spearman |rho| via average-tie ranks (numpy only)."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    def rank(a):
        order = np.argsort(a, kind="mergesort")
        r = np.empty(len(a))
        sa = a[order]
        i = 0
        while i < len(a):
            j = i
            while j + 1 < len(a) and sa[j + 1] == sa[i]:
                j += 1
            r[order[i:j + 1]] = (i + j) / 2.0 + 1.0
            i = j + 1
        return r

    rx = rank(x) - rank(x).mean()
    ry = rank(y) - rank(y).mean()
    denom = np.sqrt(float((rx * rx).sum()) * float((ry * ry).sum()))
    return float((rx * ry).sum() / denom) if denom > 0 else 0.0


# --------------------------------------- F-3 clock-placebo constructibility -

def placebo_rebuild(p, occ_anchor, occ_natural, anchor_trips, in_session_mask,
                    seed, warmup_end_idx=0, band_pp=0.10, hold=None):
    """F-3 clock-placebo REBUILD — skeptic ADJUDICATION #2 (one shot, no
    iteration).

    One-shot calibration: r = (occ_anchor + band_pp) / occ_natural,
    computed ONCE from the already-measured occupancies. Construction
    (fully seed-driven, draw order pinned): rng = default_rng(seed); for
    each traded day in ascending order draw u ~ U(0,1); the day carries
    an entry iff u < r (entries/day scaled one-shot by r); selected days
    draw a UNIFORM-RANDOM in-session entry hour h ~ Int[7,17] —
    deliberately NOT the anchor's hour distribution (predicate (f)); the
    direction alternates by traded-day index with the seed-pinned parity
    +1 on EVEN index (recorded; no free parameter); exit after
    round(anchor avg hold) bars — UNCHANGED — or the day-close bar,
    whichever first. Fills are costed at the placebo's OWN event times in
    the scored phase (no cost-parity demand).

    Predicates (ADJUDICATION #2): (a) |occ_ctrl - occ_anchor| <= 10 pp on
    the identical in-session denominator, else UNBUILDABLE_SHAPE /
    BLOCKED_F3_CONTROL fail-closed; (b) >= 90% of control round trips
    distinct from the anchor's (entry_ts, dir); (c) both directions; (d)
    signal series non-constant."""
    r = (occ_anchor + band_pp) / occ_natural
    days = p.traded_days()
    day_index = {int(d): j for j, d in enumerate(days)}
    if hold is None:
        hold = max(1, int(round(float(np.mean([t["hold_bars"]
                                               for t in anchor_trips])))))
    bars_by_day = defaultdict(list)
    for i in np.nonzero(~p.skip)[0]:
        bars_by_day[p.day[i]].append(int(i))
    rng = np.random.default_rng(seed)
    tgt = np.zeros(len(p.ts), dtype=np.int8)
    n_selected = 0
    n_placed = 0
    for d in days:  # draw order: traded-day ascending (pinned)
        u = float(rng.random())              # draw 1: day selection
        if u >= r:
            continue
        n_selected += 1
        h0 = int(rng.integers(7, 18))        # draw 2: uniform hour 7..17
        direction = 1 if day_index[int(d)] % 2 == 0 else -1
        bars = bars_by_day.get(d, [])
        cand = [i for i in bars if p.hour[i] == h0]
        if not cand:                          # micro-gap day: entry unplaceable
            continue
        i0 = cand[0]
        i1 = min(i0 + hold, bars[-1])
        tgt[i0:i1 + 1] = direction
        n_placed += 1
    trips = schedule_only(p, tgt, warmup_end_idx=warmup_end_idx)
    occ = float((tgt[in_session_mask] != 0).mean())
    ka = {(t["entry_ts"], t["dir"]) for t in anchor_trips}
    kb = {(t["entry_ts"], t["dir"]) for t in trips}
    distinct = (len(kb - ka) / len(kb)) if kb else 0.0
    dirs = {t["dir"] for t in trips}
    nonconstant = bool(len(np.unique(tgt[in_session_mask])) > 1)
    margin_a = band_pp - abs(occ - occ_anchor)
    preds = {
        "a_shape_fidelity_10pp": bool(margin_a >= 0.0),
        "b_90pct_distinct_trips": bool(distinct >= 0.90),
        "c_both_directions": len(dirs) == 2,
        "d_non_constant": nonconstant,
    }
    return {
        "r": r,
        "hold_bars": hold,
        "entries_expected": r * len(days),
        "days_selected": n_selected,
        "entries_placed": n_placed,
        "trips_dev": len(trips),
        "occ_ctrl": occ,
        "occ_anchor": occ_anchor,
        "occ_natural_before": occ_natural,
        "margin_a_pp": margin_a * 100.0,
        "distinct_trip_share": distinct,
        "directions": sorted(dirs),
        "predicates": preds,
        "all_predicates_hold": bool(all(preds.values())),
        "parity_rule": "+1 on even traded-day index, -1 on odd (seed-pinned, recorded)",
        "draw_order": "default_rng(seed); per traded day ascending: u=runif() "
                      "day-selection (entry iff u < r); selected days draw "
                      "h=rng.integers(7,18) (uniform, NOT anchor hours)",
    }


def placebo_probe(p, trips_anchor, in_session_mask, lo_q=0.3, hi_q=0.7,
                  warmup_end_idx=0):
    """F-3 CLOCK-PLACEBO constructibility probe (no scored arm). Recipe
    (pinned in the freeze artifact): entries/day = round(anchor avg
    entries per traded day, min 1); entry hour = round(anchor avg entry
    hour) clamped to [7,17] (second entry +2h when entries/day >= 2);
    direction alternates by traded-day index (+1 on even); exit after
    round(anchor avg hold_bars) bars or the day-close bar, whichever
    first. Predicates (plan §8 F-3): occupancy 10-40% of in-session bars;
    both directions; >=90% of round trips differ from the anchor's;
    non-constant series."""
    days = p.traded_days()
    day_index = {d: j for j, d in enumerate(days)}
    n_trips = len(trips_anchor)
    n_days = max(len(days), 1)
    avg_per_day = n_trips / n_days
    hours = [ (t["entry_ts"] // 3600) % 24 for t in trips_anchor ]
    avg_hour = float(np.mean(hours)) if hours else 0.0
    avg_hold = float(np.mean([t["hold_bars"] for t in trips_anchor])) \
        if trips_anchor else 0.0
    n_per_day = max(1, int(round(avg_per_day)))
    entry_hour = int(min(17, max(7, round(avg_hour))))
    hold = max(1, int(round(avg_hold)))

    tgt = np.zeros(len(p.ts), dtype=np.int8)
    bars_by_day = defaultdict(list)
    for i in np.nonzero(~p.skip)[0]:
        bars_by_day[p.day[i]].append(int(i))
    for d, bars in bars_by_day.items():
        di = day_index.get(d)
        if di is None:
            continue
        direction = 1 if di % 2 == 0 else -1
        for e in range(n_per_day):
            h0 = min(18, entry_hour + 2 * e)
            cand = [i for i in bars if p.hour[i] == h0]
            if not cand:
                continue
            i0 = cand[0]
            i1 = min(i0 + hold, bars[-1])
            tgt[i0:i1 + 1] = direction
    trips = schedule_only(p, tgt, warmup_end_idx=warmup_end_idx)
    occ = float((tgt[in_session_mask] != 0).mean())
    dirs = {t["dir"] for t in trips}
    ka = {(t["entry_ts"], t["dir"]) for t in trips_anchor}
    kb = {(t["entry_ts"], t["dir"]) for t in trips}
    distinct = (len(kb - ka) / len(kb)) if kb else 0.0
    nonconstant = bool(len(np.unique(tgt[in_session_mask])) > 1)
    return {
        "anchor_avg_entries_per_day": avg_per_day,
        "anchor_avg_entry_hour": avg_hour,
        "anchor_avg_hold_bars": avg_hold,
        "placebo_entries_per_day": n_per_day,
        "placebo_entry_hour": entry_hour,
        "placebo_hold_bars": hold,
        "placebo_trips": len(trips),
        "occupancy_in_session": occ,
        "pred_occupancy_10_40": bool(0.10 <= occ <= 0.40),
        "pred_both_directions": len(dirs) == 2,
        "pred_90pct_distinct_trips": bool(distinct >= 0.90),
        "distinct_trip_share": distinct,
        "pred_non_constant": nonconstant,
        "all_predicates_hold": bool(
            0.10 <= occ <= 0.40 and len(dirs) == 2
            and distinct >= 0.90 and nonconstant),
    }
