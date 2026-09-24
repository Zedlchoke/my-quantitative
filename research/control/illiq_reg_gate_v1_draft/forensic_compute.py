"""ILLIQ-REG-V1 draft namespace — FORENSIC aggregation of EXISTING artifacts.

Read-only outside this namespace. No scored cell, no engine modification.
Sources:
  - illiq_diag/{S0R-ANCHOR-A5, Y2024P-ANCHOR-A4, Y2021-ANCHOR-v2}/results/artifact.json
  - catalog_live_crypto_s0r  (bars 2024-04..2025-09)  -> observables at S0R stamps
  - catalog_live_crypto_b20  (bars 2020-01..2024-08)  -> PRE-WINDOW calibration sanity only
  - funding_data_scan/scan_2026 (2020-07..2024-08-20) / scan_2026_a (2024-08-20..2026-08-21)

Descriptive aggregation of staged input data + existing diag payloads only.
"""
import json, math, glob, statistics, sys
import datetime as dt
from pathlib import Path
import pyarrow.parquet as pq

UTC = dt.timezone.utc
CTRL = Path("/Users/hoangminhlong/my-quantitative/.worktrees/crypto-historical-replication-3f-v1/integration/research/control/crypto_historical_replication_3f_v1")
NS = Path("/Users/hoangminhlong/my-quantitative/research/control/illiq_reg_gate_v1_draft")
DAY_NS = 86_400_000_000_000
SYMS = ["1000PEPEUSDT","AAVEUSDT","ACEUSDT","ADAUSDT","AVAXUSDT","BCHUSDT","BNBUSDT",
        "BOMEUSDT","BTCUSDT","DOGEUSDT","ENAUSDT","ETHUSDT","LINKUSDT","NEARUSDT",
        "ONGUSDT","SUIUSDT","SUI_PLACEHOLDER","WLDUSDT","XRPUSDT","ZECUSDT"]
SYMS = sorted(set(s for s in SYMS if s != "SUI_PLACEHOLDER"))
# universe per artifact is authoritative; we just need a superset for DV aggregation
ALL_SYMS = ["1000PEPEUSDT","AAVEUSDT","ACEUSDT","ADAUSDT","AVAXUSDT","BCHUSDT","BNBUSDT",
            "BOMEUSDT","BTCUSDT","DOGEUSDT","ENAUSDT","ETHUSDT","LINKUSDT","NEARUSDT",
            "ONGUSDT","SUIUSDT","WLDUSDT","XRPUSDT","ZECUSDT","SOLUSDT"]
MAJORS = {"BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT","BNBUSDT","ADAUSDT","DOGEUSDT","LINKUSDT","AVAXUSDT","BCHUSDT"}
ILLIQ_MAJORS = set(ALL_SYMS) - MAJORS

def d(ns): return dt.datetime.fromtimestamp(int(ns)/1e9, UTC)
def fdate(ns): return d(ns).date().isoformat()

out = {}

# ---------------------------------------------------------------- artifacts
art = {}
for tag in ["S0R-ANCHOR-A5","Y2024P-ANCHOR-A4","Y2021-ANCHOR-v2"]:
    art[tag] = json.load(open(CTRL/f"illiq_diag/{tag}/results/artifact.json"))

def portfolio_row(tag):
    a = art[tag]
    pm = a["portfolio_metrics"]; bh = a["benchmarks"]["buy_and_hold"]
    sched = a["schedule"]
    return dict(
        window=f"{fdate(sched['first_decision_ns'])}..{fdate(sched['last_decision_ns'])}",
        n_stamps=sched["n_instants"],
        net_return_sum=pm["net_return_sum"], mdd_additive=pm["max_drawdown"],
        position_pf=pm["position_pf"], daily_hit_rate=pm["daily_hit_rate"],
        price_pnl_sum=pm["price_pnl_sum"], funding_sum=pm["funding_sum"],
        cost_charged_sum=pm["cost_charged_sum"], n_positions=pm["n_positions"],
        btc_leg_window_return=bh["per_leg_gross_return"].get("BTCUSDT"),
        bench_ew_cum=bh["cumulative_gross_return"],
        turnover_one_side=a["portfolio_payload"]["summary"]["total_turnover_one_side"],
    )
out["cross_year"] = {t: portfolio_row(t) for t in art}

# ---------------------------------------------------------------- fold tables
out["folds"] = {}
for tag in art:
    a = art[tag]
    rows = []
    for fm in a["fold_metrics"]:
        rows.append(dict(
            fold=fm["fold_label"],
            first=fdate(fm["first_decision_ns"]), last=fdate(fm["last_decision_ns"]),
            n_days=fm["n_days_with_records"], net=fm["net_return_sum"],
            price=fm["price_pnl_sum"], funding=fm["funding_sum"],
            cost=fm["cost_allocated_sum"], mdd=fm["max_drawdown"],
            pf=fm["position_pf"], hit=fm["daily_hit_rate"], n_pos=fm["n_positions"]))
    out["folds"][tag] = rows

# ---------------------------------------------------------------- S0R deep dive
a = art["S0R-ANCHOR-A5"]
pos = a["positions"]; daily = a["daily_returns"]; books = a["books"]
for p in pos:
    p["leg"] = "LONG" if p["signed_weight"] > 0 else "SHORT"
    p["exit_d"] = fdate(p["exit_ns"]); p["entry_d"] = fdate(p["entry_ns"])
    p["exit_month"] = fdate(p["exit_ns"])[:7]; p["entry_month"] = fdate(p["entry_ns"])[:7]

def agg(ps):
    return dict(
        n=len(ps),
        price=math.fsum(p["price_pnl_per_unit"] for p in ps),
        funding=math.fsum(p["funding_cashflow_per_unit"] for p in ps),
        cost=math.fsum(p["cost_allocated_per_unit"] for p in ps),
        net=math.fsum(p["net_pnl_per_unit"] for p in ps),
        wins=len([p for p in ps if p["net_pnl_per_unit"] > 0]),
        mean_abs_w=(statistics.fmean(abs(p["signed_weight"]) for p in ps) if ps else 0.0),
    )

out["s0r_leg_total"] = {leg: agg([p for p in pos if p["leg"] == leg]) for leg in ["LONG","SHORT"]}
out["s0r_leg_by_fold"] = {
    f"{fm['fold_label']}/{leg}": agg([p for p in pos if p["fold_label"] == fm["fold_label"] and p["leg"] == leg])
    for fm in a["fold_metrics"] for leg in ["LONG","SHORT"]}

sym_rows = []
for s in sorted(set(p["symbol"] for p in pos)):
    ps = [p for p in pos if p["symbol"] == s]
    r = agg(ps); r["symbol"] = s
    r["n_long"] = len([p for p in ps if p["leg"] == "LONG"]); r["n_short"] = len([p for p in ps if p["leg"] == "SHORT"])
    sym_rows.append(r)
sym_rows.sort(key=lambda r: r["net"])
out["s0r_by_symbol"] = sym_rows

# month concentration (by exit month of the P&L)
months = {}
for p in pos:
    months.setdefault(p["exit_month"], []).append(p)
out["s0r_by_exit_month"] = {m: agg(ps) for m, ps in sorted(months.items())}

# daily_returns month aggregation (engine's own boundary P&L)
dr_months = {}
for r in daily:
    m = fdate(r["decision_ns"])[:7]
    dr_months.setdefault(m, []).append(r["net_return_per_unit"])
out["s0r_boundary_return_by_month"] = {m: dict(n=len(v), net=math.fsum(v)) for m, v in sorted(dr_months.items())}

# reconciliation: positions grouped by exit date vs daily_returns rows
by_exit = {}
for p in pos:
    by_exit.setdefault(p["exit_d"], []).append(p["net_pnl_per_unit"])
recon = []
for r in daily:
    dd = fdate(r["decision_ns"])
    # engine fills at D+1; realized pnl for boundary stamped D is booked at D
    s = math.fsum(by_exit.get(dd, []))
    recon.append(dict(date=dd, boundary_net=r["net_return_per_unit"], positions_exiting_this_date_sum=s))
out["recon_note"] = "boundary vs same-date position-exit sums shown for alignment diagnosis"
out["s0r_boundary_recon"] = recon[:5]

# ---------------------------------------------------------------- MDD chain (additive, engine convention)
equity, curve = 0.0, []
for r in daily:
    equity += r["net_return_per_unit"]
    curve.append(dict(date=fdate(r["decision_ns"]), ret=r["net_return_per_unit"], eq=equity))
peak, peak_i, worst, chain = -1e9, 0, 0.0, None
run_peak_i = 0
for i, c in enumerate(curve):
    if c["eq"] > peak:
        peak, run_peak_i = c["eq"], i
    dd = peak - c["eq"]
    if dd > worst:
        worst, chain = dd, (run_peak_i, i)
out["s0r_mdd_reproduced"] = dict(depth=worst, peak_date=curve[chain[0]]["date"], trough_date=curve[chain[1]]["date"],
                                 peak_eq=peak, trough_eq=curve[chain[1]]["eq"])
pi, ti = chain
out["s0r_mdd_chain"] = [dict(date=c["date"], ret=c["ret"], eq=c["eq"]) for c in curve[pi:ti+1]]
# multiplicative equity for context
eqm, mcurve = 1.0, []
for r in daily:
    eqm *= (1.0 + r["net_return_per_unit"]); mcurve.append(eqm)
out["s0r_multiplicative_final_equity"] = eqm
out["s0r_worst5_boundaries"] = sorted(curve, key=lambda c: c["ret"])[:5]

# ---------------------------------------------------------------- per-boundary drivers + observables
# positions exiting in the MDD chain window
chain_exits = set(curve[i]["date"] for i in range(pi, ti+1))
# positions close at the NEXT stamp's fill (= stamp+1d); attribute to closing stamp
def closing_stamp(p):
    return (d(p["exit_ns"]) - dt.timedelta(days=1)).date().isoformat()
chain_pos = [p for p in pos if closing_stamp(p) in chain_exits]
cp = {}
for p in chain_pos:
    cp.setdefault(p["symbol"], agg([q for q in chain_pos if q["symbol"] == p["symbol"]]))
out["s0r_mdd_window_by_symbol"] = sorted((dict(symbol=k, **v) for k, v in cp.items()), key=lambda r: r["net"])

# turnover per boundary from fills
turn = {}
for row in a["portfolio_payload"]["rows"]:
    dd = fdate(row["decision_ns"])
    turn[dd] = math.fsum(abs(f["signed_weight_change"]) for f in row["fills"])
out["s0r_turnover_by_boundary"] = turn
out["s0r_mdd_chain_turnover"] = {c["date"]: turn.get(c["date"]) for c in curve[pi:ti+1]}

# book diagnostics at chain stamps
book_by_date = {fdate(b["decision_ns"]): b for b in books}
out["s0r_books_chain"] = [
    dict(date=dd,
         status=(book_by_date.get(dd) or {}).get("status", "TERMINAL_FORCE_FLAT"),
         n_eligible=(book_by_date.get(dd) or {}).get("diagnostics", {}).get("n_eligible"),
         long_leg=(book_by_date.get(dd) or {}).get("diagnostics", {}).get("long_leg"),
         short_leg=(book_by_date.get(dd) or {}).get("diagnostics", {}).get("short_leg"),
         rho_rev=(book_by_date.get(dd) or {}).get("diagnostics", {}).get("rho_amihud_vs_reversal_7d"),
         rho_size=(book_by_date.get(dd) or {}).get("diagnostics", {}).get("rho_amihud_vs_log_size_proxy"))
    for dd in sorted(chain_exits)]

# ---------------------------------------------------------------- staged-bar observables (BTC trend, DV concentration, vol)
def daily_close_dv(catalog, sym, t0=None, t1=None):
    """{date: (close, dv_sum)} from 15m parts; optionally clipped to [t0,t1) dates."""
    directory = CTRL / catalog / "data" / "binance_bar" / f"{sym}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
    files = sorted(glob.glob(str(directory / "*.parquet")))
    per = {}
    for fp in files:
        t = pq.read_table(fp, columns=["ts_event", "close", "quote_volume"])
        ts = t.column("ts_event").to_pylist(); cl = t.column("close").to_pylist(); qv = t.column("quote_volume").to_pylist()
        for i in range(len(ts)):
            day = d(ts[i]).date()
            if t0 and (day < t0 or day >= t1): continue
            raw = cl[i]
            c = (int.from_bytes(raw, "little", signed=True) / 10**16) if isinstance(raw, (bytes, bytearray)) else float(raw)
            qv_raw = float(qv[i])
            e = per.get(day)
            if e is None: per[day] = [c, qv_raw]
            else:
                e[0] = c; e[1] += qv_raw
    return per

def weekly_stamp_dates(first_ns, n):
    return [ (d(first_ns) + dt.timedelta(days=7*i)).date() for i in range(n) ]

def btc_series(catalog, t0, t1):
    per = daily_close_dv(catalog, "BTCUSDT", t0, t1)
    days = sorted(per)
    closes = {day: per[day][0] for day in days}
    return closes

def realized_vol(closes, day, window=30):
    days = [x for x in sorted(closes) if x < day][-window-1:]
    if len(days) < window + 1: return None
    rs = [math.log(closes[days[i+1]] / closes[days[i]]) for i in range(window)]
    return statistics.fmean(rs) and (statistics.pstdev(rs) * math.sqrt(365))

def conc_series(catalog, t0, t1, majors=MAJORS):
    """CONC_t = trailing-28d mean of daily (DV in majors / total DV) across staged universe."""
    total, mjs = {}, {}
    for sym in ALL_SYMS:
        try:
            per = daily_close_dv(catalog, sym, t0, t1)
        except Exception:
            continue
        for day, (c, dv) in per.items():
            total[day] = total.get(day, 0.0) + dv
            if sym in majors: mjs[day] = mjs.get(day, 0.0) + dv
    share = {day: (mjs.get(day, 0.0) / total[day]) for day in sorted(total) if total[day] > 0}
    return share

def stamp_observables(share, closes, stamps, conc_window=28, trend_window=90):
    rows = {}
    days = sorted(share)
    for st in stamps:
        past_share = [share[x] for x in days if st - dt.timedelta(days=conc_window) <= x < st]
        conc = math.fsum(past_share)/len(past_share) if past_share else None
        past_share90 = [share[x] for x in days if st - dt.timedelta(days=trend_window) <= x < st]
        conc90 = math.fsum(past_share90)/len(past_share90) if past_share90 else None
        past_days = [x for x in sorted(closes) if x <= st]
        btc_now = closes.get(st) or (past_days[-1] if past_days else None)
        b90 = [closes[x] for x in sorted(closes) if st - dt.timedelta(days=trend_window) <= x <= st]
        trend = (btc_now / b90[0] - 1.0) if btc_now and b90 else None
        rows[st.isoformat()] = dict(conc28=conc, conc90=conc90, d_conc_90d=(None if conc is None or conc90 is None else conc - conc90),
                                    btc_close=btc_now, btc_trend_90d=trend, btc_rvol30=realized_vol(closes, st))
    return rows

# S0R observables at the 52 stamps (forensic description)
s0r_stamps = [ d(r["decision_ns"]).date() for r in daily ]
t0 = dt.date(2024, 4, 1); t1 = dt.date(2025, 10, 1)
share_s0r = conc_series("catalog_live_crypto_s0r", t0, t1)
closes_s0r = btc_series("catalog_live_crypto_s0r", t0, t1)
obs_s0r = stamp_observables(share_s0r, closes_s0r, s0r_stamps)
out["s0r_observables_at_stamps"] = obs_s0r
out["s0r_btc_window"] = dict(first=closes_s0r.get(s0r_stamps[0]), last=closes_s0r.get(s0r_stamps[-1]))

# chain-stamp observables table
out["s0r_mdd_chain_observables"] = [dict(date=dd, **obs_s0r.get(dd, {})) for dd in sorted(chain_exits)]

# ---------------------------------------------------------------- funding observables
def funding_rows(scan, sym):
    p = CTRL / "funding_data_scan" / scan / sym / "funding.json"
    if not p.exists(): return []
    return json.load(open(p))["rows"]

def funding_state_at(stamp_date, scan):
    t_ms = int(dt.datetime.combine(stamp_date, dt.time(0, 0), UTC).timestamp() * 1000)
    w0 = t_ms - 7 * 86_400_000
    per = {}
    for sym in ALL_SYMS:
        rs = [float(r["fundingRate"]) for r in funding_rows(scan, sym) if w0 <= int(r["fundingTime"]) < t_ms]
        if len(rs) >= 7:  # need a real trailing sample
            per[sym] = math.fsum(rs) / len(rs) * 3 * 365  # annualized
    if len(per) < 5: return None
    vals = sorted(per.values())
    p10, p90 = vals[int(0.1*len(vals))], vals[min(len(vals)-1, int(0.9*len(vals)))]
    liq = statistics.fmean(v for s, v in per.items() if s in MAJORS)
    ill = statistics.fmean(v for s, v in per.items() if s in ILLIQ_MAJORS)
    return dict(n=len(per), cs_mean=statistics.fmean(vals), p90_p10=p90 - p10, majors_mean=liq, illiq_mean=ill)

out["s0r_funding_state_chain"] = {}
for dd in sorted(chain_exits):
    st = dt.date.fromisoformat(dd)
    stt = funding_state_at(st, "scan_2026_a")
    out["s0r_funding_state_chain"][dd] = stt

# ---------------------------------------------------------------- PRE-WINDOW calibration sanity (2020-01-01..2024-08-21)
pw0, pw1 = dt.date(2020, 1, 1), dt.date(2024, 8, 22)
share_pw = conc_series("catalog_live_crypto_b20", pw0, pw1)
closes_pw = btc_series("catalog_live_crypto_b20", pw0, pw1)
pw_mondays = []
day = pw0
while day <= pw1:
    if day.weekday() == 0: pw_mondays.append(day)
    day += dt.timedelta(days=1)
obs_pw = stamp_observables(share_pw, closes_pw, pw_mondays)
vals_d = [v["d_conc_90d"] for v in obs_pw.values() if v["d_conc_90d"] is not None]
vals_v = [v["btc_rvol30"] for v in obs_pw.values() if v["btc_rvol30"] is not None]
def q(sorted_vals, p):
    i = min(len(sorted_vals)-1, max(0, int(p * len(sorted_vals))))
    return sorted_vals[i]
dv_sorted, vv_sorted = sorted(vals_d), sorted(vals_v)
print("DEBUG share_pw days:", len(share_pw), "closes_pw days:", len(closes_pw),
      "n_d:", len(vals_d), "n_v:", len(vals_v), "mondays:", len(pw_mondays),
      "sample d:", vals_d[:3] if vals_d else "EMPTY")
sys.stdout.flush()
out["prewindow_sanity"] = dict(
    window=f"{pw0}..{pw1}", n_mondays=len(pw_mondays),
    n_d=len(vals_d), n_v=len(vals_v),
    d_conc_90d=dict(p10=q(dv_sorted,0.10), p25=q(dv_sorted,0.25), p50=q(dv_sorted,0.50),
                    p70=q(dv_sorted,0.70), p75=q(dv_sorted,0.75), p90=q(dv_sorted,0.90),
                    min=dv_sorted[0], max=dv_sorted[-1]),
    btc_rvol30=dict(p10=q(vv_sorted,0.10), p25=q(vv_sorted,0.25), p50=q(vv_sorted,0.50),
                    p75=q(vv_sorted,0.75), p90=q(vv_sorted,0.90),
                    min=vv_sorted[0], max=vv_sorted[-1]),
    share_conc28=dict(p25=q(sorted([v["conc28"] for v in obs_pw.values() if v["conc28"] is not None]),0.25),
                      p50=q(sorted([v["conc28"] for v in obs_pw.values() if v["conc28"] is not None]),0.50),
                      p75=q(sorted([v["conc28"] for v in obs_pw.values() if v["conc28"] is not None]),0.75)),
)

# Y2021 / Y2024P leg splits (context)
for tag in ["Y2024P-ANCHOR-A4","Y2021-ANCHOR-v2"]:
    pp = art[tag]["positions"]
    for p in pp: p["leg"] = "LONG" if p["signed_weight"] > 0 else "SHORT"
    out[f"{tag}_leg_total"] = {leg: agg([p for p in pp if p["leg"] == leg]) for leg in ["LONG","SHORT"]}

json.dump(out, open(NS/"forensic_numbers.json","w"), indent=1, default=str)
print("WROTE", NS/"forensic_numbers.json")

# ---------------------------------------------------------------- console digest
print(json.dumps(out["cross_year"], indent=1, default=str))
print("FOLDS S0R:", json.dumps(out["folds"]["S0R-ANCHOR-A5"], indent=1))
print("LEGS S0R:", json.dumps(out["s0r_leg_total"], indent=1))
print("LEGS by fold S0R:", json.dumps(out["s0r_leg_by_fold"], indent=1))
print("TOP8 SYMBOL LOSERS S0R:", json.dumps(out["s0r_by_symbol"][:8], indent=1))
print("BOTTOM3 (winners) :", json.dumps(out["s0r_by_symbol"][-3:], indent=1))
print("MONTHS S0R:", json.dumps(out["s0r_boundary_return_by_month"], indent=1))
print("MDD:", json.dumps(out["s0r_mdd_reproduced"], indent=1))
print("CHAIN:", json.dumps(out["s0r_mdd_chain"], indent=1))
print("CHAIN TURNOVER:", json.dumps(out["s0r_mdd_chain_turnover"], indent=1))
print("CHAIN OBS:", json.dumps(out["s0r_mdd_chain_observables"], indent=1))
print("CHAIN FUNDING:", json.dumps(out["s0r_funding_state_chain"], indent=1))
print("MDD WINDOW BY SYMBOL:", json.dumps(out["s0r_mdd_window_by_symbol"], indent=1))
print("PREWINDOW SANITY:", json.dumps(out["prewindow_sanity"], indent=1))
print("LEG Y2024P:", json.dumps(out["Y2024P-ANCHOR-A4_leg_total"], indent=1))
print("LEG Y2021:", json.dumps(out["Y2021-ANCHOR-v2_leg_total"], indent=1))
