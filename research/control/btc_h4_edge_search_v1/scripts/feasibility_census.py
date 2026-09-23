#!/usr/bin/env python
"""ES1 P1/P2 feasibility census — data gate + counts only. NO PnL anywhere.

Sections:
  GATE  ETH/SOL 1h zips -> H4 panels (floor(open/4h), complete iff 4 aligned
        H1 bars) with OHLC sanity + gap census vs the 1h calendar (fail-closed
        thresholds from the PSV1 BTC law: interior missing <= 0.05% of slots,
        no missing run > 4 consecutive H1).
  FUND  measured funding series (per-settlement signed rates) vs the frozen
        PSV1 constant 1.377e-5/8h: annualized drag comparison, share positive,
        per-fold averages. (Cost authority audit — counts and means only.)
  FLIPC TREND_LF (close > SMA200(H4)) flip census on BTC_H4 + band-law
        flip counts at b in {0.005, 0.01, 0.02, 0.03} (lane C arithmetic).
  VOLP  realized-vol (150 H4 bars) path census: occupancy of
        scale = min(1, TARGET/rvol) at 0.40/0.60 targets (lane A arithmetic).
  BASK  per-asset SMA200 gate occupancy BTC/ETH/SOL + co-occupancy (lane B).
"""
from __future__ import annotations

import datetime as dt
import io
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RAW = ROOT / "data_local" / "vision"
OUT = ROOT / "freezes" / "feasibility_census.json"
BTC_PANEL = Path("/Users/hoangminhlong/my-quantitative/.worktrees/phase-strategy-v1/"
                 "lane-btc-h4/research/control/phase_strategy_v1/lane_btc_h4/data_staging/scored_h4.parquet")
BTC_MANIFEST = Path("/Users/hoangminhlong/my-quantitative/.worktrees/phase-strategy-v1/"
                    "integration/research/control/phase_strategy_v1/lane_btc_h4/data/manifest.json")

FOLD_EDGES = ["2021-05-01", "2023-01-01", "2025-01-01"]
WARMUP = 153  # PSV1 BTC_H4 convention (window reporting starts after warmup)


def read_monthly_zips(series_dir: Path, months: list[str]) -> pd.DataFrame:
    rows = []
    for ym in months:
        path = series_dir / f"{ym}.zip"
        with zipfile.ZipFile(path) as z:
            name = z.namelist()[0]
            raw = z.read(name).decode()
        lines = raw.strip().split("\n")
        start = 1 if not lines[0].split(",")[0].strip().isdigit() else 0
        for ln in lines[start:]:
            f = ln.split(",")
            rows.append((int(f[0]), float(f[1]), float(f[2]), float(f[3]), float(f[4])))
    df = pd.DataFrame(rows, columns=["open_ms", "open", "high", "low", "close"])
    return df.sort_values("open_ms").reset_index(drop=True)


def h4_from_h1(h1: pd.DataFrame) -> pd.DataFrame:
    bucket = (h1["open_ms"] // (4 * 3600 * 1000)) * 4 * 3600 * 1000
    g = h1.assign(bucket=bucket).groupby("bucket")
    out = g.agg(open=("open", "first"), high=("high", "max"), low=("low", "min"),
                close=("close", "last"), n=("close", "size")).reset_index()
    out = out[out["n"] == 4].drop(columns=["n"])  # complete iff 4 aligned H1 bars
    return out


def integrity(h1: pd.DataFrame, label: str, first_ms: int, last_ms: int) -> dict:
    cal = np.arange(first_ms, last_ms + 3600 * 1000, 3600 * 1000)
    missing = np.setdiff1d(cal, h1["open_ms"].to_numpy())
    # interior missing runs
    runs = []
    if missing.size:
        splits = np.where(np.diff(missing) > 3600 * 1000)[0]
        for seg in np.split(missing, splits + 1):
            runs.append(int(len(seg)))
    gap_frac = float(missing.size) / max(1, len(cal))
    ohlc_bad = int(((h1["high"] < h1[["open", "close", "low"]].max(axis=1)) |
                    (h1["low"] > h1[["open", "close", "high"]].min(axis=1))).sum())
    res = {
        "calendar_slots": int(len(cal)), "missing_h1": int(missing.size),
        "gap_fraction": round(gap_frac, 6), "max_missing_run": int(max(runs) if runs else 0),
        "ohlc_violations": ohlc_bad,
    }
    res["verdict"] = ("PASS" if (gap_frac <= 0.0005 and res["max_missing_run"] <= 4 and ohlc_bad == 0)
                      else "FAIL")
    return res


def fold_of(ts) -> np.ndarray:
    if isinstance(ts, pd.Series) and isinstance(ts.dtype, pd.DatetimeTZDtype):
        ms = ts.astype("int64").to_numpy() // 10**6
    else:
        ms = np.asarray(ts, dtype=np.int64)
    edges = [pd.Timestamp(e, tz="UTC").value // 10**6 for e in FOLD_EDGES]
    f = np.zeros(len(ms), dtype=int)
    for e in edges:
        f += (ms >= e).astype(int)
    return f


def main():
    man = json.loads((ROOT / "freezes" / "staging_manifest.json").read_text())
    out = {"schema": "es1.feasibility_census@1",
           "built_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "outcome_blindness": "counts/rates only; no returns, equity, costs or PnL anywhere",
           "gate": {}, "fund": {}, "flipc": {}, "volp": {}, "bask": {}}

    # ---------- GATE: ETH/SOL 1h -> H4 ----------
    panels = {}
    for sym in ("ETHUSDT", "SOLUSDT"):
        s = man["series"][f"klines:{sym}:1h"]
        months = sorted(s["digests"].keys())
        h1 = read_monthly_zips(RAW / f"klines_{sym}_1h", months)
        first_ms, last_ms = int(h1["open_ms"].iloc[0]), int(h1["open_ms"].iloc[-1])
        ig = integrity(h1, sym, first_ms, last_ms)
        h4 = h4_from_h1(h1)
        panels[sym] = h4
        out["gate"][sym] = {**ig, "h1_rows": int(len(h1)), "h4_rows": int(len(h4)),
                            "h4_first_open_utc": dt.datetime.fromtimestamp(
                                int(h4["bucket"].iloc[0]) / 1000, tz=dt.timezone.utc).isoformat(),
                            "h4_last_open_utc": dt.datetime.fromtimestamp(
                                int(h4["bucket"].iloc[-1]) / 1000, tz=dt.timezone.utc).isoformat()}

    # ---------- BTC panel (frozen) for FLIPC/VOLP ----------
    btc = pd.read_parquet(BTC_PANEL)
    btc_close = btc["close"].to_numpy(float)
    btc_open_ms = btc["bucket_ms"].to_numpy()
    sma200 = pd.Series(btc_close).rolling(200).mean().to_numpy()
    valid = np.isfinite(sma200)
    side = np.where(valid, btc_close > sma200, False)
    win = slice(WARMUP, len(btc))
    flips = np.diff(side[win].astype(int))
    n_flips = int(np.abs(flips).sum() // 2 if False else np.sum(flips != 0))
    ts_win = pd.to_datetime(btc_open_ms[win], unit="ms", utc=True)
    folds = fold_of(ts_win)
    flip_idx = np.where(flips != 0)[0]
    flips_per_fold = {f"F{i+1}": int(np.sum(folds[flip_idx] == i)) for i in range(4)}
    # band law flip counts
    band_flips = {}
    for b in (0.005, 0.01, 0.02, 0.03):
        st = np.zeros(len(btc), dtype=int)
        state = 0
        for t in range(len(btc)):
            if not valid[t]:
                st[t] = 0
                continue
            r = btc_close[t] / sma200[t] - 1.0
            if state == 0 and r > b:
                state = 1
            elif state == 1 and r < -b:
                state = 0
            st[t] = state
        bw = st[win]
        band_flips[f"b={b}"] = int(np.sum(np.diff(bw) != 0))
    out["flipc"] = {
        "trend_lf_sma200_btc_h4": {"flips_window": n_flips, "flips_per_fold": flips_per_fold,
                                   "note": "each flip = one round trip of the band-less signal "
                                           "(2 fills); the band law reduces these"},
        "band_law_flips_window": band_flips,
    }

    # ---------- VOLP ----------
    ret = np.diff(np.log(btc_close))
    rvol_bars = pd.Series(ret).rolling(150).std().to_numpy() * np.sqrt(6 * 365)  # ann. (H4)
    rvol_win = rvol_bars[win]
    volp = {}
    for tgt in (0.40, 0.60):
        scale = np.minimum(1.0, tgt / rvol_win)
        volp[f"target={tgt}"] = {
            "occupancy_scale_lt_1": round(float(np.mean(scale < 1.0)), 4),
            "median_scale_when_active": round(float(np.median(scale[scale < 1.0])) if np.any(scale < 1.0) else 1.0, 4),
            "mean_scale": round(float(np.nanmean(scale)), 4),
        }
    out["volp"] = volp

    # ---------- BASK ----------
    bask = {}
    gate_series = {"BTCUSDT": side[win]}
    for sym in ("ETHUSDT", "SOLUSDT"):
        h4 = panels[sym]
        c = h4["close"].to_numpy(float)
        s200 = pd.Series(c).rolling(200).mean().to_numpy()
        g = np.where(np.isfinite(s200), c > s200, False)
        t = pd.to_datetime(h4["bucket"], unit="ms", utc=True)
        folds_s = fold_of(pd.Series(t))
        w = g[np.isfinite(s200)]
        bask[sym] = {
            "h4_rows": int(len(c)),
            "gate_occupancy_window": round(float(np.mean(w)), 4),
            "gate_flips_window": int(np.sum(np.diff(w.astype(int)) != 0)),
            "folds_spanned": int(np.unique(folds_s).size),
        }
        gate_series[sym] = None  # different clock; co-occupancy reported descriptively via dates
    # BTC occupancy on its window
    bask["BTCUSDT"] = {"gate_occupancy_window": round(float(np.mean(side[win])), 4),
                       "gate_flips_window": n_flips, "h4_rows": int(len(btc))}
    out["bask"] = bask

    # ---------- FUND ----------
    CONST = 1.377e-5
    fund = {}
    for sym in ("BTCUSDT", "ETHUSDT", "SOLUSDT"):
        s = man["series"][f"funding:{sym}"]
        months = sorted(s["digests"].keys())
        rows = []
        for ym in months:
            path = RAW / f"funding_{sym}" / f"{ym}.zip"
            with zipfile.ZipFile(path) as z:
                raw = z.read(z.namelist()[0]).decode()
            lines = raw.strip().split("\n")
            start = 1 if not lines[0].split(",")[0].strip().replace(".", "").isdigit() else 0
            for ln in lines[start:]:
                f = ln.split(",")
                rows.append((int(f[0]), float(f[2])))
        fr = pd.DataFrame(rows, columns=["calc_ms", "rate"]).sort_values("calc_ms")
        ann = fr["rate"].mean() * 3 * 365
        fund[sym] = {
            "settlements": int(len(fr)),
            "interval_hours_mode": float(fr["calc_ms"].diff().median() / 3600000),
            "mean_rate_per_8h": round(float(fr["rate"].mean()), 8),
            "median_rate_per_8h": round(float(fr["rate"].median()), 8),
            "share_positive": round(float((fr["rate"] > 0).mean()), 4),
            "annualized_mean_drag_pct": round(float(ann) * 100, 3),
            "psv1_constant_annualized_pct": round(CONST * 3 * 365 * 100, 3),
            "ratio_measured_over_constant": round(float(ann) / (CONST * 3 * 365), 3),
        }
    out["fund"] = fund
    out["gate"]["BTCUSDT_reference"] = {
        "manifest_sha256": hashlib.sha256(BTC_MANIFEST.read_bytes()).hexdigest(),
        "note": "BTC panel is the frozen PSV1 staging (already gated in PSV1/V2/TRV1)"}

    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps({"gate": {k: v["verdict"] for k, v in out["gate"].items() if isinstance(v, dict) and "verdict" in v},
                      "fund_annual_drag_pct": {k: v["annualized_mean_drag_pct"] for k, v in fund.items()},
                      "ratio_vs_constant": {k: v["ratio_measured_over_constant"] for k, v in fund.items()},
                      "trend_lf_flips": n_flips, "flips_per_fold": flips_per_fold,
                      "band_flips": band_flips, "volp": volp}, indent=1))
    print("wrote", OUT)


if __name__ == "__main__":
    import hashlib
    main()
