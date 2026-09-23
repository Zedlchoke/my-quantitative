"""EURUSD-OPEN-SEARCH-V2 library: H1 plane masks + 12 new families.

Plane semantics (plan §2/§4, frozen before outcomes):
  - bars: valid H1 bars aggregated from the 15m plane (4x15m exact)
  - trading day = UTC day; tradable hours 00..19 only (hours >=20 exist in
    data but are NOT traded: no fills, no actions, positions can never be
    open there because the day-close bar is the 19:00 bar -> close at 20:00,
    one full hour before the 21:00 rollover)
  - fills at next-bar open, opposite side, stress multiplier k (engine v1)
  - all family signals use trailing data only (PIT)
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine as E


class H1Plane(E.Plane):
    """Plane with V2 trading masks on top of engine.Plane."""

    def __init__(self, df):
        df = df.copy()
        df["s_open"] = df["a_o"] - df["b_o"]
        df["s_close"] = df["a_c"] - df["b_c"]
        super().__init__(df)
        self.hour = (self.ts // 3600 % 24).astype(np.int32)
        self.day = (self.ts // E.SEC_DAY).astype(np.int64)
        tradable = self.hour <= 19
        self.skip = ~tradable
        # day-close bar: last tradable bar of each day (19:00 normally)
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
            self.last_tradable_of_day[self.last_tradable_of_day[m]] == np.arange(len(self.ts))[m]
        )
        self.fill_ok = tradable & (self.hour <= 18)
        self.fill_ok[0] = False

    def day_open_close(self):
        """Per-day first open and last close (traded hours only)."""
        out = {}
        for i in range(len(self.ts)):
            if self.skip[i]:
                continue
            d = self.day[i]
            if d not in out:
                out[d] = [self.b_o[i], self.b_c[i], i]
            else:
                out[d][1] = self.b_c[i]
        return out


# ---------------- families: target arrays over the H1 plane ----------------

def _prev_day_stats(p):
    """Per-day (high, low, open, close) over traded hours, PIT helper."""
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


def f_gap(p, th, mode):
    _, _, oc = _prev_day_stats(p)
    days = sorted(oc)
    sign = 1.0 if mode == "follow" else -1.0
    tgt = np.zeros(len(p.ts), dtype=np.int8)
    for j, d in enumerate(days):
        if j == 0:
            continue
        gap = oc[d][0] - oc[days[j - 1]][1]
        if abs(gap) >= th / E.PIP:
            want = int(sign * np.sign(gap))
            tgt[(p.day == d) & (p.hour >= 7) & (p.hour <= 18)] = want
    return tgt


def f_pdhloc(p, buf, opposite_exit):
    """Break of prior-day high/low (with buffer); optional opposite-extreme exit."""
    hi, lo, _ = _prev_day_stats(p)
    days = sorted(hi)
    prev = {days[j]: days[j - 1] for j in range(1, len(days))}
    tgt = np.zeros(len(p.ts), dtype=np.int8)
    pos = 0
    cur_day = -1
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
            if p.b_c[i] > pd_h + buf:
                pos = 1
            elif p.b_c[i] < pd_l - buf:
                pos = -1
        elif opposite_exit:
            if (pos > 0 and p.b_c[i] < pd_l) or (pos < 0 and p.b_c[i] > pd_h):
                pos = 0
        tgt[i] = pos
    return tgt


def f_dow_simple(p, weeks, min_days):
    """Trailing `weeks` mean day-return per weekday -> intraday follow."""
    import datetime as dt

    day_ret = {}
    hi, lo, oc = _prev_day_stats(p)
    days = sorted(oc)
    for j in range(1, len(days)):
        day_ret[days[j]] = oc[days[j]][1] - oc[days[j - 1]][1]
    dow_of = {}
    for d in days:
        dow_of[d] = dt.datetime.utcfromtimestamp(int(d * E.SEC_DAY)).weekday()
    from collections import defaultdict

    s_by = defaultdict(float); c_by = defaultdict(int)
    tgt = np.zeros(len(p.ts), dtype=np.int8)
    for d in days:
        wd = dow_of[d]
        past = [v for d0, v in day_ret.items() if d0 < d and dow_of[d0] == wd]
        if len(past) >= weeks and len(past) >= min_days:
            mean = float(np.mean(past[-weeks:]))
            want = 1 if mean > 0 else (-1 if mean < 0 else 0)
            tgt[(p.day == d) & (p.hour >= 7) & (p.hour <= 18)] = want
    return tgt


def f_asiafade(p, asia_end, buf):
    tgt = np.zeros(len(p.ts), dtype=np.int8)
    pos = 0
    cur_day = -1
    rng = None
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
            if p.b_c[i] > rng[0] + buf:
                pos = -1
            elif p.b_c[i] < rng[1] - buf:
                pos = 1
        else:
            if abs(p.b_c[i] - (rng[0] + rng[1]) / 2) < buf + (rng[0] - rng[1]) / 4:
                pos = 0
        tgt[i] = pos
    return tgt


def f_sessma(p, th, win_atr):
    atr = E._atr(p, win_atr)
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
    hi, lo = E._roll_hi_lo(p, L)
    tgt = np.zeros(len(p.ts), dtype=np.int8)
    pos = 0
    hold = 0
    for i in range(len(p.ts)):
        if p.skip[i]:
            tgt[i] = 0
            continue
        if pos != 0:
            hold -= 1
            if hold <= 0 or (pos > 0 and p.b_c[i] < lo[i]) or (pos < 0 and p.b_c[i] > hi[i]):
                pos = 0
        if pos == 0 and not np.isnan(hi[i]):
            if p.b_c[i] > hi[i]:
                pos, hold = 1, int(hold_mult * L)
            elif p.b_c[i] < lo[i]:
                pos, hold = -1, int(hold_mult * L)
        tgt[i] = pos
    return tgt


def f_daymom(p, N):
    hi, lo, oc = _prev_day_stats(p)
    days = sorted(oc)
    closes = {d: oc[d][1] for d in days}
    tgt = np.zeros(len(p.ts), dtype=np.int8)
    for j in range(N, len(days)):
        d = days[j]
        ret = closes[d] - closes[days[j - N]]
        want = int(np.sign(ret))
        tgt[(p.day == d) & (p.hour >= 7) & (p.hour <= 18)] = want
    return tgt


def f_rangeexp(p, lo_q, hi_q, use_breakout):
    hi, lo, oc = _prev_day_stats(p)
    days = sorted(oc)
    ranges = {}
    for j in range(1, len(days)):
        d = days[j]
        ranges[d] = (hi[d] - lo[d], hi[days[j - 1]], lo[days[j - 1]])
    hist = []
    pct = {}
    for d in days:
        pct[d] = (
            float(np.mean([1.0 for x in hist])) if not hist else float(np.searchsorted(sorted(hist), ranges[d][0]) / len(hist))
        )
        hist.append(ranges[d][0])
        if len(hist) > 60:
            hist.pop(0)
    tgt = np.zeros(len(p.ts), dtype=np.int8)
    pos = 0
    cur_day = -1
    pd_h = pd_l = None
    expand = None
    for i in range(len(p.ts)):
        if p.skip[i]:
            continue
        d = p.day[i]
        if d != cur_day:
            cur_day, pos = d, 0
            if d in pct and pct[d] > 0:
                narrow = pct[d] < lo_q
                wide = pct[d] > hi_q
                expand = narrow if use_breakout else (wide if not narrow else False)
                expand = narrow if use_breakout else wide
                pd_h = ranges[d][1] if d in ranges else None
                pd_l = ranges[d][2] if d in ranges else None
            else:
                expand = None
        if expand is None or pd_h is None or p.hour[i] < 7 or p.hour[i] > 18:
            tgt[i] = 0
            continue
        if expand:  # narrow yesterday -> breakout today
            if pos == 0:
                if p.b_c[i] > pd_h:
                    pos = 1
                elif p.b_c[i] < pd_l:
                    pos = -1
        else:  # wide yesterday -> fade today
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


def f_stoch(p, N, th_hi, th_lo):
    hh = pd.Series(p.b_h).rolling(N).max().shift(1).to_numpy()
    ll = pd.Series(p.b_l).rolling(N).min().shift(1).to_numpy()
    rng = hh - ll
    k = np.where(np.abs(rng) > 0, 100.0 * (p.b_c - ll) / np.where(np.abs(rng) > 0, rng, 1.0), 50.0)
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


def f_roundnum(p, grid, prox):
    tgt = np.zeros(len(p.ts), dtype=np.int8)
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
    import datetime as dt

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
        s = CS[d_i - 1, h] - CS[d_i - 1 - win_days, h]
        sig = 1 if s > 0 else (-1 if s < 0 else 0)
        tgt[i] = int(-sig if invert else sig)
    return tgt
