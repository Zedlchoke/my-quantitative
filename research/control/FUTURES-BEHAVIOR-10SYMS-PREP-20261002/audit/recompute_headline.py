#!/usr/bin/env python3
"""A7 independent recomputation — FUTURES-BEHAVIOR-10SYMS-PREP-20261002 audit.

Fresh-context auditor script (no reuse of lane analysis code). Reads ONLY the
read-only raw snapshot ~/.my-quantitative-data/futures-10syms-v1/raw/ and
recomputes headline OBSERVED numbers claimed in the dossiers:

  R1  ES   5 declared-roll adjacent-close gaps   (ES_DOSSIER 1/3)
  R2  CL   rule-front daily vol sd 3.17%, M2-M1 280/280 negative, median -0.58,
           14 roll gaps median -0.51 / max -8.22 @2026-03-31 CLK6->CLM6
  R3  SI   6 cycle-chain roll gaps; 2026-01-30 crash bar; 2026-01-26 peak close
  R4  NG   front-era m1-m2 median -0.112, 75.2% negative (2025-08-01..2026-10-01)
  R5  GC   real-volume-era sigma 1.61%/day n=424 (2025-01-15..); 6 cycle gaps
  R6  6J   quarterly-chain intervention days 2026-04-30 / 2026-07-30;
           quarterly roll gaps +109/+100/+92 ticks
  R7  Spreads (close-proxy BID/ASK): ESZ6 last-20 (1.0 tick), NQZ6 last-20
           (6.5 ticks), NGX26 last-20 (2 ticks), 6AV6 file medians (4 ticks)
  R8  Header audit: lastTradeDate for CLX6/NGX26 (delivery-month convention check)

Outputs JSON to audit/recompute_headline.json and prints a table.
"""
import json
import math
import re
import statistics
from datetime import date
from pathlib import Path

RAW = Path.home() / ".my-quantitative-data/futures-10syms-v1/raw"
OUT = Path(__file__).with_name("recompute_headline.json")

FNAME = re.compile(
    r"^(?P<sym>[A-Z0-9]{1,4})_(?P<local>[A-Z0-9]+)_(?P<conid>\d+)"
    r"(?:_(?P<marker>front|next|nearest_expired))?"
    r"_(?P<what>TRADES|BID|ASK)_(?P<bar>1day|1hour|1min)_(?P<span>[A-Za-z0-9]+)\.json$"
)

MONTH_OF_CODE = {c: i + 1 for i, c in enumerate("FGHJKMNQUVXZ")}


def load_all():
    """{sym: {local: {what: {"bars": {date: bar}, "ltd": date}}}}"""
    out = {}
    for p in sorted(RAW.glob("*.json")):
        m = FNAME.match(p.name)
        if not m or m.group("marker"):
            continue
        if m.group("bar") != "1day":
            continue
        doc = json.loads(p.read_text())
        bars = {}
        for b in doc.get("bars", []):
            d = date.fromisoformat(b["t"][:10])
            bars[d] = b
        ltd = date.fromisoformat(
            f"{doc['expiry_month'][:4]}-{doc['expiry_month'][4:6]}-{doc['expiry_month'][6:]}")
        sym, local, what = m.group("sym"), m.group("local"), m.group("what")
        e = out.setdefault(sym, {}).setdefault(
            local, {"ltd": ltd, "TRADES": {}, "BID": {}, "ASK": {}, "conid": m.group("conid")})
        e[what] = bars
        if e["ltd"] != ltd:
            raise SystemExit(f"conflicting LTD {local}")
    return out


D = load_all()
results = {"audit_lane": "A7", "raw_dir": str(RAW), "checks": {}}


def closes(sym, local):
    return {d: b["c"] for d, b in D[sym][local]["TRADES"].items()}


def vols(sym, local):
    return {d: b["v"] for d, b in D[sym][local]["TRADES"].items()}


def roll_session(ltd, session_dates):
    """Last session strictly before day-1 of the month of `ltd` (last-trade
    month basis, matching futbt roll.py + BACKTEST_LAUNCH_DRAFT)."""
    day1 = date(ltd.year, ltd.month, 1)
    prior = [d for d in session_dates if d < day1]
    return max(prior) if prior else None


def chain(sym, locals_, lo=None, hi=None):
    """Calendar-roll chain over contracts sorted by LTD.
    Returns list of (date, local, close, vol)."""
    ordered = sorted(locals_, key=lambda s: D[sym][s]["ltd"])
    closes_ = {s: closes(sym, s) for s in ordered}
    vols_ = {s: vols(sym, s) for s in ordered}
    sessions = sorted({d for s in ordered for d in closes_[s]})
    roll_of = {}
    for s in ordered:
        own = sorted(closes_[s])
        roll_of[s] = roll_session(D[sym][s]["ltd"], own)
    # held contract per session: last contract whose roll session >= d,
    # else the first contract
    held = []
    for d in sessions:
        cur = ordered[0]
        for s in ordered:
            r = roll_of[s]
            if r is not None and r >= d:
                cur = s
                break
            cur = s  # if we never break, hold the last (no further roll info)
        held.append(cur)
    rows = []
    for d, s in zip(sessions, held):
        if d in closes_[s]:
            if lo and d < lo:
                continue
            if hi and d > hi:
                continue
            rows.append((d, s, closes_[s][d], vols_[s].get(d, 0.0)))
    return rows, roll_of


def within_returns(rows, log=False):
    """Same-contract consecutive close returns on the chain."""
    rets = []
    for (d1, s1, c1, _), (d2, s2, c2, _) in zip(rows, rows[1:]):
        if s1 == s2 and c1:
            r = (c2 / c1 - 1.0) if not log else math.log(c2 / c1)
            rets.append((d2, r))
    return rets


# ------------------------------------------------------------------ R1: ES
es_locals = list(D["ES"].keys())
rows, roll_of = chain("ES", es_locals)
r1 = []
ordered = sorted(es_locals, key=lambda s: D["ES"][s]["ltd"])
for old, new in zip(ordered, ordered[1:]):
    t = roll_of[old]
    co, cn = closes("ES", old), closes("ES", new)
    if t and t in co and t in cn:
        r1.append({"old": old, "new": new, "session": str(t),
                   "gap_pts": round(cn[t] - co[t], 4)})
results["checks"]["R1_ES_roll_gaps"] = {
    "claim": "5 declared-roll gaps +55.75, +58.75, +52.5, +61.75, +67.75 pts",
    "recomputed": r1}

# ------------------------------------------------------------------ R2: CL
cl_locals = sorted(D["CL"].keys(), key=lambda s: D["CL"][s]["ltd"])
cl_rows, cl_roll_of = chain("CL", cl_locals, lo=date(2025, 8, 21), hi=date(2026, 10, 1))
real = [(d, s, c, v) for d, s, c, v in cl_rows if v > 0]
cl_rets = within_returns(real)
sd = statistics.pstdev([r for _, r in cl_rets]) * 100
# variants to bracket the dossier's 3.17% figure
cl_rets_all = within_returns(cl_rows)                      # endpoints any volume
sd_all = statistics.pstdev([r for _, r in cl_rets_all]) * 100
stitched = []
for (d1, s1, c1, _), (d2, s2, c2, _) in zip(real, real[1:]):
    if c1:
        stitched.append(c2 / c1 - 1.0)                     # incl. roll jumps
sd_stitched = statistics.pstdev(stitched) * 100
cl_ordered = sorted(cl_locals, key=lambda s: D["CL"][s]["ltd"])
cl_gaps = []
m2m1 = []
idx_of = {s: i for i, s in enumerate(cl_ordered)}
for d, s, c, v in real:
    i = idx_of[s]
    if i + 1 < len(cl_ordered):
        nc = closes("CL", cl_ordered[i + 1]).get(d)
        nv = vols("CL", cl_ordered[i + 1]).get(d, 0.0)
        if nc is not None:
            m2m1.append((d, nc - c, nv))
for old, new in zip(cl_ordered, cl_ordered[1:]):
    t = cl_roll_of[old]
    co, cn = closes("CL", old), closes("CL", new)
    if t and t in co and t in cn:
        vo = vols("CL", old).get(t, 0.0)
        vn = vols("CL", new).get(t, 0.0)
        if vo > 0 and vn > 0:
            cl_gaps.append({"old": old, "new": new, "session": str(t),
                            "gap": round(cn[t] - co[t], 4),
                            "v_old": vo, "v_new": vn})
gap_vals = [g["gap"] for g in cl_gaps]
cl14 = [g for g in cl_gaps if g["session"] != "2026-10-01"]  # completed rolls only
                                                        # (2026-10-01 rows are
                                                        # fetch-boundary artifacts)
neg = [x for _, x, _ in m2m1 if x < 0]
neg_rv = [x for _, x, nv in m2m1 if x < 0 and nv > 0]
results["checks"]["R2_CL"] = {
    "claim": "sd 3.17%/day (280 real-volume days 2025-08-21..2026-10-01); "
             "M2-M1 negative 280/280, median -0.58; 14 roll gaps median -0.51, "
             "max -8.22 @2026-03-31 CLK6->CLM6",
    "recomputed": {
        "n_real_volume_days": len(real),
        "n_returns": len(cl_rets),
        "sd_pct": round(sd, 4),
        "sd_pct_anyvol_endpoints": round(sd_all, 4),
        "sd_pct_stitched_incl_rolljumps": round(sd_stitched, 4),
        "n_roll_gaps_completed_14": len(cl14),
        "roll_gap_median_14": round(statistics.median(g["gap"] for g in cl14), 4),
        "annualized_pct": round(sd * math.sqrt(252), 2),
        "M2_minus_M1_days": len(m2m1),
        "M2_minus_M1_negative": len(neg),
        "M2_minus_M1_median": round(statistics.median(x for _, x, _ in m2m1), 4),
        "M2_minus_M1_negative_both_realvol": len(neg_rv),
        "roll_gaps_both_realvol": cl_gaps,
        "roll_gap_median": round(statistics.median(gap_vals), 4),
        "roll_gap_min": round(min(gap_vals), 4),
        "roll_gap_max": round(max(gap_vals), 4),
        "worst_gap_row": min(cl_gaps, key=lambda g: g["gap"]),
    }}

# ------------------------------------------------------------------ R3: SI
CYCLE = set("HKNUZ")  # SI dossier liquid cycle: H,K,N,U,Z (Mar/May/Jul/Sep/Dec)
si_cycle = [s for s in D["SI"] if s[-2] in CYCLE]
si_ordered = sorted(si_cycle, key=lambda s: D["SI"][s]["ltd"])
si_gaps = []
for old, new in zip(si_ordered, si_ordered[1:]):
    t = roll_session(D["SI"][old]["ltd"], sorted(closes("SI", old)))
    co, cn = closes("SI", old), closes("SI", new)
    if t and t in co and t in cn:
        si_gaps.append({"old": old, "new": new, "session": str(t),
                        "gap_usd_oz": round(cn[t] - co[t], 4)})
sih6 = D["SI"]["SIH6"]["TRADES"]
crash = sih6.get(date(2026, 1, 30))
prev = sih6.get(date(2026, 1, 29))
peak_day = max(sih6, key=lambda d: sih6[d]["c"] if sih6[d]["v"] > 0 else -1)
results["checks"]["R3_SI"] = {
    "claim": "6 cycle gaps +0.525,+0.725,+0.605,+0.495,+0.445,+0.770; crash day "
             "2026-01-30 o=98.355 l=74.000 c=78.530 v=173244 ret -31.37%; peak "
             "close 115.505 @2026-01-26",
    "recomputed": {
        "cycle_chain": si_ordered,
        "roll_gaps": si_gaps,
        "crash_bar_2026_01_30": {k: crash[k] for k in ("t", "o", "h", "l", "c", "v", "n")},
        "prev_close_2026_01_29": prev["c"] if prev else None,
        "crash_simple_ret_pct": round((crash["c"] / prev["c"] - 1) * 100, 3) if prev else None,
        "peak_realvol_close": {"date": str(peak_day), "close": sih6[peak_day]["c"]},
    }}

# ------------------------------------------------------------------ R4: NG
ng_ordered = sorted(D["NG"].keys(),
                    key=lambda s: (D["NG"][s]["ltd"].year, D["NG"][s]["ltd"].month))
ng_close = {s: closes("NG", s) for s in ng_ordered}
spreads = []
for d in sorted({d for s in ng_ordered for d in ng_close[s]}):
    if not (date(2025, 8, 1) <= d <= date(2026, 10, 1)):
        continue
    avail = [s for s in ng_ordered if d in ng_close[s]]
    if len(avail) >= 2:
        m1, m2 = avail[0], avail[1]
        spreads.append((d, ng_close[m1][d] - ng_close[m2][d]))
vals = [x for _, x in spreads]
results["checks"]["R4_NG_m1_minus_m2"] = {
    "claim": "front era 2025-08-01..2026-10-01 median -0.112, 75.2% days negative",
    "recomputed": {
        "n_days": len(vals),
        "median": round(statistics.median(vals), 4),
        "pct_negative": round(100 * sum(1 for x in vals if x < 0) / len(vals), 2),
        "p10": round(sorted(vals)[int(0.10 * len(vals))], 4),
        "p90": round(sorted(vals)[int(0.90 * len(vals))], 4),
    }}

# ------------------------------------------------------------------ R5: GC
GC_CYCLE = set("GJMQVZ")
gc_cycle = [s for s in D["GC"] if s[-2] in GC_CYCLE]
gc_ordered = sorted(gc_cycle, key=lambda s: D["GC"][s]["ltd"])
gc_rows_all, gc_roll_of = chain("GC", gc_ordered)
gc_rows = [(d, s, c, v) for d, s, c, v in gc_rows_all
           if date(2025, 1, 15) <= d <= date(2026, 10, 1)]
gc_rets = within_returns(gc_rows, log=True)
gc_sd = statistics.pstdev([r for _, r in gc_rets]) * 100
gc_gaps = []
for old, new in zip(gc_ordered, gc_ordered[1:]):
    t = gc_roll_of[old]
    co, cn = closes("GC", old), closes("GC", new)
    vo = vols("GC", old).get(t, 0) if t else 0
    vn = vols("GC", new).get(t, 0) if t else 0
    if t and t in co and t in cn and vo > 0 and vn > 0 and t >= date(2025, 1, 15):
        gc_gaps.append({"old": old, "new": new, "session": str(t),
                        "gap": round(cn[t] - co[t], 2), "v_old": vo, "v_new": vn})
worst = min(gc_rets, key=lambda x: x[1])
results["checks"]["R5_GC"] = {
    "claim": "real-volume era 2025-01-15..2026-10-01 sigma=1.61%/day n=424; 6 gaps "
             "+32.4,+37.3,+31.2,+31.0,+32.5,+27.5; worst day -12.07% @2026-01-30",
    "recomputed": {
        "n_returns": len(gc_rets),
        "sigma_pct_log": round(gc_sd, 4),
        "roll_gaps": gc_gaps,
        "worst_day": {"date": str(worst[0]), "ret_pct": round(worst[1] * 100, 3)},
    }}

# ------------------------------------------------------------------ R6: 6J
FX_CYCLE = set("HMUZ")
j6_q = [s for s in D["6J"] if s[-2] in FX_CYCLE]
j6_ordered = sorted(j6_q, key=lambda s: D["6J"][s]["ltd"])
j6_rows, j6_roll_of = chain("6J", j6_ordered)


def fx_day_ret(sym, rows, d):
    for i, (dt_, s, c, v) in enumerate(rows):
        if dt_ == d and i > 0:
            pd_, ps, pc, pv = rows[i - 1]
            if ps == s and pc:
                return {"contract": s, "prev_date": str(pd_),
                        "simple_ret_pct": round((c / pc - 1) * 100, 3),
                        "log_ret_pct": round(math.log(c / pc) * 100, 3),
                        "volume": v}
    return None


j6_gaps = []
for old, new in zip(j6_ordered, j6_ordered[1:]):
    t = j6_roll_of[old]
    co, cn = closes("6J", old), closes("6J", new)
    if t and t in co and t in cn:
        j6_gaps.append({"old": old, "new": new, "session": str(t),
                        "gap": round(cn[t] - co[t], 8),
                        "ticks": round((cn[t] - co[t]) / 5e-7, 1)})
results["checks"]["R6_6J"] = {
    "claim": "2026-04-30 +2.48% (vol 107,535), 2026-07-30 +2.75% (vol 490,134) "
             "on quarterly chain; quarterly roll gaps +109/+100/+92 ticks "
             "($681.25/$625/$575) at 2025-11-28/2026-02-27/2026-05-29",
    "recomputed": {
        "ret_2026_04_30": fx_day_ret("6J", j6_rows, date(2026, 4, 30)),
        "ret_2026_07_30": fx_day_ret("6J", j6_rows, date(2026, 7, 30)),
        "quarterly_roll_gaps": j6_gaps,
    }}

# ------------------------------------------------------------------ R7: spreads
def ba_spread(sym, local, last_n=None):
    bid = D[sym][local].get("BID", {})
    ask = D[sym][local].get("ASK", {})
    common = sorted(set(bid) & set(ask))
    if last_n:
        common = common[-last_n:]
    out = {}
    if common:
        sp = [ask[d]["c"] - bid[d]["c"] for d in common]
        out = {"n_days": len(common), "median_spread": round(statistics.median(sp), 8),
               "first": str(common[0]), "last": str(common[-1])}
    return out


mt = {"ES": 0.25, "NQ": 0.25, "NG": 0.001, "6A": 5e-05}
r7 = {}
for sym, local, ln in [("ES", "ESZ6", 20), ("NQ", "NQZ6", 20),
                       ("NG", "NGX26", 20)]:
    s = ba_spread(sym, local, ln)
    s["median_ticks"] = round(s["median_spread"] / mt[sym], 2)
    r7[f"{sym}_{local}_last{ln}"] = s
v6_full = ba_spread("6A", "6AV6")
v6_full["median_ticks"] = round(v6_full["median_spread"] / mt["6A"], 2)
v6_tail95 = ba_spread("6A", "6AV6", 95)
v6_tail95["median_ticks"] = round(v6_tail95["median_spread"] / mt["6A"], 2)
r7["6A_6AV6_full"] = v6_full
r7["6A_6AV6_last95"] = v6_tail95
results["checks"]["R7_spreads"] = {
    "claim": "S6 medians: ES 1.0 tick/$12.5, NQ 6.5/$32.5, NG 2.0/$20; 6A "
             "dossier: 6AV6 median 4 ticks/$20 (n=95); ESZ6 last-20 = 1.0 tick",
    "recomputed": r7}

# ------------------------------------------------------------------ R8: LTD headers
r8 = {}
for sym, local in [("CL", "CLX6"), ("CL", "CLV6"), ("NG", "NGX26"), ("NG", "NGV26"),
                   ("ES", "ESU5"), ("6J", "6JZ5"), ("GC", "GCV5"), ("SI", "SIU5")]:
    if local in D.get(sym, {}):
        code = local[len(sym)]
        r8[f"{sym}_{local}"] = {"ltd_raw_field": str(D[sym][local]["ltd"]),
                                "letter_month": MONTH_OF_CODE[code]}
results["checks"]["R8_lastTradeDate_headers"] = {
    "claim": "raw expiry_month = lastTradeDate; CL/NG delivery month = letter "
             "month (= month after last-trade month); CLX6 20261020, NGX26 20261028",
    "recomputed": r8}

OUT.write_text(json.dumps(results, indent=1))
print(json.dumps(results, indent=1))
