#!/usr/bin/env python
"""A7-N prewindow-only signal-rank diagnostics.

READ-ONLY inputs:
  - /Users/hoangminhlong/my-quantitative/catalog_live_crypto (15m bars, 20 symbols)
  - /Users/hoangminhlong/my-quantitative/funding_data/scan_2026 (funding history)

Rules honored:
  - completed 15m bars aggregated to daily UTC closes
  - PREWINDOW ONLY: daily stamps strictly before 2026-08-21, at most last 180 days
  - NO scored-window returns/PnL/PF/Sharpe/rankings computed anywhere
Output: research/audits/v11p/a7n_scratch/a7n_rho_results.json (+ csv panels)
"""
import glob
import json
import os
from datetime import datetime, timezone

import numpy as np
import pandas as pd

CAT = "/Users/hoangminhlong/my-quantitative/catalog_live_crypto/data/binance_bar"
FUND = "/Users/hoangminhlong/my-quantitative/funding_data/scan_2026"
OUT = "/Users/hoangminhlong/my-quantitative/.worktrees/v11/d2-a7-novelty/research/audits/v11p/a7n_scratch"

PRE_END = pd.Timestamp("2026-08-21", tz="UTC")   # exclusive
MAX_DAYS = 180
PRE_START = PRE_END - pd.Timedelta(days=MAX_DAYS)  # 2026-02-22 inclusive
BETA_WIN = 90

def decode_fixed(b, precision):
    return int.from_bytes(b, "little", signed=True) / (10 ** (precision + 14))

def load_symbol(dirpath):
    sch = None
    frames = []
    for f in sorted(glob.glob(os.path.join(dirpath, "*.parquet"))):
        sch = sch or __import__("pyarrow.parquet", fromlist=["read_schema"]).read_schema(f)
        md = sch.metadata or {}
        import pyarrow.parquet as pq
        meta = pq.read_schema(f).metadata
        pp = int(meta[b"price_precision"].decode())
        df = pd.read_parquet(f, columns=["close", "quote_volume", "taker_buy_quote_volume", "ts_init"])
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    close_raw = df["close"].map(lambda b: int.from_bytes(b, "little", signed=True))
    df["close"] = close_raw.astype("float64") / (10 ** (pp + 14))
    df["quote_volume"] = pd.to_numeric(df["quote_volume"])
    df["tbuy"] = pd.to_numeric(df["taker_buy_quote_volume"])
    end_ns = df["ts_init"] + 1_000_000  # bar close instant = ts_init + 1ms
    df["dt"] = pd.to_datetime(end_ns, utc=True)
    return df

def daily_panel(df):
    df = df.sort_values("dt")
    r15 = np.log(df["close"].astype("float64")).diff().abs()
    d = df.set_index("dt").resample("1D", origin="start_day").agg(
        close=("close", "last"), bars=("close", "size"), dvol=("quote_volume", "sum"),
        tbuy=("tbuy", "sum"))
    # recompute abs15 sum per day properly
    r15s = r15.groupby(df["dt"].dt.floor("1D")).sum()
    d["abs15"] = r15s.reindex(d.index).fillna(0.0)
    d = d[d["bars"] > 0]
    d["complete"] = d["bars"] >= 90  # >=93.75% of 96 bars
    return d

def main():
    syms = sorted(os.listdir(CAT))
    names = [s.split("-")[0].replace("-PERP", "") for s in syms]
    panels = {}
    for d, nm in zip(syms, names):
        df = load_symbol(os.path.join(CAT, d))
        panels[nm] = daily_panel(df)
    closes = pd.DataFrame({nm: p["close"] for nm, p in panels.items()})
    dvols = pd.DataFrame({nm: p["dvol"] for nm, p in panels.items()})
    nbars = pd.DataFrame({nm: p["bars"] for nm, p in panels.items()})
    # prewindow cut
    closes = closes[(closes.index >= PRE_START) & (closes.index < PRE_END)]
    dvols = dvols[(dvols.index >= PRE_START) & (dvols.index < PRE_END)]
    nbars = nbars[(nbars.index >= PRE_START) & (nbars.index < PRE_END)]
    rets = np.log(closes).diff()
    btc = rets["BTCUSDT"]

    # rolling beta (window ending t-1, min 90 obs within the 180d prewindow), then residual
    beta = pd.DataFrame(index=rets.index, columns=rets.columns, dtype=float)
    for nm in rets.columns:
        b = []
        r = rets[nm]
        for t in range(len(rets)):
            if t < BETA_WIN:
                b.append(np.nan)
                continue
            y = r.iloc[t - BETA_WIN: t].values
            x = btc.iloc[t - BETA_WIN: t].values
            m = ~(np.isnan(y) | np.isnan(x))
            if m.sum() < BETA_WIN - 5:
                b.append(np.nan)
                continue
            vx = np.var(x[m])
            b.append(np.cov(y[m], x[m], bias=True)[0, 1] / vx if vx > 0 else np.nan)
        beta[nm] = b
    resid = rets - beta.shift(1).mul(btc, axis=0)  # beta known at t (from t-90..t-1)

    # ---- features (each a DataFrame over stamps x symbols; value = characteristic) ----
    F = {}
    F["MOM-28D"] = rets.rolling(28, min_periods=28).sum()          # ancestor: trend/momentum
    F["MOM-7D"] = rets.rolling(7, min_periods=7).sum()             # ancestor: weekly reversal
    F["RESMR-7D"] = -(resid.rolling(7, min_periods=7).sum())       # ancestor: residual mean-reversion (reversion sign)
    amihud_d = (resid.abs() / dvols) * 1e6
    F["ILQ-AMIHUD-RES-28D"] = amihud_d.rolling(28, min_periods=28).mean()      # A6-P1 monthly variant (residualised)
    amihud_raw_d = (rets.abs() / dvols) * 1e6
    F["ILLIQ-AMIHUD-28D"] = amihud_raw_d.rolling(28, min_periods=28).mean()    # A5-P1/A8-P1 weekly anchor
    F["ILLIQ-AMIHUD-56D"] = amihud_raw_d.rolling(56, min_periods=56).mean()    # A8-P1 neighbour
    # A5-P1 exact 15m construction: sum|15m log ret| / sum dvol over trailing 28d (ratio of sums)
    abs15 = pd.DataFrame({nm: p["abs15"] for nm, p in panels.items()})
    abs15 = abs15[(abs15.index >= PRE_START) & (abs15.index < PRE_END)]
    F["ILLIQ-AMIHUD-28D-15M"] = abs15.rolling(28, min_periods=28).sum() / dvols.rolling(28, min_periods=28).sum()
    F["DEF-RESVOL-28D"] = resid.rolling(28, min_periods=28).std()              # seed-defensive anchor
    F["LOT-RESMAX-7D"] = resid.rolling(7, min_periods=7).max()                 # seed-lottery anchor
    F["LOT-RESSKEW-30D"] = resid.rolling(30, min_periods=30).skew()            # seed-lottery neighbour
    # Roll (1984) implied spread: 2*sqrt(max(-cov(daily Δp lag1),0)) / close, 28d — approximated from daily closes
    dp = closes.diff()
    roll_num = dp.rolling(28, min_periods=28).cov(dp.shift(1))
    roll = 2 * np.sqrt((-roll_num).clip(lower=0)) / closes
    F["ILLIQ-ROLLSPREAD-28D"] = roll
    # funding carry ancestor (28d mean funding rate) — from funding_data
    fund_rows = {}
    for nm in names:
        p = os.path.join(FUND, nm, "funding.json")
        if not os.path.exists(p):
            continue
        with open(p) as fh:
            j = json.load(fh)
        s = pd.Series(
            [float(r["fundingRate"]) for r in j["rows"]],
            index=pd.to_datetime([r["fundingTime"] for r in j["rows"]], unit="ms", utc=True))
        fund_rows[nm] = s
    funddf = pd.DataFrame(fund_rows)
    fund_daily = funddf.resample("1D").mean()
    fund_daily = fund_daily[(fund_daily.index >= PRE_START) & (fund_daily.index < PRE_END)]
    F["FUND-CARRY-28D"] = fund_daily.rolling(28, min_periods=28).mean()        # ancestor: funding carry/crowding
    # M01 aggressor-flow proxy ancestor: trailing 28d taker-buy share of quote volume
    tb = pd.DataFrame({nm: p["tbuy"] for nm, p in panels.items()})
    tb = tb[(tb.index >= PRE_START) & (tb.index < PRE_END)]
    F["TAKERFLOW-28D"] = tb.rolling(28, min_periods=28).sum() / dvols.rolling(28, min_periods=28).sum()

    # save panels
    closes.to_csv(os.path.join(OUT, "a7n_daily_closes_prewindow.csv"))
    dvols.to_csv(os.path.join(OUT, "a7n_daily_dvol_prewindow.csv"))
    resid.to_csv(os.path.join(OUT, "a7n_daily_resid_prewindow.csv"))
    beta.to_csv(os.path.join(OUT, "a7n_daily_beta_prewindow.csv"))

    min_n = 8

    def rho_matrix(a_key, b_key):
        a, b = F[a_key], F[b_key]
        rhos, ns, stamps = [], [], []
        for t in a.index:
            if t not in b.index:
                continue
            x, y = a.loc[t], b.loc[t]
            m = x.notna() & y.notna()
            if m.sum() < min_n:
                continue
            rx, ry = x[m].rank(), y[m].rank()
            if rx.std() == 0 or ry.std() == 0:
                continue
            rhos.append(np.corrcoef(rx, ry)[0, 1])
            ns.append(int(m.sum()))
            stamps.append(t.strftime("%Y-%m-%d"))
        return rhos, ns, stamps

    # (a) proposal/seed features vs rejected ancestors
    ancestors = ["MOM-28D", "MOM-7D", "RESMR-7D", "FUND-CARRY-28D", "TAKERFLOW-28D"]
    probers = ["DEF-RESVOL-28D", "LOT-RESMAX-7D", "LOT-RESSKEW-30D",
               "ILLIQ-AMIHUD-28D", "ILLIQ-AMIHUD-28D-15M", "ILLIQ-AMIHUD-56D",
               "ILLIQ-ROLLSPREAD-28D", "ILQ-AMIHUD-RES-28D"]
    table_a = {}
    for p in probers:
        row = {}
        for a in ancestors:
            rhos, ns, stamps = rho_matrix(p, a)
            if not rhos:
                row[a] = {"status": "NO_COMMON_STAMPS"}
                continue
            arr = np.array(rhos)
            row[a] = {
                "n_stamps": len(arr), "mean_rho": round(float(arr.mean()), 4),
                "min_rho": round(float(arr.min()), 4), "max_rho": round(float(arr.max()), 4),
                "share_abs_ge_0.50": round(float((np.abs(arr) >= 0.50).mean()), 4),
                "median_n": int(np.median(ns))}
        table_a[p] = row

    # rho on time-averaged cross-sectional z-scores (persistent-book similarity)
    def zbar(key):
        dfk = F[key]
        z = dfk.sub(dfk.mean(axis=1), axis=0).div(dfk.std(axis=1), axis=0)
        return z.mean(axis=0)

    def rho_zbar(a_key, b_key):
        za, zb = zbar(a_key), zbar(b_key)
        m = za.notna() & zb.notna()
        if m.sum() < min_n:
            return None
        return round(float(np.corrcoef(za[m].rank(), zb[m].rank())[0, 1]), 4)

    table_a_z = {p: {a: rho_zbar(p, a) for a in ancestors} for p in probers}

    # (b) frozen-set pairwise on common eligible stamps
    frozen = ["DEF-RESVOL-28D", "LOT-RESMAX-7D", "LOT-RESSKEW-30D",
              "ILLIQ-AMIHUD-28D", "ILLIQ-AMIHUD-28D-15M", "ILQ-AMIHUD-RES-28D",
              "ILLIQ-ROLLSPREAD-28D"]
    table_b = {}
    detail_b = {}
    for i in range(len(frozen)):
        for j in range(i + 1, len(frozen)):
            a, b = frozen[i], frozen[j]
            rhos, ns, stamps = rho_matrix(a, b)
            key = f"{a}|{b}"
            if not rhos:
                table_b[key] = {"status": "NO_COMMON_STAMPS"}
                continue
            arr = np.array(rhos)
            table_b[key] = {
                "n_stamps": len(arr), "mean_rho": round(float(arr.mean()), 4),
                "min_rho": round(float(arr.min()), 4), "max_rho": round(float(arr.max()), 4),
                "share_abs_ge_0.35": round(float((np.abs(arr) >= 0.35).mean()), 4),
                "rho_zbar": rho_zbar(a, b), "median_n": int(np.median(ns))}
            detail_b[key] = {"stamps": stamps, "rhos": [round(float(r), 4) for r in rhos]}

    # OI group availability
    oi_probe = {
        "catalog_crypto_perpetual_files": sorted(os.listdir(
            "/Users/hoangminhlong/my-quantitative/catalog_live_crypto/data/crypto_perpetual"))[:3],
        "note": "crypto_perpetual/ contains 1 file x 1 row per symbol = instrument definition stubs only; "
                "no open-interest time series exists in the staged snapshot; funding_data contains "
                "fundingRate/markPrice only, no OI fields.",
        "verdict": "UNAVAILABLE_FAIL_CLOSED for OI-HP-28D / SAT-OIGRTH / OILEV-FLOW-28D rank diagnostics"}

    out = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "prewindow": {"start": str(PRE_START.date()), "end_exclusive": str(PRE_END.date()),
                      "max_days": MAX_DAYS, "rule": "daily UTC stamps strictly before 2026-08-21"},
        "universe": {"n_symbols": len(names), "symbols": names,
                     "source": "catalog_live_crypto/data/binance_bar (15m bars, 2024-08-23..2026-08-23 staged)"},
        "conventions": {"beta": "rolling 90d OLS daily beta vs BTC, window ending t-1, applied at t",
                        "residual": "r_i,t - beta_i,t*r_BTC,t",
                        "min_cross_section_n": min_n,
                        "rho": "cross-sectional Spearman of feature ranks at each stamp"},
        "table_a_vs_ancestors": table_a,
        "table_a_rho_timeavg_z": table_a_z,
        "table_b_frozen_pairwise": table_b,
        "oi_group": oi_probe,
    }
    with open(os.path.join(OUT, "a7n_rho_results.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    with open(os.path.join(OUT, "a7n_rho_detail_b.json"), "w") as fh:
        json.dump(detail_b, fh, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "oi_group"}, indent=1)[:6000])
    print("OI:", json.dumps(oi_probe["verdict"]))

if __name__ == "__main__":
    main()
