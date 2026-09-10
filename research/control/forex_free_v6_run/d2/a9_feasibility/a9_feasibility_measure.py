#!/usr/bin/env python3
"""A9 D2 feasibility measurement — FOREX-FREE-V6. Counts, dates, flags ONLY.

NO PnL OF ANY KIND IS COMPUTED OR EMITTED (handbook 12.4 scope): no returns,
no profit factors, no cost-adjusted outcomes, no signed magnitudes. Internally
the script computes only the SIGN BITS and STATE BOOLEANS strictly required to
define decision/activation populations (zero-R skip, dead-zone band, trend
direction nonzero, noise-floor pass, state_high flag); no magnitude of any
return, ratio, vol or cumulative-move is written to any output.

Conventions (cited, not asserted — P-1):
- Decision calendar per pair = staged 1day snapshot dates with weekday() < 5
  (provider weekend-stamped rows are not NY sessions — frozen V5/V6 session
  convention, V5 d2_a9 measurement basis; re-measured here).
- Bar completion instant = date 16:00 America/New_York (zoneinfo, DST);
  decision_clock per p3_conditioning_clocks_v6.json clock_semantics and the
  V5 run_contract ("daily 16:00-NY (DST)").
- S0 = 2018-04-04..2025-07-24 frozen (p3_conditioning_clocks_v6.json).
- Clocks: research/control/forex_free_v6_run/p3_conditioning_clocks_v6.json
  (246 = GB 88 / CA 105 / AU 23 / NZ 30; CA conditionable at published
  available_for_daily_decision_date; 3 CA boundary rows remap).
- A6 fold thirds are FROZEN HERE (rubric: "boundaries frozen by A1/A9 before
  any scored computation") on the funded 7-pair common decision-day grid.

Outputs: measure_output.json + per-proposal JSONs next to this script.
"""
import json
import math
import time
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v6/d2-a9-feasibility")
DATA = WT / "data_raw/forex_free_v1"
CLOCKS = WT / "research/control/forex_free_v6_run/p3_conditioning_clocks_v6.json"
OUTDIR = WT / "research/control/forex_free_v6_run/d2/a9_feasibility"

NY = ZoneInfo("America/New_York")
S0_START = date(2018, 4, 4)
S0_END = date(2025, 7, 24)
PAIRS7 = ["AUDUSD", "EURUSD", "GBPUSD", "NZDUSD", "USDCAD", "USDCHF", "USDJPY"]
PAIR_OF = {"GB": "GBPUSD", "CA": "USDCAD", "AU": "AUDUSD", "NZ": "NZDUSD"}
ECON_OF_PAIR = {v: k for k, v in PAIR_OF.items()}
RT_BPS = {"1.0": 3.0, "1.5": 4.5, "2.0": 6.0}

# A4 fold contract (frozen in the A4 proposals)
A4_FOLDS = [("F1", date(2018, 4, 4), date(2020, 12, 31)),
            ("F2", date(2021, 1, 1), date(2023, 3, 31)),
            ("F3", date(2023, 4, 1), date(2025, 7, 24))]


def next_weekday(d):
    d += timedelta(days=1)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def prev_weekday(d):
    d -= timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


# ---------- staged daily calendars ----------
def load_daily(pair):
    doc = json.load(open(DATA / f"{pair}_1day_2018-09-01_a.json"))
    rows = doc["values"]
    wknd = [v["datetime"] for v in rows
            if datetime.strptime(v["datetime"], "%Y-%m-%d").date().weekday() >= 5]
    kept = [v for v in rows
            if datetime.strptime(v["datetime"], "%Y-%m-%d").date().weekday() < 5]
    dates = [datetime.strptime(v["datetime"], "%Y-%m-%d").date() for v in kept]
    assert dates == sorted(dates) and len(set(dates)) == len(dates), pair
    closes = {d: float(v["close"]) for d, v in zip(dates, kept)}
    return dates, closes, len(wknd), doc["status"]


CAL, CLO, WKND, STATUS = {}, {}, {}, {}
for p in PAIRS7:
    CAL[p], CLO[p], WKND[p], STATUS[p] = load_daily(p)

IDX = {p: {d: i for i, d in enumerate(CAL[p])} for p in PAIRS7}

# weekday grid inside S0 (universal decision-day axis, 24/5, no holiday refinement)
GRID_S0 = []
d = S0_START
while d <= S0_END:
    if d.weekday() < 5:
        GRID_S0.append(d)
    d += timedelta(days=1)

# missing weekday dates per pair inside the FUNDED span (provider gaps)
MISSING = {}
for p in PAIRS7:
    lo, hi = CAL[p][0], min(CAL[p][-1], S0_END)
    g, sset = [], set(CAL[p])
    x = lo
    while x <= hi:
        if x.weekday() < 5 and x not in sset:
            g.append(x)
        x += timedelta(days=1)
    MISSING[p] = g

# funded 7-pair common decision-day grid within S0 (intersection calendar)
COMMON = sorted(set.intersection(*[set(CAL[p]) for p in PAIRS7]))
COMMON = [d for d in COMMON if S0_START <= d <= S0_END]
CIDX = {d: i for i, d in enumerate(COMMON)}
n = len(COMMON)
B1, B2 = COMMON[n // 3], COMMON[(2 * n) // 3]
A6_FOLDS = [("F1", COMMON[0], B1), ("F2", next_weekday(B1), B2),
            ("F3", next_weekday(B2), COMMON[-1])]


def a4_fold_of(d0):
    for fid, lo, hi in A4_FOLDS:
        if lo <= d0 <= hi:
            return fid
    return None


def a6_fold_of(d0):
    for fid, lo, hi in A6_FOLDS:
        if lo <= d0 <= hi:
            return fid
    return None


def logret(pair, a, b):
    """sign bit of ln(C_b/C_a) only: +1 / -1 / 0. No magnitude leaves this fn."""
    ca, cb = CLO[pair][a], CLO[pair][b]
    r = math.log(cb / ca)
    return 0 if r == 0.0 else (1 if r > 0 else -1)


def rets(pair, i, k):
    """k consecutive log-return SIGN bits ending at series index i (for
    zero/nonzero checks); magnitudes internal only where a boolean needs them."""
    out = []
    for j in range(i - k + 1, i + 1):
        out.append(logret(pair, CAL[pair][j - 1], CAL[pair][j]))
    return out


def band_flag(pair, i):
    """A6-P1 state band boolean at series index i.
    Returns 'compression' | 'expansion' | 'dead' | 'degenerate'.
    Internally compares rv5/rv20 against the preregistered 0.9/1.1 bands;
    no vol magnitude is emitted."""
    c = [CLO[pair][CAL[pair][j]] for j in range(i - 25, i + 1)]
    r = [math.log(c[j + 1] / c[j]) for j in range(len(c) - 1)]
    r5 = r[-5:]
    r20 = r[-25:-5]
    m5 = sum(r5) / 5.0
    m20 = sum(r20) / 20.0
    v5 = math.sqrt(sum((x - m5) ** 2 for x in r5) / 4.0)
    v20 = math.sqrt(sum((x - m20) ** 2 for x in r20) / 19.0)
    if v20 == 0.0:
        return "degenerate"
    ratio = v5 / v20
    if ratio <= 0.9:
        return "compression"
    if ratio >= 1.1:
        return "expansion"
    return "dead"


def trend10_sign(pair, i):
    c = [CLO[pair][CAL[pair][j]] for j in range(i - 10, i + 1)]
    s = sum(math.log(c[j + 1] / c[j]) for j in range(10))
    return 0 if s == 0.0 else (1 if s > 0 else -1)


# ---------- A4 schedule machinery ----------
def a4_events():
    """Published A4 event list: one row per clock (P1 own-pair view) with
    conditionable D0 (CA rows at available_for_daily_decision_date)."""
    clocks = json.load(open(CLOCKS))["clocks"]
    ev = []
    for c in clocks:
        eco = c["economy"]
        pair = PAIR_OF[eco]
        d0 = date.fromisoformat(c["decision_date"])
        if eco == "CA":
            d0 = date.fromisoformat(c["available_for_daily_decision_date"])
        ev.append({"economy": eco, "pair": pair, "d0": d0,
                   "sha": c["archive_sha256"][:12],
                   "boundary_remap": eco == "CA" and
                   c["available_for_daily_decision_date"] != c["decision_date"]})
    ev.sort(key=lambda e: (e["d0"], e["pair"]))
    return ev


def a4_run(events, k, shift_days, label, pair_scope=None):
    """Reconstruct one A4 arm schedule at count fidelity.
    shift_days=0 anchor/neighbour; 7 = sham (+7 calendar days; CA boundary rows
    shift from their published available_for_daily_decision_date)."""
    per_pair_spans = defaultdict(list)  # pair -> [(entry_idx, exit_idx)]
    rec = []
    for e in events:
        pair = e["pair"]
        if pair_scope and pair not in pair_scope:
            continue
        d0 = e["d0"] + timedelta(days=shift_days)
        row = {"economy": e["economy"], "pair": pair, "d0_pub": str(e["d0"]),
               "d0": str(d0), "shifted": shift_days > 0, "boundary_remap": e["boundary_remap"]}
        dates = CAL[pair]
        # staged-close existence for the reaction window
        if d0 < dates[0]:
            row["skip"] = "pre_staged_data_start"
        elif d0 not in IDX[pair]:
            row["skip"] = "missing_staged_close_d0"
        else:
            i0 = IDX[pair][d0]
            dp = prev_weekday(d0)
            if dp not in IDX[pair]:
                row["skip"] = "missing_staged_close_d_prev"
            else:
                ip = IDX[pair][dp]
                if ip < 4:
                    row["skip"] = "warmup_skipped"  # 5 closes ending at close(D_prev)
                else:
                    d1 = next_weekday(d0)
                    if d1 not in IDX[pair]:
                        row["skip"] = "fill_missing_staged_close_entry"
                    else:
                        ie = IDX[pair][d1]
                        ix = ie + k
                        if ix >= len(dates):
                            row["skip"] = "fill_missing_staged_close_exit"
                        else:
                            # collision: max one open position per pair
                            coll = any(ie <= ox and ix >= oe or (ie <= ox <= ix) or (oe <= ie <= ox)
                                       for oe, ox in per_pair_spans[pair])
                            coll = any(not (ix < oe or ie > ox) for oe, ox in per_pair_spans[pair])
                            sig_open = any(ie <= i0 <= ix for _, ix2 in []) # placeholder
                            sig_in_open = any(oe <= i0 <= ox for oe, ox in per_pair_spans[pair])
                            if sig_in_open or coll:
                                row["skip"] = "collision_skipped"
                            else:
                                s = logret(pair, dp, d0)
                                if s == 0:
                                    row["skip"] = "zero_signal_skipped"
                                else:
                                    row["skip"] = None
                                    row["entry_fill"] = str(d1)
                                    row["exit_fill"] = str(dates[ix])
                                    per_pair_spans[pair].append((ie, ix))
        rec.append(row)
    # aggregates
    agg = {"label": label, "k": k, "shift_days": shift_days,
           "published": len(rec),
           "qualified": sum(1 for r in rec if r["skip"] is None),
           "skips": dict(Counter(r["skip"] for r in rec if r["skip"])),
           "first_qualified_d0": min((r["d0"] for r in rec if r["skip"] is None),
                                     default=None),
           "last_qualified_d0": max((r["d0"] for r in rec if r["skip"] is None),
                                    default=None)}
    folds = {}
    for fid, lo, hi in A4_FOLDS:
        sub = [r for r in rec if r["skip"] is None and lo <= date.fromisoformat(r["d0"]) <= hi]
        pub = [r for r in rec if lo <= date.fromisoformat(r["d0_pub"] if shift_days == 0 else r["d0"]) <= hi]
        span = sum(1 for r in sub if date.fromisoformat(r["exit_fill"]) > hi)
        folds[fid] = {"qualified_decisions": len(sub), "published": len(pub),
                      "span_boundary_purged_equiv": span,
                      "rts": len(sub)}
    agg["folds"] = folds
    agg["rows"] = rec
    agg["rt_bps_drag"] = {t: round(agg["qualified"] * b, 1) for t, b in RT_BPS.items()}
    return agg


def a4_p1():
    ev = a4_events()
    anchor = a4_run(ev, 5, 0, "anchor_reaction_drift_k5")
    neigh = a4_run(ev, 10, 0, "neighbour_reaction_drift_k10")
    sham = a4_run(ev, 5, 7, "control_sham_calendar_plus7_k5")
    # coincidence: shifted date lands on a real published clock of same economy
    pub_by_eco = defaultdict(set)
    for e in ev:
        pub_by_eco[e["economy"]].add(e["d0"])
    coinc = [r["d0"] for r in sham["rows"]
             if date.fromisoformat(r["d0"]) in pub_by_eco[r["economy"]]]
    # same-pair date overlap sham vs anchor
    a_dates = defaultdict(set)
    for r in anchor["rows"]:
        if r["skip"] is None:
            a_dates[r["pair"]].add(r["d0"])
    s_overlap = sum(1 for r in sham["rows"] if r["skip"] is None and r["d0"] in a_dates[r["pair"]])
    s_qual = sum(1 for r in sham["rows"] if r["skip"] is None)
    idt = {"same_economy_shifted_date_on_real_clock": sorted(coinc),
           "same_pair_qualified_date_overlap_sham_vs_anchor": s_overlap,
           "sham_qualified_total": s_qual,
           "anchor_qualified_total": anchor["qualified"],
           "sham_vs_anchor_ratio_total": round(s_qual / max(1, anchor["qualified"]), 3)}
    recon = {eco: len([r for r in anchor["rows"] if r["economy"] == eco]) for eco in PAIR_OF}
    ca_remap_used = [r["d0_pub"] for r in anchor["rows"] if r["boundary_remap"]]
    out = {"hypothesis_id": "FXFV6-A4-P1", "proposal": "d1/a4_postrelease/proposal_P1.json",
           "arms": {"anchor": anchor, "neighbour": neigh, "control": sham},
           "reconciliation_published_per_economy": recon,
           "ca_boundary_remap_rows_published": 3,
           "ca_boundary_remap_rows_in_schedule": len(ca_remap_used),
           "ca_boundary_remap_rows_qualified": len([r for r in anchor["rows"]
                                                    if r["boundary_remap"] and r["skip"] is None]),
           "control_identifiability": idt}
    del out["arms"]["anchor"]["rows"]
    del out["arms"]["neighbour"]["rows"]
    del out["arms"]["control"]["rows"]
    return out


def a4_p2():
    ev = [e for e in a4_events() if e["economy"] == "GB"]
    pairs = ["EURUSD", "USDJPY", "USDCHF"]
    pe = [dict(e, pair=p) for e in ev for p in pairs]
    anchor = a4_run(pe, 5, 0, "anchor_foreign_reaction_drift_k5")
    neigh = a4_run(pe, 10, 0, "neighbour_foreign_reaction_drift_k10")
    sham = a4_run(pe, 5, 7, "control_sham_gb_calendar_plus7_k5")
    pub = set(e["d0"] for e in ev)
    coinc = sorted(set(r["d0"] for r in sham["rows"]
                       if date.fromisoformat(r["d0"]) in pub))
    a_dates = defaultdict(set)
    for r in anchor["rows"]:
        if r["skip"] is None:
            a_dates[r["pair"]].add(r["d0"])
    s_overlap = sum(1 for r in sham["rows"] if r["skip"] is None and r["d0"] in a_dates[r["pair"]])
    per_pair_anchor = {p: sum(1 for r in anchor["rows"] if r["pair"] == p and r["skip"] is None)
                       for p in pairs}
    idt = {"same_economy_shifted_date_on_real_gb_clock": coinc,
           "same_pair_qualified_date_overlap_sham_vs_anchor": s_overlap,
           "sham_qualified_total": sham["qualified"],
           "anchor_qualified_total": anchor["qualified"],
           "sham_vs_anchor_ratio_total": round(sham["qualified"] / max(1, anchor["qualified"]), 3)}
    out = {"hypothesis_id": "FXFV6-A4-P2", "proposal": "d1/a4_postrelease/proposal_P2.json",
           "arms": {"anchor": anchor, "neighbour": neigh, "control": sham},
           "reconciliation": {"published_pair_events": len(pe), "expected": 264,
                              "match": len(pe) == 264},
           "anchor_qualified_per_pair": per_pair_anchor,
           "control_identifiability": idt}
    for a in out["arms"].values():
        a.pop("rows", None)
    return out


# ---------- A6-P1 ----------
def a6_p1_arm(shift, label, state_side):
    clocks = json.load(open(CLOCKS))["clocks"]
    spans = defaultdict(list)
    rows = []
    for c in clocks:
        eco = c["economy"]
        pair = PAIR_OF[eco]
        a = date.fromisoformat(c["available_for_daily_decision_date"]) if eco == "CA" \
            else date.fromisoformat(c["decision_date"])
        a_pub = a
        if shift:
            a = a + timedelta(days=7)
            while a.weekday() >= 5:
                a += timedelta(days=1)
        row = {"economy": eco, "pair": pair, "a_pub": str(a_pub), "a": str(a),
               "shifted": bool(shift)}
        dates = CAL[pair]
        if a < dates[0]:
            row["skip"] = "pre_staged_data_start"
        elif a not in IDX[pair]:
            row["skip"] = "missing_staged_close_a"
        else:
            i = IDX[pair][a]
            if i < 25:
                row["skip"] = "warmup_skipped"  # 26 closes ending at A
            else:
                band = band_flag(pair, i)
                row["band"] = band
                tsign = trend10_sign(pair, i)
                want = {"compression": band == "compression",
                        "expansion": band == "expansion"}[state_side]
                if band == "degenerate":
                    row["skip"] = "degenerate_zero_vol_skipped"
                elif not want:
                    row["skip"] = "dead_zone_skipped" if band == "dead" else f"state_not_{state_side}_skipped"
                elif tsign == 0:
                    row["skip"] = "zero_signal_skipped"
                else:
                    ie = i + 1
                    ix = ie + 5
                    if ix >= len(dates):
                        row["skip"] = "fill_missing_staged_close"
                    elif any(not (ix < oe or ie > ox) for oe, ox in spans[pair]):
                        row["skip"] = "collision_skipped"
                    else:
                        row["skip"] = None
                        row["entry_fill"] = str(dates[ie])
                        row["exit_fill"] = str(dates[ix])
                        spans[pair].append((ie, ix))
        rows.append(row)
    agg = {"label": label, "state_side": state_side,
           "published": len(rows),
           "qualified": sum(1 for r in rows if r["skip"] is None),
           "skips": dict(Counter(r["skip"] for r in rows if r["skip"])),
           "bands_all_events": dict(Counter(r.get("band") for r in rows)),
           "first_qualified_a": min((r["a"] for r in rows if r["skip"] is None), default=None)}
    folds = {}
    for fid, lo, hi in A6_FOLDS:
        sub = [r for r in rows if r["skip"] is None and lo <= date.fromisoformat(r["a"]) <= hi]
        dropped = sum(1 for r in sub if date.fromisoformat(r["exit_fill"]) > hi)
        folds[fid] = {"qualified_decisions": len(sub) - dropped,
                      "qualified_before_boundary_drop": len(sub),
                      "boundary_crossing_dropped": dropped, "rts": len(sub) - dropped}
    agg["folds"] = folds
    agg["rt_bps_drag"] = {t: round(agg["qualified"] * b, 1) for t, b in RT_BPS.items()}
    agg["rows"] = rows
    return agg


def a6_p1():
    anchor = a6_p1_arm(False, "FXFV6-A6-P1-anchor", "compression")
    neigh = a6_p1_arm(False, "FXFV6-A6-P1-neighbour", "expansion")
    sham = a6_p1_arm(True, "FXFV6-A6-P1-sham", "compression")
    pub_by_eco = defaultdict(set)
    for r in anchor["rows"]:
        pub_by_eco[r["economy"]].add(date.fromisoformat(r["a_pub"]))
    coinc = sorted(set(r["a"] for r in sham["rows"]
                       if date.fromisoformat(r["a"]) in pub_by_eco[r["economy"]]))
    # twin agreement: same clock, anchor band at A vs sham band at A_sham (flags only)
    twins = 0
    agree = 0
    amap = {(r["economy"], r["a_pub"]): r.get("band") for r in anchor["rows"]}
    for r in sham["rows"]:
        key = (r["economy"], r["a_pub"])
        if key in amap and amap[key] is not None and r.get("band") is not None:
            twins += 1
            agree += (amap[key] == r["band"])
    idt = {"same_economy_sham_date_on_real_clock": coinc,
           "twin_band_comparable": twins, "twin_band_agreement": agree,
           "twin_band_agreement_frac": round(agree / twins, 3) if twins else None,
           "sham_qualified_total": sham["qualified"],
           "anchor_qualified_total": anchor["qualified"],
           "sham_vs_anchor_ratio_total": round(sham["qualified"] / max(1, anchor["qualified"]), 3)}
    out = {"hypothesis_id": "FXFV6-A6-P1", "proposal": "d1/a6_open/proposal_P1.json",
           "arms": {"anchor": anchor, "neighbour": neigh, "control": sham},
           "control_identifiability": idt,
           "reconciliation_published": 246,
           "reconciliation_rows": len(anchor["rows"])}
    for a in out["arms"].values():
        a.pop("rows", None)
    return out


# ---------- A6-P2 ----------
def a6_p2_state_series():
    """state_high boolean per common-grid index + numeric-guard counts.
    No share magnitudes are emitted."""
    closes = np.array([[CLO[p][d] for p in PAIRS7] for d in COMMON], dtype=float)
    lr = np.diff(np.log(closes), axis=0)  # lr[i] = return of grid day i+1
    s_flag = [None] * len(COMMON)
    guard = {"singular_or_degenerate_correlation": 0, "nonfinite": 0}
    for i in range(20, len(COMMON)):
        w = lr[i - 20:i]  # 20 returns ending at grid day i (lr index aligned)
        if not np.isfinite(w).all():
            guard["nonfinite"] += 1
            continue
        sd = w.std(axis=0)
        if (sd == 0).any():
            guard["singular_or_degenerate_correlation"] += 1
            continue
        z = (w - w.mean(axis=0)) / sd
        cm = np.corrcoef(z, rowvar=False)
        ev = np.linalg.eigvalsh(cm)
        if not np.isfinite(ev).all():
            guard["nonfinite"] += 1
            continue
        s_flag[i] = float(ev[-1] / ev.sum())  # internal only
    first_state = next(i for i in range(len(s_flag)) if s_flag[i] is not None)
    ref_ready = first_state + 252  # 252 prior s values ending at t-1
    hi = [None] * len(COMMON)
    for i in range(first_state, len(COMMON)):
        if s_flag[i] is None:
            continue
        if i >= ref_ready:
            ref = np.array([s_flag[j] for j in range(i - 252, i)])
            thr = np.percentile(ref, 75)
            hi[i] = bool(s_flag[i] >= thr)
    return {"hi": hi, "guard": guard, "first_state_idx": first_state,
            "first_state_date": str(COMMON[first_state]),
            "first_state_eligible_date": str(COMMON[ref_ready])}


def a6_p2_arm(hi, label, state_rule, shift_idx=0):
    """state_rule(i) -> bool | None (None = state undefined at i)."""
    n = len(COMMON)
    noise_floor_cache = {}
    def floor_ok(i, p):
        key = (i, p)
        if key in noise_floor_cache:
            return noise_floor_cache[key]
        closes = [CLO[p][d] for d in COMMON[i - 10:i + 1]]
        r = [math.log(closes[j + 1] / closes[j]) for j in range(10)]
        cum = sum(r)
        m = sum(r) / 10.0
        v = math.sqrt(sum((x - m) ** 2 for x in r) / 9.0)
        ok = abs(cum) >= 0.25 * v * math.sqrt(10) and cum != 0.0
        noise_floor_cache[key] = ok
        return ok
    spans = {p: [] for p in PAIRS7}
    rows = []
    first_state = 20
    start = first_state + 252 + shift_idx
    blocked_days = 0
    skip_leg_floor = 0
    skip_leg_collision = 0
    days_high = 0
    days_not_high = 0
    for i in range(start, n):
        t = COMMON[i]
        if t > S0_END:
            break
        st = state_rule(i)
        row = {"t": str(t)}
        if st is None:
            row["skip"] = "state_undefined_fail_closed"
            blocked_days += 1
            rows.append(row)
            continue
        if not st:
            days_not_high += 1
            rows.append({"t": str(t), "skip": "state_false_no_entry", "n_legs": 0})
            continue
        days_high += 1
        legs = []
        for p in PAIRS7:
            if not floor_ok(i, p):
                skip_leg_floor += 1
                continue
            ie = i + 1
            ix = ie + 5
            if ix >= n:
                continue
            if any(not (ix < oe or ie > ox) for oe, ox in spans[p]):
                skip_leg_collision += 1
                continue
            legs.append((p, ie, ix))
        row["legs"] = [(p, str(COMMON[ie]), str(COMMON[ix])) for p, ie, ix in legs]
        for p, ie, ix in legs:
            spans[p].append((ie, ix))
        row["n_legs"] = len(legs)
        rows.append(row)
    q = sum(r["n_legs"] for r in rows)
    days = sum(1 for r in rows if r["n_legs"] > 0)
    agg = {"label": label, "qualified_leg_decisions": q, "entry_days": days,
           "decision_days_scanned": len(rows),
           "state_high_days": days_high, "state_not_high_days": days_not_high,
           "leg_skips_noise_floor": skip_leg_floor,
           "leg_skips_collision": skip_leg_collision,
           "state_undefined_days": blocked_days,
           "first_eligible_t": rows[0]["t"] if rows else None,
           "last_eligible_t": rows[-1]["t"] if rows else None}
    folds = {}
    for fid, lo, hix in A6_FOLDS:
        sub = [r for r in rows if lo <= date.fromisoformat(r["t"]) <= hix]
        legs = [(lp, date.fromisoformat(le), date.fromisoformat(lx)) for r in sub
                for lp, le, lx in r.get("legs", [])]
        dropped = sum(1 for _, _, x in legs if x > hix)
        folds[fid] = {"qualified_leg_decisions": len(legs) - dropped,
                      "boundary_crossing_dropped": dropped,
                      "entry_days": sum(1 for r in sub if r["n_legs"] > 0),
                      "rts": len(legs) - dropped}
    agg["folds"] = folds
    agg["rt_bps_drag"] = {t: round(q * b, 1) for t, b in RT_BPS.items()}
    return agg, rows


def a6_p2_sensitivity_universal_grid():
    """Sensitivity: A6-P2 missing-day fail-closed rule on the UNIVERSAL funded
    weekday grid (not the intersection grid, where the rule is vacuous by
    construction). Counts decision days blocked because >= 1 of 7 pairs lacks
    a decision close inside the trailing 20-decision-day window. Count-fidelity
    sensitivity only; the primary measurement uses the frozen intersection
    grid (recorded as an A9 implementation choice for selection)."""
    lo, hi_ = COMMON[0], COMMON[-1]
    uni = []
    x = lo
    while x <= hi_:
        if x.weekday() < 5:
            uni.append(x)
        x += timedelta(days=1)
    uset = {p: set(CAL[p]) for p in PAIRS7}
    blocked_after_warmup = 0
    blocked_by_fold = {f: 0 for f, _, _ in A6_FOLDS}
    for i in range(272, len(uni)):
        t = uni[i]
        if t > S0_END:
            break
        win = uni[i - 19: i + 1]
        pre = uni[i - 20]
        if any(pre not in uset[p] or any(w not in uset[p] for w in win) for p in PAIRS7):
            blocked_after_warmup += 1
            for f, flo, fhi in A6_FOLDS:
                if flo <= t <= fhi:
                    blocked_by_fold[f] += 1
    return {"universal_grid_days": len(uni),
            "blocked_decision_days_by_missing_pair_close": blocked_after_warmup,
            "blocked_by_fold": blocked_by_fold,
            "note": "sensitivity only: primary A6-P2 measurement runs the frozen intersection grid where every common date has all 7 closes by construction (state_undefined_days = 0 measured)"}


def a6_p1_sensitivity_full_s0_thirds():
    """A6-P1 fold counts under the alternative full-S0 thirds freeze
    (thirds of GRID_S0 rather than the funded grid). Robustness check for
    the rubric-floor verdict."""
    n = len(GRID_S0)
    b1, b2 = GRID_S0[n // 3], GRID_S0[(2 * n) // 3]
    spans = {"anchor": [("compression", a6_p1_arm(False, "s", "compression")["rows"])],
             "neighbour": [("expansion", a6_p1_arm(False, "n", "expansion")["rows"])]}
    out = {"B1": str(b1), "B2": str(b2)}
    for arm, (side, rows) in [("anchor", spans["anchor"][0]),
                              ("neighbour", spans["neighbour"][0])]:
        folds = []
        for lo, hi_ in [(S0_START, b1), (next_weekday(b1), b2), (next_weekday(b2), S0_END)]:
            folds.append(sum(1 for r in rows if r["skip"] is None
                             and lo <= date.fromisoformat(r["a"]) <= hi_))
        out[f"{arm}_qualified_folds"] = folds
    return out


def a6_p2():
    st = a6_p2_state_series()
    hi = st["hi"]
    anchor, a_rows = a6_p2_arm(hi, "FXFV6-A6-P2-anchor", lambda i: hi[i])
    neigh, n_rows = a6_p2_arm(hi, "FXFV6-A6-P2-neighbour",
                              lambda i: (not hi[i]) if hi[i] is not None else None)
    placebo, p_rows = a6_p2_arm(hi, "FXFV6-A6-P2-placebo",
                                lambda i: hi[i - 100] if i - 100 >= 0 and hi[i - 100] is not None else None,
                                shift_idx=100)
    # identifiability: flag disagreement between state_high(t) and state_high(t-100)
    cmp_span = [i for i in range(20 + 252 + 100, len(COMMON))
                if hi[i] is not None and hi[i - 100] is not None and COMMON[i] <= S0_END]
    disagree = sum(1 for i in cmp_span if hi[i] != hi[i - 100])
    a_days = set(r["t"] for r in a_rows if r["n_legs"] > 0)
    p_days = set(r["t"] for r in p_rows if r["n_legs"] > 0)
    idt = {"comparable_days": len(cmp_span),
           "state_flag_disagreement_days": disagree,
           "state_flag_disagreement_frac": round(disagree / max(1, len(cmp_span)), 3),
           "anchor_entry_days": len(a_days), "placebo_entry_days": len(p_days),
           "entry_day_overlap": len(a_days & p_days),
           "placebo_vs_anchor_leg_ratio_total":
               round(placebo["qualified_leg_decisions"] / max(1, anchor["qualified_leg_decisions"]), 3),
           "placebo_warmup_shift_decision_days": 100,
           "placebo_first_eligible_t": placebo["first_eligible_t"]}
    out = {"hypothesis_id": "FXFV6-A6-P2", "proposal": "d1/a6_open/proposal_P2.json",
           "state_series": {"first_state_date": st["first_state_date"],
                            "first_state_eligible_date": st["first_state_eligible_date"],
                            "guard": st["guard"],
                            "state_high_days_within_S0": sum(1 for i in range(len(COMMON))
                                                             if hi[i] is True)},
           "sensitivity_missing_day_rule_universal_grid": a6_p2_sensitivity_universal_grid(),
           "sensitivity_fold_thirds_full_S0_grid": a6_p1_sensitivity_full_s0_thirds(),
           "arms": {"anchor": anchor, "neighbour": neigh, "control": placebo},
           "control_identifiability": idt}
    return out


# ---------- main ----------
def main():
    t0 = time.time()
    data_summary = {p: {"bars_raw": len(json.loads("{}") if False else CAL[p]) or len(CAL[p]),
                        "weekend_stamped_rows_excluded": WKND[p],
                        "first": str(CAL[p][0]), "last": str(CAL[p][-1]),
                        "provider_weekday_gaps_in_funded_span": len(MISSING[p]),
                        "gap_dates_sample": [str(x) for x in MISSING[p][:8]],
                        "status": STATUS[p]} for p in PAIRS7}
    a4p1 = a4_p1()
    a4p2 = a4_p2()
    a6p1 = a6_p1()
    a6p2 = a6_p2()
    frozen = {"a6_fold_thirds_frozen_by": "A9 (rubric delegation: 'boundaries frozen by A1/A9')",
              "a6_folds": [{"id": f, "start": str(lo), "end": str(hi)} for f, lo, hi in A6_FOLDS],
              "common_grid_days": len(COMMON),
              "common_grid_first": str(COMMON[0]), "common_grid_last": str(COMMON[-1])}
    out = {"schema": "forex_free_v6_d2_a9_measure_v1",
           "measured_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "producer": "A9_INDEPENDENT_FEASIBILITY_AUDITOR",
           "no_pnl_statement": "counts, dates and boolean flags only; sign bits and state booleans were computed solely to define decision populations; no return, ratio, vol, cumulative-move or PnL magnitude appears in any output",
           "staged_data": data_summary,
           "folds": {"a4": [{"id": f, "start": str(lo), "end": str(hi)} for f, lo, hi in A4_FOLDS],
                     **frozen},
           "proposals": {"FXFV6-A4-P1": a4p1, "FXFV6-A4-P2": a4p2,
                         "FXFV6-A6-P1": a6p1, "FXFV6-A6-P2": a6p2},
           "wall_seconds": round(time.time() - t0, 3)}
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / "measure_output.json").write_text(json.dumps(out, indent=1))
    for hid, blob in out["proposals"].items():
        (OUTDIR / f"{hid}.json").write_text(json.dumps(blob, indent=1))
    # console summary
    for hid, b in out["proposals"].items():
        print(f"== {hid}")
        for arm, a in b["arms"].items():
            fs = {f: v.get("qualified_decisions", v.get("qualified_leg_decisions"))
                  for f, v in a["folds"].items()}
            print(f"  {arm:9s} qual={a.get('qualified', a.get('qualified_leg_decisions')):4d} "
                  f"folds={fs} skips={a.get('skips', {})}")
        print(f"  identifiability: {json.dumps(b['control_identifiability'])[:220]}")
    print("wall_seconds", out["wall_seconds"])


if __name__ == "__main__":
    main()
