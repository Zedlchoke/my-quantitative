#!/usr/bin/env python3
"""A7 PRELAUNCH G3: independent spot-recompute of the decisive novelty rho
FXFV6-A4-P1 anchor  vs  FXFV5-A6-P1 sham shadow.

Written fresh by the prelaunch auditor from the frozen RULE TEXTS
(d1/a4_postrelease/proposal_P1.json; research/assets/forex_free_v5/family_a6p1.py
docstring law) and the two clocks files.  Not an import or re-run of the D2
lane's compute_ancestry_rhos.py -- schedule construction, data loading and
Spearman ranking are implemented independently here.  Conventions (exposure
cell f..x-1, pooled signed variants, S0 span) are the frozen D2 method as
recorded in d2_a7_novelty_verdict.json method section.

Schedule fidelity only.  No PnL, no costs, no scored output.
"""
import glob
import json
import math
import os
from bisect import bisect_left, bisect_right
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
NY = ZoneInfo("America/New_York")
UTC = timezone.utc

PAIRS = ["GBPUSD", "USDCAD", "AUDUSD", "NZDUSD"]
ECON_PAIR = {"GB": "GBPUSD", "CA": "USDCAD", "AU": "AUDUSD", "NZ": "NZDUSD"}
S0_START = date(2018, 4, 4)
S0_END = date(2025, 7, 24)
CAP = datetime(2025, 7, 25, tzinfo=UTC)          # V5 family S0 cap instant


def ny_close(d):
    """The 16:00 America/New_York instant of NY date d, in UTC."""
    return datetime(d.year, d.month, d.day, 16, 0, tzinfo=NY).astimezone(UTC)


def stamp(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(UTC)


# ---------------------------------------------------------------- data ----
# Independent loader: walk every H1 snapshot row, keep weekday 16:00-NY bars,
# key by NY date; the decision close of d is the bar stamped exactly ny_close(d).
def decision_closes(pair):
    by_date = {}
    for path in sorted(glob.glob(os.path.join(ROOT, f"data_raw/forex_free_v1/{pair}_1h_*_a.json"))):
        blob = json.load(open(path))
        if blob.get("status") != "ok":
            continue
        for row in blob["values"]:
            t = datetime.strptime(row["datetime"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
            loc = t.astimezone(NY)
            if loc.hour == 16 and loc.minute == 0 and loc.weekday() < 5:
                prev = by_date.get(loc.date())
                if prev is not None and prev[1] != float(row["close"]):
                    raise SystemExit(f"conflict {pair} {loc.date()}")
                by_date[loc.date()] = (t, float(row["close"]))
    return {d: v[1] for d, v in by_date.items() if ny_close(d) == v[0]}


CLOSES, DAYS = {}, {}
for p in PAIRS:
    CLOSES[p] = decision_closes(p)
    DAYS[p] = sorted(CLOSES[p])


def rets(p):
    out = {}
    ds = DAYS[p]
    for a, b in zip(ds, ds[1:]):
        out[b] = math.log(CLOSES[p][b] / CLOSES[p][a])
    return out


RET = {p: rets(p) for p in PAIRS}


# ------------------------------------------------------- A4-P1 schedule ----
def a4p1_cells(sham=False):
    """proposal_P1.json law: per own-economy clock, D0 = conditionable date
    (CA at published available_for_daily_decision_date, GB/AU/NZ at
    decision_date); sham shifts D0 +7 calendar days.  R = ln(C0/Cprev),
    side = sign(R) (R==0 skip); fill close(D1); hold k=5; exit close(D1+5);
    cells D1..D1+4.  One open position per pair; exit must lie at/below the
    S0 end close."""
    v6 = json.load(open(os.path.join(ROOT, "research/control/forex_free_v6_run/p3_conditioning_clocks_v6.json")))["clocks"]
    events = []
    for r in v6:
        d0 = date.fromisoformat(r["available_for_daily_decision_date"]) \
            if (r["economy"] == "CA" and r.get("available_for_daily_decision_date")) \
            else date.fromisoformat(r["decision_date"])
        if sham:
            d0 = d0 + timedelta(days=7)
        events.append((d0, ECON_PAIR[r["economy"]]))
    events.sort()
    cells, trades, free_at = set(), 0, {}
    for d0, p in events:
        ds = DAYS[p]
        i0 = bisect_left(ds, d0)
        if i0 >= len(ds) or ds[i0] != d0:
            continue                                    # no decision close that day
        if i0 < 6:
            continue                                    # warmup: 5 closes end at D_prev
        i_prev, i1 = i0 - 1, i0 + 1
        if i1 + 5 >= len(ds):
            continue                                    # exit beyond series
        R = math.log(CLOSES[p][ds[i0]] / CLOSES[p][ds[i_prev]])
        if R == 0.0:
            continue
        ent, exi = ny_close(ds[i1]), ny_close(ds[i1 + 5])
        if exi > ny_close(S0_END):
            continue                                    # S0 exit boundary
        if p in free_at and ent < free_at[p]:
            continue                                    # one-position governor
        free_at[p] = exi
        for j in range(i1, i1 + 5):
            cells.add((ds[j], p, 1 if R > 0 else -1))
        trades += 1
    return cells, trades


# ------------------------------------------------- V5 sham shadow law -----
def v5_sham_cells():
    """family_a6p1.py sham law: a' = a+7d; F = last bar close strictly before
    a'; D = session before F; X = first bar close strictly after a';
    side = -sign(sum of the 10 log returns strictly before D); warmup 11
    closes; F and X within the S0 cap; window dropped iff ANY evidenced V5
    clock instant lies strictly inside (F, X); fill lag F-D <= 4 days;
    governor entry >= open exit; cells F..X-1."""
    v5 = json.load(open(os.path.join(ROOT, "research/control/forex_free_v5_run/p3_conditioning_clocks_v5.json")))["clocks"]
    clocks = [{"e": r["economy"], "a": stamp(r["available_time_utc"])} for r in v5]
    clocks.sort(key=lambda c: c["a"])
    all_inst = sorted(c["a"] for c in clocks)
    cells, trades, free_at, used_day = set(), 0, {}, {}
    for c in clocks:
        p = ECON_PAIR[c["e"]]
        a = c["a"] + timedelta(days=7)
        ds = DAYS[p]
        # last index with close strictly before a (same-day close counts when
        # the stamp is after 16:00-NY, e.g. GB 23:59:59Z end-of-day bounds)
        hi = bisect_right(ds, a.date())
        cand = [d for d in ds[:hi] if ny_close(d) < a]
        if not cand:
            continue
        i_f = len(cand) - 1
        i_d = i_f - 1
        if i_d < 0:
            continue
        # first index with close strictly after a
        lo = [d for d in ds if ny_close(d) > a]
        if not lo:
            continue
        i_x = ds.index(lo[0])
        if i_d < 11:
            continue                                    # 11-close warmup void
        if ny_close(ds[i_f]) >= CAP or ny_close(ds[i_x]) > CAP:
            continue
        cs = [CLOSES[p][ds[j]] for j in range(i_d - 11, i_d)]
        s = sum(math.log(cs[k] / cs[k - 1]) for k in range(1, 11))
        if s == 0.0:
            continue
        side = -1 if s > 0 else 1
        f_ts, x_ts = ny_close(ds[i_f]), ny_close(ds[i_x])
        if any(f_ts < t < x_ts for t in all_inst):
            continue                                    # sham window contains a real clock
        if f_ts - ny_close(ds[i_d]) > timedelta(days=4):
            continue                                    # MAX_FILL_LAG_DAYS
        if p in free_at and f_ts < free_at[p]:
            continue
        if used_day.get(p) == ds[i_f]:
            continue
        free_at[p], used_day[p] = x_ts, ds[i_f]
        for j in range(i_f, i_x):
            cells.add((ds[j], p, side))
        trades += 1
    return cells, trades


# ------------------------------------------------------------ Spearman ----
def ranks(v):
    order = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(v):
        j = i
        while j + 1 < len(v) and v[order[j + 1]] == v[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return r


def spearman(x, y):
    if len(x) < 3:
        return None
    rx, ry = ranks(x), ranks(y)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return None if den == 0 else num / den


def main():
    a_cells, a_trades = a4p1_cells(sham=False)
    b_cells, b_trades = v5_sham_cells()
    print(f"A4P1 anchor: trades={a_trades} cells={len(a_cells)}")
    print(f"V5 sham   : trades={b_trades} cells={len(b_cells)}")

    inter = {(d, p) for d, p, _ in a_cells} & {(d, p) for d, p, _ in b_cells}
    print(f"intersection={len(inter)} containment_b_in_a={len(inter)/max(1,len(b_cells)):.4f}")
    same = sum(1 for k in inter
               if next(v for d, p, v in a_cells if (d, p) == k)
               == next(v for d, p, v in b_cells if (d, p) == k))
    print(f"sign agreement same={same} rate={same/max(1,len(inter)):.4f}")

    # variant 1: cellwise signed, full per-pair S0 grid over shared pairs
    xs, ys = [], []
    for p in PAIRS:
        for d in DAYS[p]:
            if S0_START <= d <= S0_END:
                va = next((v for dd, pp, v in a_cells if dd == d and pp == p), 0)
                vb = next((v for dd, pp, v in b_cells if dd == d and pp == p), 0)
                xs.append(float(va)); ys.append(float(vb))
    v1 = spearman(xs, ys)
    print(f"cellwise_signed_full_grid n={len(xs)} rho={v1:.4f}")

    # variant 2: cellwise on union of active keys
    keys = sorted({(d, p) for d, p, _ in a_cells} | {(d, p) for d, p, _ in b_cells})
    xa = [float(next((v for dd, pp, v in a_cells if (dd, pp) == k), 0)) for k in keys]
    yb = [float(next((v for dd, pp, v in b_cells if (dd, pp) == k), 0)) for k in keys]
    v2 = spearman(xa, yb)
    print(f"cellwise_union_active n={len(keys)} rho={v2:.4f}")

    # variant 3: per-date net signed sum over shared pairs, union date grid
    amap, bmap = {}, {}
    for d, p, v in a_cells:
        amap.setdefault(d, {})[p] = v
    for d, p, v in b_cells:
        bmap.setdefault(d, {})[p] = v
    dates = sorted(set(amap) | set(bmap))
    na = [float(sum(amap.get(d, {}).values())) for d in dates]
    nb = [float(sum(bmap.get(d, {}).values())) for d in dates]
    v3 = spearman(na, nb)
    print(f"netsigned_union_dates_shared_pairs n={len(dates)} rho={v3:.4f}")

    pooled = max(abs(v1), abs(v2), abs(v3))
    rec = {"recomputed_by": "A7 prelaunch g3_rho_recompute.py (independent implementation)",
           "a4p1_trades": a_trades, "a4p1_cells": len(a_cells),
           "v5_sham_trades": b_trades, "v5_sham_cells": len(b_cells),
           "intersection": len(inter),
           "containment_b_in_a": round(len(inter) / max(1, len(b_cells)), 4),
           "sign_agreement_rate": round(same / max(1, len(inter)), 4),
           "rho_cellwise_signed_full_grid": round(v1, 4),
           "rho_cellwise_union_active": round(v2, 4),
           "rho_netsigned_union_dates": round(v3, 4),
           "pooled_max_abs_rho": round(pooled, 4),
           "recorded_max_abs_pooled_rho": 0.1235,
           "recorded_netsigned_rho": -0.1235,
           "abs_delta_vs_recorded": round(abs(pooled - 0.1235), 4),
           "within_tolerance_0.005": abs(pooled - 0.1235) <= 0.005,
           "under_bar_0.20": pooled <= 0.20}
    print(json.dumps(rec, indent=1))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "g3_rho_recompute_result.json")
    json.dump(rec, open(out, "w"), indent=1)
    print("wrote", out)


if __name__ == "__main__":
    main()
