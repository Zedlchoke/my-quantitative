#!/usr/bin/env python
"""ES1 G11 ancestry rho measurements — PRE-PnL, signal-series information
content only (PSV1 D2 convention: correlation of the signal/weight series,
not returns; no PnL exists anywhere in this script).

Lane A: vol-scale series (targets 0.40/0.60) vs
  - vol-shock proxy (transparent, declared here): z60 of the 30-bar change
    in the 150-bar realized vol (the realized analogue of the dead
    generic_dvol_shock class), and
  - run_imbalance shadow (PSV1 SHADOW_WINDOWS: 12-bar signed run share).
Lane B: BTC+ETH equal-weight long/flat basket exposure vs a cross-sectional
  rank representation (per 42 H4 bars = 7 days: rank BTC vs ETH by trailing
  return, long top / short bottom — the V9 xsect_tstrend class analogue).
Verdict per measurement: |rho| <= 0.20 passes; > 0.20 vetoes the lane.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BTC_PANEL = Path("/Users/hoangminhlong/my-quantitative/.worktrees/phase-strategy-v1/"
                 "lane-btc-h4/research/control/phase_strategy_v1/lane_btc_h4/data_staging/scored_h4.parquet")
ETH_H4 = ROOT / "data_local" / "vision"  # klines rebuilt on the fly
OUT = ROOT / "freezes" / "ancestry_rho.json"
WARMUP = 153


def read_monthly_zips(series_dir: Path, months: list[str]) -> pd.DataFrame:
    rows = []
    for ym in months:
        with zipfile.ZipFile(series_dir / f"{ym}.zip") as z:
            raw = z.read(z.namelist()[0]).decode()
        lines = raw.strip().split("\n")
        start = 1 if not lines[0].split(",")[0].strip().isdigit() else 0
        for ln in lines[start:]:
            f = ln.split(",")
            rows.append((int(f[0]), float(f[1]), float(f[2]), float(f[3]), float(f[4])))
    return pd.DataFrame(rows, columns=["open_ms", "open", "high", "low", "close"])


def h4_from_h1(h1: pd.DataFrame) -> pd.DataFrame:
    bucket = (h1["open_ms"] // (4 * 3600 * 1000)) * 4 * 3600 * 1000
    g = h1.assign(bucket=bucket).groupby("bucket")
    out = g.agg(open=("open", "first"), high=("high", "max"), low=("low", "min"),
                close=("close", "last"), n=("close", "size")).reset_index()
    return out[out["n"] == 4].drop(columns=["n"])


import zipfile


def main():
    btc = pd.read_parquet(BTC_PANEL)
    close = btc["close"].to_numpy(float)
    ret = np.diff(np.log(close), prepend=np.log(close[0]))
    rvol = pd.Series(ret).rolling(150).std().to_numpy() * np.sqrt(6 * 365)

    win = slice(WARMUP, len(close))
    n = len(range(*win.indices(len(close))))

    # lane A series
    scales = {}
    for tgt in (0.40, 0.60):
        scales[tgt] = np.minimum(1.0, tgt / rvol)[win]
    # vol-shock proxy: z60 of 30-bar change in rvol
    chg = pd.Series(rvol).diff(30)
    shock = ((chg - chg.rolling(60).mean()) / chg.rolling(60).std())[win].to_numpy()
    # run_imbalance shadow (12-bar signed run share)
    sgn = np.sign(ret)
    run_imb = pd.Series(sgn).rolling(12).mean()[win].to_numpy()

    # lane B basket exposure: BTC+ETH gates, aligned on BTC window dates
    eth_man = json.loads((ROOT / "freezes" / "staging_manifest.json").read_text())["series"]["klines:ETHUSDT:1h"]
    eth_h1 = read_monthly_zips(ETH_H4 / "klines_ETHUSDT_1h", sorted(eth_man["digests"].keys()))
    eth_h4 = h4_from_h1(eth_h1)
    ec = eth_h4["close"].to_numpy(float)
    esma = pd.Series(ec).rolling(200).mean().to_numpy()
    egate = pd.Series(np.where(np.isfinite(esma), ec > esma, np.nan),
                      index=eth_h4["bucket"])
    btc_bucket = pd.Series(btc["bucket_ms"][win])
    eg_aligned = egate.reindex(btc_bucket).ffill(limit=6).to_numpy()
    bgate = np.where(np.isfinite(pd.Series(close).rolling(200).mean()[win]),
                     close[win] > pd.Series(close).rolling(200).mean()[win], np.nan)
    basket = np.nanmean(np.column_stack([bgate, eg_aligned]), axis=1)
    ok = np.isfinite(basket)

    # xsect rank representation: per 42 bars, rank trailing 42-bar returns BTC vs ETH
    btc_r42 = pd.Series(close).pct_change(42)[win].to_numpy()
    er = pd.Series(ec).pct_change(42)
    er.index = eth_h4["bucket"]
    eth_r42 = er.reindex(btc_bucket).to_numpy()
    both = np.isfinite(btc_r42) & np.isfinite(eth_r42)
    xsect = np.where(np.isnan(btc_r42) | np.isnan(eth_r42), np.nan,
                     np.sign(btc_r42 - eth_r42))  # +1 long-bias when BTC stronger
    xsect = np.nan_to_num(xsect, nan=0.0)

    def rho(a, b, mask=None):
        if mask is not None:
            a, b = a[mask], b[mask]
        m = np.isfinite(a) & np.isfinite(b)
        return round(float(np.corrcoef(a[m], b[m])[0, 1]), 6), int(m.sum())

    res = {
        "schema": "es1.ancestry_rho@1",
        "convention": "PSV1 D2: signal-series information content, PRE-PnL; veto bar 0.20",
        "lane_A": {
            "scale_t0.40_vs_volshock_proxy": rho(scales[0.40], shock),
            "scale_t0.60_vs_volshock_proxy": rho(scales[0.60], shock),
            "scale_t0.40_vs_run_imbalance": rho(scales[0.40], run_imb),
            "scale_t0.60_vs_run_imbalance": rho(scales[0.60], run_imb),
        },
        "lane_B": {
            "basket_btc_eth_vs_xsect_rank_42bar": rho(basket, xsect, mask=ok),
        },
        "lane_C": {
            "declared": "band-state series shares ancestry with TREND_LF by construction; "
                        "no novelty claim; G3-vs-TREND_LF is the adjudicating test",
        },
    }
    vetoes = []
    for lane, d in res.items():
        if not isinstance(d, dict):
            continue
        for k, v in d.items():
            if isinstance(v, tuple) and abs(v[0]) > 0.20:
                vetoes.append(f"{lane}/{k}: |rho|={v[0]}")
    res["vetoes"] = vetoes
    res["verdict"] = "RHO_PASS_ALL" if not vetoes else f"VETOED: {vetoes}"
    OUT.write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
