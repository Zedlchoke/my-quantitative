#!/usr/bin/env python
"""T4 independent recompute for the first real prospective forecast rows (2026-10-09).

Fresh-context auditor arithmetic: parses the saved raw bar files, recomputes RV5/RV30
with the collector's own documented semantics (dedupe keep-first on ts, consecutive
pairs gap==60e9 ns and close>0 both, return anchored at LATER bar-start, math.fsum of
ret^2 over later bar-starts 09:31..09:34 (RV5) / 09:31..09:59 (RV30)), then recomputes
yhat_reduced/yhat_full from the PINNED betas in 17_null_calibration_raw_v2.json.
No model fit. Read-only except stdout.
"""
import json, math, hashlib, sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
BASE = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-q1q2q3-prep/prep/research/control/PREP-FUTURES-Q1Q2Q3-20261007"
RAW = {s: f"{BASE}/prospective/raw/2026-10-09/{s}_Z6_2026-10-09_m1.json" for s in ("ES", "NQ")}
LEDGER = f"{BASE}/prospective/ledger_q1_prospective.jsonl"
CALIB = f"{BASE}/17_null_calibration_raw_v2.json"

MIN_PAIR_NS = 60 * 10**9
CUTOFF = (10, 0)  # 10:00:00 ET exclusive

def tod_ns(h, m, s=0):
    return (h * 3600 + m * 60 + s) * 10**9

RV5_LATER = [tod_ns(9, 30 + i) for i in range(1, 5)]
RV30_LATER = [tod_ns(9, 30 + i) for i in range(1, 30)]
RTH_LO = tod_ns(9, 30)

def ny_parts(ts_ns):
    dt = datetime.fromtimestamp(ts_ns / 1e9, tz=timezone.utc).astimezone(NY)
    midnight = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    return dt.date(), int((dt - midnight).total_seconds() * 1e9)

def rel(a, b):
    if a == b:
        return 0.0
    return abs(a - b) / max(abs(a), abs(b), 1e-300)

report = {"checks": []}
rows = [json.loads(l) for l in open(LEDGER) if l.strip()]
assert len(rows) == 2, f"ledger rows {len(rows)} != 2"

calib = json.load(open(CALIB))

for sym in ("ES", "NQ"):
    r = next(x for x in rows if x["symbol"] == sym)
    raw = json.load(open(RAW[sym]))
    bars = raw["bars"]
    ck = {"symbol": sym, "n_bars_file": len(bars), "request": raw.get("request"),
          "fetched_utc": raw.get("fetched_utc")}
    # --- timestamps: max bar ts vs bar_completed_at
    ts_all = [b["ts_ns"] for b in bars]
    dts = [datetime.fromtimestamp(t / 1e9, tz=timezone.utc) for t in ts_all]
    ck["max_bar_utc"] = max(dts).strftime("%Y-%m-%dT%H:%M:%SZ")
    ck["min_bar_utc"] = min(dts).strftime("%Y-%m-%dT%H:%M:%SZ")
    ck["all_bars_lt_1400Z"] = all(t < tod_ns(10, 0) or ny_parts(t)[0] != datetime.fromisoformat(r["session_date"]).date() for t in ts_all)
    day_bars = [b for b in bars if ny_parts(b["ts_ns"])[0].isoformat() == r["session_date"] and ny_parts(b["ts_ns"])[1] < tod_ns(10, 0) and ny_parts(b["ts_ns"])[1] >= RTH_LO]
    ck["n_day_input_bars"] = len(day_bars)
    tods = sorted(ny_parts(b["ts_ns"])[1] for b in day_bars)
    ck["first_bar_et"] = datetime.fromtimestamp(day_bars[0]["ts_ns"] / 1e9, tz=timezone.utc).astimezone(NY).isoformat() if day_bars else None
    ck["last_bar_et"] = datetime.fromtimestamp(day_bars[-1]["ts_ns"] / 1e9, tz=timezone.utc).astimezone(NY).isoformat() if day_bars else None
    # expected grid 09:30..09:59
    expected = [tod_ns(9, 30 + i) for i in range(30)]
    have = set(tods)
    ck["missing_bar_tods_et"] = [f"{9 + (t // 3600):02d}:{(t % 3600) // 60:02d}" for t in expected if t not in have]
    # gaps between consecutive bars
    gaps = [b2 - b1 for b1, b2 in zip(tods, tods[1:])]
    ck["non60s_gaps"] = [f"{g / 10**9:.0f}s" for g in gaps if g != MIN_PAIR_NS]
    ck["any_close_nonpos"] = any(b["close"] <= 0 for b in day_bars)
    # --- recompute pairs/features (collector semantics, independent impl)
    b = []
    seen = set()
    for x in sorted(day_bars, key=lambda x: x["ts_ns"]):
        if x["ts_ns"] in seen:
            continue
        seen.add(x["ts_ns"])
        b.append(x)
    pr = []
    for prev, cur in zip(b, b[1:]):
        gap = cur["ts_ns"] - prev["ts_ns"]
        ok = (gap == MIN_PAIR_NS and cur["close"] > 0 and prev["close"] > 0)
        pr.append({"later": cur["ts_ns"], "ok": ok,
                   "ret": math.log(cur["close"] / prev["close"]) if ok else None})
    def rvsum(laters):
        allowed = set(laters)
        return math.fsum(p["ret"] ** 2 for p in pr if p["ok"] and ny_parts(p["later"])[1] in allowed)
    rv5 = rvsum(RV5_LATER)
    rv30 = rvsum(RV30_LATER)
    n_open_valid = sum(1 for p in pr if p["ok"] and ny_parts(p["later"])[1] in set(RV30_LATER))
    ck["recomputed"] = {"rv5": rv5, "rv30": rv30, "n_pairs_open_valid": n_open_valid}
    ck["ledger"] = r["features"]
    ck["rel_dev_rv5"] = rel(rv5, r["features"]["rv5"])
    ck["rel_dev_rv30"] = rel(rv30, r["features"]["rv30"])
    ck["n_pairs_match"] = n_open_valid == r["guard_flags"]["n_pairs_open_valid"]
    # --- forecast recompute from pinned betas
    pc = calib["symbols"][sym]["pinned_coefficients"]
    ck["calib_betas_match_row"] = (pc["reduced_beta"] == r["pins_applied"]["reduced_beta"]
                                   and pc["full_beta"] == r["pins_applied"]["full_beta"]
                                   and pc["ybar_train_full"] == r["pins_applied"]["ybar"])
    lg1, t20 = r["features"]["lag1_logrest30"], r["features"]["trail20_logrest30"]
    l5, l30 = math.log(rv5), math.log(rv30)
    y_red = pc["reduced_beta"][0] + pc["reduced_beta"][1] * lg1 + pc["reduced_beta"][2] * t20
    y_full = (pc["full_beta"][0] + pc["full_beta"][1] * lg1 + pc["full_beta"][2] * t20
              + pc["full_beta"][3] * l5 + pc["full_beta"][4] * l30)
    ck["recomputed_forecast"] = {"yhat_reduced": y_red, "yhat_full": y_full,
                                 "log_rv5": l5, "log_rv30": l30}
    ck["rel_dev_yhat_reduced"] = rel(y_red, r["forecast"]["yhat_reduced"])
    ck["rel_dev_yhat_full"] = rel(y_full, r["forecast"]["yhat_full"])
    report["checks"].append(ck)

# --- timestamp inequalities (the core check)
ts = {}
for sym in ("ES", "NQ"):
    r = next(x for x in rows if x["symbol"] == sym)
    ts[sym] = {"bar_completed_at": r["bar_completed_at"], "data_arrival_at": r["data_arrival_at"],
               "forecast_made_at": r["forecast_made_at"], "issue_deadline_et": r["issue_deadline_et"]}
def T(z):
    return datetime.strptime(z, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
DEADLINE = T("2026-10-09T14:05:00Z")
ineq = {}
for sym in ("ES", "NQ"):
    bc, da, fm = T(ts[sym]["bar_completed_at"]), T(ts[sym]["data_arrival_at"]), T(ts[sym]["forecast_made_at"])
    ineq[sym] = {
        "bc_eq_140000Z": bc == T("2026-10-09T14:00:00Z"),
        "da_gt_bc": da > bc,
        "da_lt_deadline": da < DEADLINE,
        "fm_gt_bc": fm > bc,
        "fm_lt_deadline": fm < DEADLINE,
        "fm_ge_da": fm >= da,
    }
report["timestamp_inequalities"] = ineq

# parity captures: open-window bar counts on September paper-feed days (G3 context)
par = {}
import glob, os
for f in sorted(glob.glob(f"{BASE}/prospective/ops/parity_captures/*_ibkr.json")):
    try:
        d = json.load(open(f))
    except Exception:
        continue
    bars = d.get("bars") or d.get("rows") or []
    n_open = 0
    for b in bars:
        dt = b.get("date") or b.get("ts_et") or b.get("datetime")
        if dt is None:
            continue
        try:
            if hasattr(dt, "tzinfo") and dt.tzinfo is not None:
                dtv = dt.astimezone(NY)
            else:
                dtv = datetime.fromisoformat(str(dt)).astimezone(NY)
        except Exception:
            continue
        if dtv.hour == 9 and 30 <= dtv.minute <= 59:
            n_open += 1
    if bars:
        par[os.path.basename(f)] = {"n_bars_total": len(bars), "n_bars_0930_0959": n_open}
report["parity_captures_open_counts"] = par

print(json.dumps(report, indent=1, default=str))
