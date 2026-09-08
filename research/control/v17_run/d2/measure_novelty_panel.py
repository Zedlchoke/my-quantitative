"""CRYPTO-V17 D2: measured novelty for the panel-based proposals (A4-P1, A4-P2, A5-P1, A5-P2).

Builds each proposal's conditioning exposure EXACTLY per its frozen
exposure_series_spec, builds forbidden-family proxy exposures from the same
published H1 panel (daily + hourly granularity), and reports pooled
Pearson + Spearman |rho| per (proposal x proxy). Pooled |rho| > 0.20 = veto
(measured, never argued). No PnL anywhere.
"""
import csv
import json
import math
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

WORKTREE = Path(__file__).resolve().parents[4]
STAGING = WORKTREE / "v17_data" / "staging_v17"
SYMS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

def f(x):
    try: return float(x)
    except (TypeError, ValueError): return 0.0

def load(sym):
    rows = list(csv.DictReader(open(STAGING / f"panel_{sym}_h1.csv")))
    return rows

def daily(rows):
    by = defaultdict(list)
    for r in rows: by[r["day_utc"]].append(r)
    out = {}
    for d, rs in sorted(by.items()):
        q = sum(f(r["quote_total"]) for r in rs); n = sum(int(r["n_trades"]) for r in rs)
        qty = sum(f(r["qty_total"]) for r in rs)
        vwap = q / qty if qty else 0.0
        last = f(rs[-1]["last_price"]); first = f(rs[0]["first_price"])
        bq = sum(f(r["buy_qty"]) for r in rs); sq = sum(f(r["sell_qty"]) for r in rs)
        bc = sum(int(r["buy_count"]) for r in rs)
        mb = max(int(r["max_run_buy"]) for r in rs); ms = max(int(r["max_run_sell"]) for r in rs)
        out[d] = {"ret": math.log(last / first) if first and last else 0.0,
                  "cdf_disp": (last - vwap) / vwap if vwap else 0.0,
                  "run_imb": (bq - sq) / (bq + sq) if (bq + sq) else 0.0,
                  "run_persist": (mb - ms) / (mb + ms) if (mb + ms) else 0.0,
                  "dvol": q, "ntrades": n,
                  "taker_sat": bc / n if n else 0.0,
                  "elite": sum(f(r["max_trade_quote"]) for r in rs),
                  "avg_ticket": q / n if n else 0.0}
    ks = sorted(out)
    prev = {}
    for i, d in enumerate(ks):
        r = out[d]
        r["dvol_shock"] = r["dvol"] / statistics.median([out[x]["dvol"] for x in ks[max(0, i - 21):i]]) if i >= 21 else None
        r["amihud"] = abs(r["ret"]) / r["dvol"] * 1e9 if r["dvol"] else None
        r["tsmom28"] = (sum(out[x]["ret"] for x in ks[max(0, i - 27):i + 1])) if i >= 27 else None
        r["dvol_level_log"] = math.log(r["dvol"]) if r["dvol"] else None
        r["avg_ticket_ratio"] = (r["avg_ticket"] / statistics.median([out[x]["avg_ticket"] for x in ks[max(0, i - 59):i]])) if i >= 59 and statistics.median([out[x]["avg_ticket"] for x in ks[max(0, i - 59):i]]) else None
        prev[d] = r
    return out

def hourly_proxies(rows):
    out = []
    for i, r in enumerate(rows):
        p = f(r["last_price"]); vw = f(r["vwap"])
        out.append({
            "hour_disp": (p - vw) / vw if vw else 0.0,
            "hour_run_imb": (f(r["buy_qty"]) - f(r["sell_qty"])) / (f(r["buy_qty"]) + f(r["sell_qty"])) if (f(r["buy_qty"]) + f(r["sell_qty"])) else 0.0,
            "hour_taker_sat": int(r["buy_count"]) / int(r["n_trades"]) if int(r["n_trades"]) else 0.0,
            "hour_ret": math.log(p / f(rows[i - 1]["last_price"])) if i and f(rows[i - 1]["last_price"]) else 0.0})
    return out

def pearson(x, y):
    pairs = [(a, b) for a, b in zip(x, y) if a is not None and b is not None]
    if len(pairs) < 30: return None
    xs = [a for a, _ in pairs]; ys = [b for _, b in pairs]
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    sxx = sum((a - mx) ** 2 for a in xs); syy = sum((b - my) ** 2 for b in ys)
    if sxx <= 0 or syy <= 0: return None
    return sum((a - mx) * (b - my) for a, b in pairs) / math.sqrt(sxx * syy)

def spearman(x, y):
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v); i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]: j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1): r[order[k]] = avg
            i = j + 1
        return r
    pairs = [(a, b) for a, b in zip(x, y) if a is not None and b is not None]
    if len(pairs) < 30: return None
    return pearson(rank([a for a, _ in pairs]), rank([b for _, b in pairs]))

def pooled(x_by_sym, y_by_sym, fn):
    xs, ys = [], []
    for s in x_by_sym:
        xs += x_by_sym[s]; ys += y_by_sym[s]
    return fn(xs, ys)

# ---------------- proposal exposures ----------------

def expo_wkndliq(symbols):
    """A4-P1: hourly signed calendar flag (Fri>=22:00..Sun = -1 else 0)."""
    ex = {}
    for sym in symbols:
        rows = load(sym)
        ex[sym] = [-1.0 if (r["day_utc"] in ("Saturday", "Sunday") or
                            (r["day_utc"].split("-") and datetime.strptime(r["day_utc"], "%Y-%m-%d").weekday() == 4 and int(r["hour_utc"][11:13]) >= 22)) else 0.0
                   for r in rows]
    return ex

def expo_silres(symbols):
    """A4-P2: sparse trigger exposure per frozen spec."""
    ex = {}
    for sym in symbols:
        rows = load(sym)
        gaps = [f(r["entry_gap_s"]) for r in rows]
        nt = [int(r["n_trades"]) for r in rows]
        dirs = [1.0 if f(r["last_price"]) > f(r["first_price"]) else (-1.0 if f(r["last_price"]) < f(r["first_price"]) else 0.0) for r in rows]
        out = []
        for i in range(len(rows)):
            if i < 720:
                out.append(0.0); continue
            w_g = gaps[i - 720:i]; w_n = nt[i - 720:i]
            q90 = sorted(w_g)[min(len(w_g) - 1, int(len(w_g) * 0.90))]
            med = statistics.median(w_n)
            if gaps[i] >= q90 and nt[i] >= 1.5 * med:
                out.append(dirs[i])
            else:
                out.append(0.0)
        ex[sym] = out
    return ex

def daily_by_sym(symbols, fn):
    out = {}
    for sym in symbols:
        d = daily(load(sym))
        ks = sorted(d)
        # value dated t uses t-1 info (proposal law); shift by one day
        vals = []
        for i, k in enumerate(ks):
            if i == 0: vals.append(None); continue
            vals.append(fn(d[ks[i - 1]], d, ks, i - 1))
        out[sym] = vals
    return out

def expo_attn(symbols):
    """a5-P1: SOL US-session trade-count share minus majors' same share, t-1."""
    d = {s: daily(load(s)) for s in symbols}
    ks = sorted(d["BTCUSDT"])
    hourly = {s: defaultdict(lambda: defaultdict(int)) for s in symbols}
    for s in symbols:
        for r in load(s):
            hourly[s][r["day_utc"]][int(r["hour_utc"][11:13])] += int(r["n_trades"])
    vals = []
    for j, t in enumerate(ks):
        if j == 0: vals.append(None); continue
        prev = ks[j - 1]
        sol_h = hourly["SOLUSDT"][prev]; maj_h = {h: hourly["BTCUSDT"][prev][h] + hourly["ETHUSDT"][prev][h] for h in range(24)}
        ts, tm = sum(sol_h.values()), sum(maj_h.values())
        if not ts or not tm: vals.append(None); continue
        e = sum(sol_h[h] / ts - maj_h[h] / tm for h in range(14, 22))
        vals.append(e)
    return {"SOLUSDT": vals}

def expo_ticket(symbols):
    """a5-P2: SOL avg-ticket ratio vs majors' avg-ticket ratio, each over own med60."""
    d = {s: daily(load(s)) for s in symbols}
    ks = sorted(d["BTCUSDT"])
    def series(s):
        out = []
        for k in ks:
            r = d[s][k]
            out.append(r["avg_ticket"])
        return out
    sol, maj = series("SOLUSDT"), None
    maj_q = [d["BTCUSDT"][k]["dvol"] + d["ETHUSDT"][k]["dvol"] for k in ks]
    maj_n = [d["BTCUSDT"][k]["ntrades"] + d["ETHUSDT"][k]["ntrades"] for k in ks]
    maj_t = [q / n if n else 0.0 for q, n in zip(maj_q, maj_n)]
    vals = []
    for i, k in enumerate(ks):
        if i < 60: vals.append(None); continue
        ms = statistics.median(sol[i - 60:i]); mm = statistics.median(maj_t[i - 60:i])
        if not ms or not mm or not maj_t[i - 1]: vals.append(None); continue
        vals.append((sol[i - 1] / ms) / (maj_t[i - 1] / mm))
    return {"SOLUSDT": vals}

# ---------------- runner ----------------

def main():
    PANEL = ["BTCUSDT", "ETHUSDT"]
    PANEL3 = PANEL + ["SOLUSDT"]
    d = {s: daily(load(s)) for s in PANEL3}
    ks = sorted(d["BTCUSDT"])

    daily_proxy_names = ["cdf_disp", "run_imb", "run_persist", "taker_sat", "ret", "tsmom28", "dvol_shock", "amihud", "dvol_level_log", "avg_ticket_ratio", "elite"]
    def proxy_daily(name):
        out = {}
        for s in PANEL3:
            out[s] = [d[s][k].get(name) for k in ks]
        return out

    def align_daily(exposure):
        """exposure: {sym: vals aligned to ks}; returns {sym: vals} (already aligned)."""
        return exposure

    results = {}

    # --- A4-P1 WKNDLIQ: hourly flag; daily agg = daily mean of flag (per symbol) ---
    ex_h = expo_wkndliq(PANEL)
    ex_daily = {s: [statistics.fmean([v for v, r in zip(ex_h[s], load(s)) if r["day_utc"] == k]) for k in ks] for s in PANEL}
    hourly_proxy = {s: hourly_proxies(load(s)) for s in PANEL}
    rhos = {}
    for pname in daily_proxy_names:
        pr = proxy_daily(pname)
        rhos["daily:" + pname] = {"pearson": pooled(ex_daily, pr, pearson), "spearman": pooled(ex_daily, pr, spearman)}
    for pname in ["hour_disp", "hour_run_imb", "hour_taker_sat", "hour_ret"]:
        pr = {s: [row[pname] for row in hourly_proxy[s]] for s in PANEL}
        rhos["hourly:" + pname] = {"pearson": pooled(ex_h, pr, pearson), "spearman": pooled(ex_h, pr, spearman)}
    results["V17-A4-P1-WKNDLIQ"] = rhos

    # --- A4-P2 SILRES: hourly sparse; daily agg = daily sum; also hourly direct ---
    ex_h2 = expo_silres(PANEL)
    ex2_daily = {s: [sum(v for v, r in zip(ex_h2[s], load(s)) if r["day_utc"] == k) for k in ks] for s in PANEL}
    rhos = {}
    for pname in daily_proxy_names:
        pr = proxy_daily(pname)
        rhos["daily:" + pname] = {"pearson": pooled(ex2_daily, pr, pearson), "spearman": pooled(ex2_daily, pr, spearman)}
    for pname in ["hour_disp", "hour_run_imb", "hour_taker_sat", "hour_ret"]:
        pr = {s: [row[pname] for row in hourly_proxy[s]] for s in PANEL}
        rhos["hourly:" + pname] = {"pearson": pooled(ex_h2, pr, pearson), "spearman": pooled(ex_h2, pr, spearman)}
    results["V17-A4-P2-SILRES"] = rhos

    # --- a5-P1 ATTN-PHASE: daily SOL series ---
    ex3 = expo_attn(PANEL3)
    rhos = {}
    for pname in daily_proxy_names:
        pr = proxy_daily(pname)
        rhos["daily:" + pname] = {"pearson": pooled(ex3, pr, pearson), "spearman": pooled(ex3, pr, spearman)}
    results["V17-a5-P1-ATTN-PHASE"] = rhos

    # --- a5-P2 TICKET-BREADTH: daily SOL series ---
    ex4 = expo_ticket(PANEL3)
    rhos = {}
    for pname in daily_proxy_names:
        pr = proxy_daily(pname)
        rhos["daily:" + pname] = {"pearson": pooled(ex4, pr, pearson), "spearman": pooled(ex4, pr, spearman)}
    results["V17-a5-P2-TICKET-BREADTH"] = rhos

    # verdicts: max |rho| across proxies (pearson or spearman)
    verdicts = {}
    for hyp, rhos in results.items():
        abs_pairs = [(k, max(abs(v["pearson"] or 0), abs(v["spearman"] or 0))) for k, v in rhos.items()]
        worst = max(abs_pairs, key=lambda kv: kv[1])
        n_veto = sum(1 for v in rhos.values() if max(abs(v["pearson"] or 0), abs(v["spearman"] or 0)) > 0.20)
        verdicts[hyp] = {"worst_proxy": worst[0], "worst_pooled_abs_rho": round(worst[1], 4),
                         "proxies_over_020": n_veto,
                         "verdict": "VETO_MEASURED" if n_veto else "NOVELTY_PASS"}
    out = {"schema": "v17_run_artifact_v1", "artifact": "d2_novelty_panel",
           "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "method": "exposure per frozen proposal spec vs forbidden-family proxies built from the published H1 panel; pooled across symbols; Pearson+Spearman; veto pooled |rho|>0.20",
           "proxy_definitions": {
             "cdf_disp": "daily (last-vwap)/vwap — CLOSE-DISPLACE-FADE",
             "run_imb": "daily (buy-sell)/(buy+sell) qty — run imbalance shadow",
             "run_persist": "daily (maxRunBuy-maxRunSell)/(sum) — RUNPERSIST",
             "taker_sat": "daily buy_count/n_trades — TAKER-SAT",
             "ret": "daily log return — momentum/reversal forms",
             "tsmom28": "28d cumulative return — XSECT-TSTREND",
             "dvol_shock": "dollar-volume / median21 — VOLSHK",
             "amihud": "|ret|/dollar-volume*1e9 — ILLIQ/LIQEPIS class",
             "dvol_level_log": "log dollar-volume — activity-level family",
             "avg_ticket_ratio": "avg ticket / median60 — ticket-mix/activity forms",
             "elite": "sum max_trade_quote — elite-level shadow",
             "hourly:*": "hourly granular proxies for the same families"},
           "results": results, "verdicts": verdicts}
    outp = Path(__file__).resolve().parents[1] / "d2_novelty_panel_v17.json"
    outp.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(verdicts, indent=1))
    print("worst rhos:")
    for hyp, rhos in results.items():
        top = sorted(((k, max(abs(v["pearson"] or 0), abs(v["spearman"] or 0))) for k, v in rhos.items()), key=lambda kv: -kv[1])[:3]
        print(" ", hyp, [(k, round(v, 3)) for k, v in top])

if __name__ == "__main__":
    main()
