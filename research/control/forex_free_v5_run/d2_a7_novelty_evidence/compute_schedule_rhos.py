#!/usr/bin/env python3
"""A7-N D2 audit: decision-schedule construction + Spearman rho vs forbidden ancestry.

DECISION-SERIES COMPUTATION ONLY: schedule construction and rank correlations of
signed/unscaled decision indicators. NO PnL, NO costs, NO scored output, NO fills
beyond schedule instants. Frozen DST 16:00 America/New_York bar convention.
"""
import datetime, json, glob, math, hashlib
from collections import defaultdict
from zoneinfo import ZoneInfo
import numpy as np

NY = ZoneInfo("America/New_York")
UTC = datetime.timezone.utc
ROOT = "/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v5/d2-a7-novelty"

PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD"]
# pair notation used across packets -> canonical slash form
SLASH = {"EURUSD": "EUR/USD", "GBPUSD": "GBP/USD", "USDJPY": "USD/JPY", "USDCHF": "USD/CHF",
         "USDCAD": "USD/CAD", "AUDUSD": "AUD/USD", "NZDUSD": "NZD/USD"}
ECON_PAIR = {"GB": "GBP/USD", "CA": "USD/CAD", "AU": "AUD/USD", "NZ": "NZD/USD",
             "US": None, "EMU": "EUR/USD", "JP": "USD/JPY", "CH": "USD/CHF"}
# non-USD leg currency is BASE or QUOTE in pair notation
LEG_SIDE = {"GBP/USD": "BASE", "AUD/USD": "BASE", "NZD/USD": "BASE", "EUR/USD": "BASE",
            "USD/JPY": "QUOTE", "USD/CHF": "QUOTE", "USD/CAD": "QUOTE"}
S0_START = datetime.date(2018, 4, 4)
S0_END = datetime.date(2025, 7, 24)  # entries with instant >= 2025-07-25 excluded



NOSLASH = {v: k for k, v in SLASH.items()}


def ns(pair):
    return NOSLASH[pair]


def ny1600(d: datetime.date) -> datetime.datetime:
    """UTC instant of 16:00 America/New_York wall time on date d (DST-aware)."""
    return datetime.datetime(d.year, d.month, d.day, 16, 0, tzinfo=NY).astimezone(UTC)


def load_daily_closes(pair):
    """Daily 16:00-NY completed closes {date: close} from H1 snapshots."""
    inst = defaultdict(dict)
    for f in sorted(glob.glob(f"{ROOT}/data_raw/forex_free_v1/{pair}_1h_*_a.json")):
        d = json.load(open(f))
        if d.get("status") != "ok":
            continue
        for v in d["values"]:
            ts = datetime.datetime.strptime(v["datetime"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
            inst[ts.date()][ts] = float(v["close"])
    out = {}
    for d, m in inst.items():
        want = ny1600(d)
        if want in m:
            out[d] = m[want]
    return out


DAILY = {p: load_daily_closes(p) for p in PAIRS}
DATES = sorted(set().union(*[set(DAILY[p].keys()) for p in PAIRS]))
ALL_DAYS = [d for d in DATES if d.weekday() < 5]  # NY trading days present in snapshot


def series_dates(pair):
    return sorted(DAILY[pair].keys())


def first_bar_strictly_after(pair, inst):
    ds = series_dates(pair)
    for d in ds:
        if ny1600(d) > inst:
            return d
    return None


def last_bar_strictly_before(pair, inst):
    ds = series_dates(pair)
    prev = None
    for d in ds:
        if ny1600(d) < inst:
            prev = d
        else:
            break
    return prev


def parse_stamp(s):
    return datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(UTC)


def spearman(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    assert len(x) == len(y) and len(x) > 2
    rx = _avg_ranks(x); ry = _avg_ranks(y)
    if rx.std() == 0 or ry.std() == 0:
        return None
    return float(np.corrcoef(rx, ry)[0, 1])


def _avg_ranks(v):
    order = np.argsort(v, kind="mergesort")
    ranks = np.empty(len(v))
    sv = v[order]
    i = 0
    while i < len(v):
        j = i
        while j + 1 < len(v) and sv[j + 1] == sv[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return ranks


def logret(pair, i, closes, dates_idx):
    a, b = closes[i - 1], closes[i]
    return math.log(b / a)


# ---------------------------------------------------------------- schedules
def sched_a4p1():
    """FXFV5-A4-P1: availability-exact print-window reaction sign; hold H=5."""
    clocks = json.load(open(f"{ROOT}/research/control/forex_free_v5_run/p3_conditioning_clocks_v5.json"))["clocks"]
    recs = []  # (decision_date, pair, dir)
    detail = []
    for c in clocks:
        e = c["economy"]; pair = ns(ECON_PAIR[e])
        a = parse_stamp(c["available_time_utc"])
        dd = datetime.date.fromisoformat(c["decision_date"])
        if not (S0_START <= dd <= S0_END):
            continue
        d1 = first_bar_strictly_after(pair, a)
        if d1 is None:
            continue
        closes = DAILY[pair]; dates = series_dates(pair)
        i1 = dates.index(d1)
        if i1 < 1:
            continue
        R = closes[dates[i1]] / closes[dates[i1 - 1]] - 1.0
        direction = 0 if R == 0 else (1 if R > 0 else -1)
        recs.append((d1, SLASH[pair], direction))
        detail.append({"economy": e, "print": c["decision_date"], "available": c["available_time_utc"],
                       "decision_bar": str(d1), "R": R, "dir": direction})
    return recs, detail


def sched_a4p2():
    """FXFV5-A4-P2: two consecutive same-sign print reactions; hold Q=15."""
    clocks = json.load(open(f"{ROOT}/research/control/forex_free_v5_run/p3_conditioning_clocks_v5.json"))["clocks"]
    by_econ = defaultdict(list)
    for c in clocks:
        e = c["economy"]; pair = ns(ECON_PAIR[e])
        a = parse_stamp(c["available_time_utc"])
        dd = datetime.date.fromisoformat(c["decision_date"])
        if not (S0_START <= dd <= S0_END):
            continue
        d1 = first_bar_strictly_after(pair, a)
        if d1 is None:
            continue
        closes = DAILY[pair]; dates = series_dates(pair)
        i1 = dates.index(d1)
        if i1 < 1:
            continue
        R = closes[dates[i1]] / closes[dates[i1 - 1]] - 1.0
        by_econ[e].append((d1, R))
    recs = []
    for e, seq in by_econ.items():
        seq.sort()
        pair = ECON_PAIR[e]
        for k in range(1, len(seq)):
            r0, r1 = seq[k - 1][1], seq[k][1]
            s0 = 0 if r0 == 0 else (1 if r0 > 0 else -1)
            s1 = 0 if r1 == 0 else (1 if r1 > 0 else -1)
            if s0 != 0 and s0 == s1:
                recs.append((seq[k][0], pair, s1))
    return sorted(recs)


def sched_a6p1():
    """FXFV5-A6-P1: pre-release counter-trend window [F,X]; dir=-sign(10-day sum at D)."""
    clocks = json.load(open(f"{ROOT}/research/control/forex_free_v5_run/p3_conditioning_clocks_v5.json"))["clocks"]
    recs = []
    detail = []
    for c in clocks:
        e = c["economy"]; pair = ns(ECON_PAIR[e])
        a = parse_stamp(c["available_time_utc"])
        dd = datetime.date.fromisoformat(c["decision_date"])
        if not (S0_START <= dd <= S0_END):
            continue
        closes = DAILY[pair]; dates = series_dates(pair)
        f = last_bar_strictly_before(pair, a)
        if f is None:
            continue
        i_f = dates.index(f)
        if i_f < 1:
            continue
        d_dec = dates[i_f - 1]          # D = previous session bar strictly before F
        i_d = i_f - 1
        x_bar = first_bar_strictly_after(pair, a)  # X
        if x_bar is None:
            continue
        if i_d < 11:
            continue
        s = sum(math.log(closes[dates[i]] / closes[dates[i - 1]]) for i in range(i_d - 10, i_d + 1))
        direction = 0 if s == 0 else (-1 if s > 0 else 1)
        recs.append((d_dec, SLASH[pair], direction))
        detail.append({"economy": e, "decision_D": str(d_dec), "F": str(f), "X": str(x_bar), "dir": direction})
    return sorted(recs), detail


def daily_log_returns(pair):
    dates = series_dates(pair)
    closes = DAILY[pair]
    r = {}
    for i in range(1, len(dates)):
        r[dates[i]] = math.log(closes[dates[i]] / closes[dates[i - 1]])
    return r


RET = {p: daily_log_returns(p) for p in PAIRS}


def sched_a6p2(ddof=0):
    """FXFV5-A6-P2: |z|>=2.0 EUR/USD trigger, six-leg map, hold 1."""
    r = RET["EURUSD"]
    days = [d for d in sorted(r.keys()) if S0_START <= d <= S0_END]
    vals = [r[d] for d in days]
    recs = []
    trig = []
    W = 120
    for i in range(W, len(days)):
        t = days[i]
        window = vals[i - W:i]  # trailing 120 strictly before t
        mu = float(np.mean(window)); sd = float(np.std(window, ddof=ddof))
        if sd == 0:
            continue
        z = (vals[i] - mu) / sd
        if abs(z) >= 2.0:
            up = z > 0
            # dirs per pair: EUR-up -> long GBP,AUD,NZD; short JPY,CHF,CAD
            m = {"GBP/USD": 1, "AUD/USD": 1, "NZD/USD": 1, "USD/JPY": -1, "USD/CHF": -1, "USD/CAD": -1}
            if not up:
                m = {k: -v for k, v in m.items()}
            for pair, d in m.items():
                recs.append((t, pair, d))
            trig.append((t, z, 1 if up else -1))
    return recs, trig


def sched_f1(ddof=0, estimator="mean"):
    """FXFV4-A6-P1 anchor (mean) / neighbour (median): commodity-bloc risk-off z<=-1."""
    days_all = sorted(set.intersection(*[set(RET[p].keys()) for p in ["AUDUSD", "NZDUSD", "USDCAD"]]))
    days = [d for d in days_all if S0_START <= d <= S0_END]
    svals = {}
    for d in days:
        s = 0.5 * (RET["AUDUSD"][d] + RET["NZDUSD"][d] - RET["USDCAD"][d])
        svals[d] = s
    recs = []; trig = []
    W = 60
    ds = sorted(svals.keys())
    v = [svals[d] for d in ds]
    for i in range(W, len(ds)):
        t = ds[i]
        window = v[i - W:i]
        mu = float(np.mean(window)); sd = float(np.std(window, ddof=ddof))
        if sd == 0:
            continue
        z = (v[i] - mu) / sd
        if z <= -1.0:
            m = {"AUD/USD": -1, "NZD/USD": -1, "USD/CAD": 1, "USD/JPY": -1, "USD/CHF": -1}
            for pair, d in m.items():
                recs.append((t, pair, d))
            trig.append((t, z))
    return recs, trig


def sched_f1_median(ddof=0):
    days_all = sorted(set.intersection(*[set(RET[p].keys()) for p in ["AUDUSD", "NZDUSD", "USDCAD"]]))
    days = [d for d in days_all if S0_START <= d <= S0_END]
    trips = []
    for d in days:
        t3 = (RET["AUDUSD"][d], RET["NZDUSD"][d], -RET["USDCAD"][d])
        trips.append((d, t3))
    recs = []; trig = []
    W = 60
    for i in range(W, len(trips)):
        t, _ = trips[i][0], None
        window = [trips[j][1] for j in range(i - W, i)]
        est = [float(np.median(w)) for w in window]
        mu = float(np.mean(est)); sd = float(np.std(est, ddof=ddof))
        cur = float(np.median(trips[i][1]))
        if sd == 0:
            continue
        z = (cur - mu) / sd
        if z <= -1.0:
            m = {"AUD/USD": -1, "NZD/USD": -1, "USD/CAD": 1, "USD/JPY": -1, "USD/CHF": -1}
            for pair, d in m.items():
                recs.append((t, pair, d))
            trig.append((t, z))
    return recs, trig


def sched_f2_style():
    """Reconstructed V4-family2-style schedule: evidenced RATE_CHANGE rows of the
    pinned V5 extension ledger; decision T = first_readable_decision_utc (the first
    16:00-NY bar at/after operative availability); direction per the frozen map."""
    rows = [json.loads(l) for l in open(f"{ROOT}/research/control/forex_free_v5_run/announcement_ledger_v5_extension.jsonl")]
    rows = [r for r in rows if r.get("row_type") == "RATE_CHANGE"
            and r["announcement"].get("status") == "EVIDENCED"]
    rows.sort(key=lambda r: r["announcement"]["operative_available_time_utc"])
    recs = []; used = set(); skipped = 0
    detail = []
    for r in rows:
        a = parse_stamp(r["announcement"]["operative_available_time_utc"])
        t = parse_stamp(r["first_readable_decision_utc"])
        d = t.date()
        if not (S0_START <= d <= S0_END):
            continue
        area = r["area"]; delta = float(r["new_value"]) - float(r["old_value"])
        if delta == 0:
            continue
        legs = []
        if area == "US":
            m = {"EUR/USD": -1, "GBP/USD": -1, "AUD/USD": -1, "NZD/USD": -1,
                 "USD/JPY": 1, "USD/CHF": 1, "USD/CAD": 1}
            if delta < 0:
                m = {k: -v for k, v in m.items()}
            legs = list(m.items())
        else:
            pair = ECON_PAIR[area]
            base = 1 if LEG_SIDE[pair] == "BASE" else -1
            sgn = base if delta > 0 else -base
            legs = [(pair, sgn)]
        for pair, s in legs:
            key = (d, pair)
            if key in used:
                skipped += 1
                continue  # earlier availability wins
            used.add(key)
            recs.append((d, pair, s))
        detail.append({"id": r["decision_id"], "area": area, "delta": delta,
                       "T_date": str(d), "available": r["announcement"]["operative_available_time_utc"]})
    return sorted(recs), detail, skipped


# ------------------------------------------------------- correlation helpers
def to_maps(recs):
    m = defaultdict(dict)
    for d, pair, s in recs:
        m[d][pair] = s
    return m


def net_signed_series(maps, dates, pairs=None):
    out = []
    for d in dates:
        legs = maps.get(d, {})
        if pairs is not None:
            legs = {k: v for k, v in legs.items() if k in pairs}
        out.append(sum(legs.values()) if legs else 0.0)
    return out


def fire_series(maps, dates, pairs=None):
    out = []
    for d in dates:
        legs = maps.get(d, {})
        if pairs is not None:
            legs = {k: v for k, v in legs.items() if k in pairs}
        out.append(1.0 if legs else 0.0)
    return out


def cell_signed_pairs(mA, mB, pairs=None):
    """Per-(date,leg) signed indicators over the union of active cells."""
    xs, ys = [], []
    keys = set(mA.keys()) | set(mB.keys())
    for d in sorted(keys):
        la = mA.get(d, {}); lb = mB.get(d, {})
        if pairs is not None:
            la = {k: v for k, v in la.items() if k in pairs}
            lb = {k: v for k, v in lb.items() if k in pairs}
        for pair in set(la) | set(lb):
            xs.append(float(la.get(pair, 0)))
            ys.append(float(lb.get(pair, 0)))
    return xs, ys


def rho_report(name, x, y):
    if len(x) < 3:
        return {"variant": name, "n": len(x), "rho": None, "note": "n too small"}
    r = spearman(x, y)
    return {"variant": name, "n": len(x), "rho": (None if r is None else round(r, 4))}


def main():
    out = {"schema": "forex_free_v5_d2_a7n_schedule_rho_computation_v1",
           "computed_utc": datetime.datetime.now(UTC).isoformat(),
           "convention": "daily completed 16:00 America/New_York bars (20:00Z EDT / 21:00Z EST), DST-aware via zoneinfo",
           "decision_series_only": "no PnL, no costs, no fills beyond schedule instants"}

    a4p1, a4p1_detail = sched_a4p1()
    a4p2 = sched_a4p2()
    a6p1, a6p1_detail = sched_a6p1()
    a6p2, a6p2_trig = sched_a6p2()
    a6p2b, a6p2b_trig = sched_a6p2(ddof=1)
    f1, f1_trig = sched_f1()
    f1n, f1n_trig = sched_f1_median()
    f1_dd1, _ = sched_f1(ddof=1)
    f2, f2_detail, f2_skipped = sched_f2_style()

    out["schedule_counts"] = {
        "A4P1_decisions": len(a4p1), "A4P2_decisions": len(a4p2), "A6P1_decisions": len(a6p1),
        "A6P2_trigger_days": len(a6p2_trig), "A6P2_leg_decisions": len(a6p2),
        "F1_anchor_trigger_days": len(f1_trig), "F1_anchor_leg_decisions": len(f1),
        "F1_neigh_trigger_days": len(f1n_trig), "F1_neigh_leg_decisions": len(f1n),
        "F2style_leg_decisions": len(f2), "F2style_rows": len(f2_detail),
        "F2style_tie_skips": f2_skipped,
    }

    mA4P1, mA4P2, mA6P1, mA6P2, mF1, mF1N, mF2 = map(to_maps, [a4p1, a4p2, a6p1, a6p2, f1, f1n, f2])

    rho = defaultdict(list)

    # ---- A6-P2 vs FXFV4-A6-P1 (both variants), shared legs and full schedules
    for fname, mF in [("anchor_mean", mF1), ("neighbour_median", mF1N)]:
        grid = sorted((set(mA6P2) | set(mF)) )
        pairs_shared = ["AUD/USD", "NZDUSD".replace("NZDUSD", "NZD/USD"), "USD/CAD", "USD/JPY", "USD/CHF"]
        pairs_shared = ["AUD/USD", "NZD/USD", "USD/CAD", "USD/JPY", "USD/CHF"]
        rho[f"A6P2_vs_FXFV4A6P1_{fname}"].append(rho_report("fire_full_grid", fire_series(mA6P2, grid), fire_series(mF, grid)))
        rho[f"A6P2_vs_FXFV4A6P1_{fname}"].append(rho_report("netsigned_full_grid_all6legs_vs_5legs", net_signed_series(mA6P2, grid), net_signed_series(mF, grid)))
        rho[f"A6P2_vs_FXFV4A6P1_{fname}"].append(rho_report("netsigned_full_grid_5shared_legs", net_signed_series(mA6P2, grid, pairs_shared), net_signed_series(mF, grid, pairs_shared)))
        union = sorted(set(d for d in mA6P2 if any(d in mF for _ in [0])) | set(mA6P2) | set(mF))
        rho[f"A6P2_vs_FXFV4A6P1_{fname}"].append(rho_report("netsigned_union_active_dates_5shared", net_signed_series(mA6P2, union, pairs_shared), net_signed_series(mF, union, pairs_shared)))
        # disclosed overlap: EUR-down triggers, 3 legs AUD/NZD/CAD
        eurdown = {d: {p: s for p, s in legs.items() if p in ("AUD/USD", "NZD/USD", "USD/CAD")}
                   for d, legs in mA6P2.items() if sum(legs.values()) < 0}  # EUR-down days have net -? compute by sign
        # recompute precisely: EUR-down = mirrored map: GBP -1, AUD -1, NZD -1, JPY +1, CHF +1, CAD +1 -> net +2? do by GBP leg
        eurdown = {}
        for d, legs in mA6P2.items():
            if legs.get("GBP/USD", 0) < 0:  # EUR-down trigger
                eurdown[d] = {p: legs[p] for p in ("AUD/USD", "NZD/USD", "USD/CAD")}
        f13 = {d: {p: s for p, s in legs.items() if p in ("AUD/USD", "NZD/USD", "USD/CAD")} for d, legs in mF.items()}
        u2 = sorted(set(eurdown) | set(f13))
        rho[f"A6P2_vs_FXFV4A6P1_{fname}"].append(rho_report("EURdown_3leg_netsigned_full_grid", net_signed_series(eurdown, grid), net_signed_series(f13, grid)))
        rho[f"A6P2_vs_FXFV4A6P1_{fname}"].append(rho_report("EURdown_3leg_netsigned_union_active", net_signed_series(eurdown, u2), net_signed_series(f13, u2)))
        xs, ys = cell_signed_pairs(eurdown, f13)
        rho[f"A6P2_vs_FXFV4A6P1_{fname}"].append(rho_report("EURdown_3leg_cellwise_union_active", xs, ys))
        # trigger-set overlap stats
        sA = set(eurdown.keys()); sB = set(d for d, legs in f13.items() if legs)
        inter = sA & sB
        jac = len(inter) / len(sA | sB) if (sA | sB) else None
        rho[f"A6P2_vs_FXFV4A6P1_{fname}"].append({"variant": "trigger_set_overlap_EURdown3leg_vs_F1event",
                                                  "nA": len(sA), "nB": len(sB), "intersection": len(inter),
                                                  "jaccard": (None if jac is None else round(jac, 4))})
        # ddof sensitivity
        f1dd, _ = sched_f1(ddof=1)
        mFdd = to_maps(f1dd)
        rho[f"A6P2_vs_FXFV4A6P1_{fname}"].append(rho_report("ddof1_EURdown_3leg_netsigned_union_active",
                                                            net_signed_series(eurdown, sorted(set(eurdown) | set(mFdd))),
                                                            net_signed_series({d: {p: s for p, s in l.items() if p in ("AUD/USD", "NZD/USD", "USD/CAD")} for d, l in mFdd.items()}, sorted(set(eurdown) | set(mFdd)))))

    # ---- A4-P1 / A4-P2 / A6-P1 vs reconstructed V4-family2-style schedule
    for pname, mA in [("A4P1", mA4P1), ("A4P2", mA4P2), ("A6P1", mA6P1), ("A6P2", mA6P2)]:
        shared_pairs = sorted(set(p for _, p, _ in (a4p1 + a6p1)) & set(p for _, p, _ in f2))
        grid = sorted(set(mA) | set(mF2))
        rho[f"{pname}_vs_F2style"].append(rho_report("netsigned_full_grid_shared_pairs", net_signed_series(mA, grid, shared_pairs), net_signed_series(mF2, grid, shared_pairs)))
        union = sorted(set(mA) | set(mF2))
        rho[f"{pname}_vs_F2style"].append(rho_report("netsigned_union_active_dates_shared_pairs", net_signed_series(mA, union, shared_pairs), net_signed_series(mF2, union, shared_pairs)))
        xs, ys = cell_signed_pairs(mA, mF2)
        rho[f"{pname}_vs_F2style"].append(rho_report("cellwise_signed_union_active_all_legs", xs, ys))
        rho[f"{pname}_vs_F2style"].append(rho_report("fire_full_grid", fire_series(mA, grid), fire_series(mF2, grid)))

    # A4-P1/A4-P2 vs F1 anchor (nearest declared ancestry) due diligence
    for pname, mA in [("A4P1", mA4P1), ("A4P2", mA4P2)]:
        shared_pairs = sorted(set(p for _, p, _ in a4p1) & {"AUD/USD", "NZD/USD", "USD/CAD", "USD/JPY", "USD/CHF"})
        grid = sorted(set(mA) | set(mF1))
        rho[f"{pname}_vs_FXFV4A6P1_anchor"].append(rho_report("netsigned_full_grid_shared_pairs", net_signed_series(mA, grid, shared_pairs), net_signed_series(mF1, grid, shared_pairs)))
        union = sorted(set(mA) | set(mF1))
        rho[f"{pname}_vs_FXFV4A6P1_anchor"].append(rho_report("netsigned_union_active_shared_pairs", net_signed_series(mA, union, shared_pairs), net_signed_series(mF1, union, shared_pairs)))
        xs, ys = cell_signed_pairs(mA, mF1)
        rho[f"{pname}_vs_FXFV4A6P1_anchor"].append(rho_report("cellwise_signed_union_active", xs, ys))

    # event-universe disjointness: CPI decision dates vs policy decision dates
    cpi_dates = set(d for d, _, _ in a4p1)
    pol_dates = set(d for d, _, _ in f2)
    out["event_universe_disjointness"] = {
        "cpi_decision_dates_A4P1": len(cpi_dates),
        "policy_decision_dates_F2style_evidenced": len(pol_dates),
        "shared_calendar_dates": len(cpi_dates & pol_dates),
        "shared_examples": sorted(str(x) for x in (cpi_dates & pol_dates))[:20],
        "verdict": "DISJOINT_EVENT_CLASSES (CPI prints vs RATE_CHANGE); calendar-date coincidence listed",
    }

    # A6-P1 window-side disjointness: exits X vs F2 entries T
    x_dates = set(datetime.date.fromisoformat(r["X"]) for r in a6p1_detail)
    out["a6p1_window_side"] = {
        "a6p1_exit_dates": len(x_dates),
        "f2_entry_dates": len(pol_dates),
        "coinciding_exit_vs_entry_dates": len(x_dates & pol_dates),
        "structure": "A6P1 window [F,X] ENDS at first bar strictly after the CPI availability instant; F2-style book ENTERS at the first 16:00-NY bar at/after a DIFFERENT event class's availability (policy rows). No shared event, no shared window side.",
    }

    # ---------------- full-calendar variants (true shared-date domain) --------
    def full_grid(mA, mB):
        return [d for d in ALL_DAYS]

    # A6-P2 vs F1 both variants, full NY-trading-day calendar of the shared span
    for fname, mF in [("anchor_mean", mF1), ("neighbour_median", mF1N)]:
        grid = full_grid(mA6P2, mF)
        pairs_shared = ["AUD/USD", "NZD/USD", "USD/CAD", "USD/JPY", "USD/CHF"]
        eurdown = {}
        for d, legs in mA6P2.items():
            if legs.get("GBP/USD", 0) < 0:  # EUR-down trigger
                eurdown[d] = {pp: legs[pp] for pp in ("AUD/USD", "NZD/USD", "USD/CAD")}
        f13 = {d: {pp: s for pp, s in legs.items() if pp in ("AUD/USD", "NZD/USD", "USD/CAD")} for d, legs in mF.items()}
        xs, ys = [], []
        for d in grid:
            la = eurdown.get(d, {}); lb = f13.get(d, {})
            for pp in ("AUD/USD", "NZD/USD", "USD/CAD"):
                xs.append(float(la.get(pp, 0))); ys.append(float(lb.get(pp, 0)))
        rho[f"A6P2_vs_FXFV4A6P1_{fname}"].append(rho_report("FULLCAL_EURdown_3leg_cellwise_signed", xs, ys))
        xs6, ys6 = [], []
        for d in grid:
            la = mA6P2.get(d, {}); lb = mF.get(d, {})
            for pp in pairs_shared:
                xs6.append(float(la.get(pp, 0))); ys6.append(float(lb.get(pp, 0)))
        rho[f"A6P2_vs_FXFV4A6P1_{fname}"].append(rho_report("FULLCAL_allshared_legs_cellwise_signed", xs6, ys6))
        # exposure-window overlap context (decision-adjacent, still no PnL):
        # A6P2 holds 1 NY-day from entry t+1; F1 holds 5 NY-days from entry t+1
        def on_windows(trigdays, hold, legs_list):
            dates_idx = {d: i for i, d in enumerate(ALL_DAYS)}
            on = set()
            for d in trigdays:
                i = dates_idx.get(d)
                if i is None:
                    continue
                for k in range(1, hold + 1):
                    if i + k < len(ALL_DAYS):
                        on.add((ALL_DAYS[i + k], None))
            return on
        a6_days = sorted(eurdown.keys())
        f1_days = sorted(d for d, l in f13.items() if l)
        def exposure_cells(trigdays, hold, pairs):
            idx = {d: i for i, d in enumerate(ALL_DAYS)}
            cells = set()
            for d in trigdays:
                i = idx.get(d)
                if i is None:
                    continue
                for k in range(1, hold + 1):
                    if i + k < len(ALL_DAYS):
                        for pp in pairs:
                            cells.add((ALL_DAYS[i + k], pp))
            return cells
        ca = exposure_cells(a6_days, 1, ("AUD/USD", "NZD/USD", "USD/CAD"))
        cb = exposure_cells(f1_days, 5, ("AUD/USD", "NZD/USD", "USD/CAD"))
        inter = len(ca & cb)
        rho[f"A6P2_vs_FXFV4A6P1_{fname}"].append({"variant": "EXPOSURE_cells_EURdown3leg_A6P2_1day_vs_F1_5day",
                                                  "nA6P2_cells": len(ca), "nF1_cells": len(cb),
                                                  "intersection": inter,
                                                  "overlap_frac_of_A6P2": (None if not ca else round(inter / len(ca), 4))})

    # A4-P1/A4-P2/A6-P1 vs F2-style: full-calendar cellwise + fire
    for pname, mA in [("A4P1", mA4P1), ("A4P2", mA4P2), ("A6P1", mA6P1)]:
        shared_pairs = sorted(set(p for _, p, _ in (a4p1 + a6p1)) & set(p for _, p, _ in f2))
        grid = [d for d in ALL_DAYS if S0_START <= d <= S0_END]
        xs, ys = [], []
        for d in grid:
            la = {p: s for p, s in mA.get(d, {}).items() if p in shared_pairs}
            lb = {p: s for p, s in mF2.get(d, {}).items() if p in shared_pairs}
            for pp in shared_pairs:
                xs.append(float(la.get(pp, 0))); ys.append(float(lb.get(pp, 0)))
        rho[f"{pname}_vs_F2style"].append(rho_report("FULLCAL_cellwise_signed_shared_pairs", xs, ys))

    # A6-P2 vs F2-style full-calendar cellwise
    shared_pairs_62 = sorted(set(p for _, p, _ in a6p2) & set(p for _, p, _ in f2))
    grid = [d for d in ALL_DAYS if S0_START <= d <= S0_END]
    xs, ys = [], []
    for d in grid:
        la = {p: s for p, s in mA6P2.get(d, {}).items() if p in shared_pairs_62}
        lb = {p: s for p, s in mF2.get(d, {}).items() if p in shared_pairs_62}
        for pp in shared_pairs_62:
            xs.append(float(la.get(pp, 0))); ys.append(float(lb.get(pp, 0)))
    rho["A6P2_vs_F2style"].append(rho_report("FULLCAL_cellwise_signed_shared_pairs", xs, ys))

    out["rho"] = {k: v for k, v in rho.items()}

    # save per-decision details for the evidence record
    json.dump({"a4p1": a4p1_detail[:5], "n": len(a4p1_detail)}, open(f"{ROOT}/research/control/forex_free_v5_run/d2_a7_novelty_evidence/_smoke.json", "w"))
    out["schedules_saved"] = {
        "a4p1": "d2_a7_novelty_evidence/schedule_A4P1.json",
        "a6p1": "d2_a7_novelty_evidence/schedule_A6P1.json",
        "a6p2_triggers": "d2_a7_novelty_evidence/schedule_A6P2_triggers.json",
        "f1_triggers": "d2_a7_novelty_evidence/schedule_F1_triggers.json",
        "f2_style": "d2_a7_novelty_evidence/schedule_F2_style.json",
    }
    json.dump(a4p1_detail, open(f"{ROOT}/research/control/forex_free_v5_run/d2_a7_novelty_evidence/schedule_A4P1.json", "w"), indent=1, default=str)
    json.dump(a6p1_detail, open(f"{ROOT}/research/control/forex_free_v5_run/d2_a7_novelty_evidence/schedule_A6P1.json", "w"), indent=1, default=str)
    json.dump([{"date": str(d), "z": round(z, 4), "sign": s} for d, z, s in a6p2_trig], open(f"{ROOT}/research/control/forex_free_v5_run/d2_a7_novelty_evidence/schedule_A6P2_triggers.json", "w"), indent=1)
    json.dump([{"date": str(d), "z": round(z, 4)} for d, z in f1_trig], open(f"{ROOT}/research/control/forex_free_v5_run/d2_a7_novelty_evidence/schedule_F1_triggers.json", "w"), indent=1)
    json.dump(f2_detail, open(f"{ROOT}/research/control/forex_free_v5_run/d2_a7_novelty_evidence/schedule_F2_style.json", "w"), indent=1, default=str)

    print(json.dumps(out["schedule_counts"], indent=1))
    print(json.dumps(out["event_universe_disjointness"], indent=1, default=str)[:900])
    print(json.dumps(out["a6p1_window_side"], indent=1, default=str))
    for k, v in out["rho"].items():
        print("\n==", k)
        for r in v:
            print("  ", r)
    json.dump(out, open(f"{ROOT}/research/control/forex_free_v5_run/d2_a7_novelty_evidence/schedule_rho_computation.json", "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
