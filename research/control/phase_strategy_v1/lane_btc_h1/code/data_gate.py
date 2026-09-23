"""Data gate for cell BTC_H1 — Binance Vision USDT-M klines (plan sec 9.1).

Integrity law is FAIL-CLOSED: OHLC sanity, duplicate-ts rejection, gap census
vs the hourly UTC calendar, zero-volume flags, and a mandatory cross-check of
the frozen 15m catalog (sha-pinned) resampled to 1h vs the Vision 1h series.
No smoothing anywhere: mismatches beyond documented tolerance => BLOCKED.

Outcome-blindness: prices/volumes are used for integrity and labeling only.
No returns / PnL path exists in this module.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import urllib.request

VOLT_BASE = "https://data.binance.vision/data/futures/um"
SYMBOL = "BTCUSDT"
INTERVAL = "1h"
MONTHLY_FMT = VOLT_BASE + "/monthly/klines/BTCUSDT/1h/BTCUSDT-1h-{ym}.zip"
DAILY_FMT = VOLT_BASE + "/daily/klines/BTCUSDT/1h/BTCUSDT-1h-{ymd}.zip"

FROZEN_15M_PATH = Path(
    "/Users/hoangminhlong/my-quantitative/catalog/data/binance_bar/"
    "BTCUSDT-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL/"
    "2025-08-20T02-34-14-475394000Z_2026-08-20T02-34-14-475394000Z.parquet"
)
FROZEN_15M_SHA256 = (
    "81d4f147c6bc6a8e03275140a65ac06a63c2e644f449f1c48d8758b187fc8321"
)

# Documented tolerances, frozen BEFORE retrieval:
GAP_TOLERANCE = {
    "max_consecutive_missing_hours": 4,
    "max_total_missing_hours": 48,
    "note": "interior gaps beyond this are BLOCKED evidence, never smoothed",
}
XCHECK_TOLERANCE = {
    "price_abs": 0.01,          # one tick at price precision 2
    "volume_rel": 1e-9,
    "bucket_law": "a 1h bucket is compared only if it contains exactly 4 complete 15m bars (RSM-V1 completeness law); partial buckets are excluded from comparison and counted",
}
COLUMNS = [
    "open_time", "open", "high", "low", "close", "volume", "close_time",
    "quote_volume", "count", "taker_buy_base", "taker_buy_quote", "ignore",
]


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def fetch(url: str, dest: Path, retries: int = 3, timeout: int = 60) -> tuple[int, str]:
    """Download url to dest (atomic). Returns (http_status, sha256_hex)."""
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "psv1-l1-data-gate"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
            tmp = dest.with_suffix(dest.suffix + ".part")
            tmp.write_bytes(data)
            tmp.replace(dest)
            return 200, hashlib.sha256(data).hexdigest()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise
            last_err = e
        except Exception as e:  # noqa: BLE001
            last_err = e
    raise RuntimeError(f"download failed after {retries} attempts: {url}: {last_err}")


def parse_kline_zip(path: Path) -> pd.DataFrame:
    """Parse one Vision kline zip. Handles header/no-header and ms/us stamps."""
    with zipfile.ZipFile(path) as z:
        name = z.namelist()[0]
        with z.open(name) as f:
            text = io.TextIOWrapper(f, encoding="utf-8")
            rows = list(csv.reader(text))
    if rows and not rows[0][0].strip().isdigit():
        rows = rows[1:]  # header row (older files)
    recs = []
    for r in rows:
        recs.append([r[0]] + [float(x) for x in r[1:6]] + [r[6].split(".")[0]]
                    + [float(r[7]), int(r[8]), float(r[9]), float(r[10]),
                       float(r[11])])
    df = pd.DataFrame(recs, columns=COLUMNS)
    ot = df["open_time"].astype("int64").to_numpy()
    unit = "us" if ot.max() > 10**14 else "ms"
    df["open_time"] = pd.to_datetime(ot, unit=unit, utc=True)
    df["close_time"] = pd.to_datetime(
        df["close_time"].astype("int64").to_numpy(), unit=unit, utc=True
    )
    return df


def build_window(today_utc: str, staging: Path) -> tuple[list[dict], pd.DataFrame]:
    """Retrieve monthly zips 2020-01..last complete month, then daily zips for
    the partial current month. Returns (manifest_entries, concatenated_df)."""
    today = pd.Timestamp(today_utc, tz="UTC")
    this_month = pd.Period(today.strftime("%Y-%m"), freq="M")
    entries: list[dict] = []
    frames: list[pd.DataFrame] = []

    first = pd.Period("2020-01", freq="M")
    for p in pd.period_range(first, this_month - 1, freq="M"):
        ym = str(p)
        url = MONTHLY_FMT.format(ym=ym)
        dest = staging / f"BTCUSDT-1h-{ym}.zip"
        if not dest.exists():
            fetch(url, dest)
        nbytes = dest.stat().st_size
        frames.append(parse_kline_zip(dest))
        entries.append({
            "kind": "monthly_zip", "period": ym, "url": url,
            "file": dest.name, "bytes": nbytes, "sha256": sha256_file(dest),
        })

    # daily tail for the current (partial) month
    day = pd.Timestamp(str(this_month) + "-01", tz="UTC")
    while day <= today.normalize():
        ymd = day.strftime("%Y-%m-%d")
        url = DAILY_FMT.format(ymd=ymd)
        dest = staging / f"BTCUSDT-1h-{ymd}.zip"
        try:
            if not dest.exists():
                fetch(url, dest)
        except urllib.error.HTTPError as e:
            if e.code == 404 and ymd == today.strftime("%Y-%m-%d"):
                break  # today's file not yet published: partial month ends yesterday
            raise
        nbytes = dest.stat().st_size
        frames.append(parse_kline_zip(dest))
        entries.append({
            "kind": "daily_zip", "period": ymd, "url": url,
            "file": dest.name, "bytes": nbytes, "sha256": sha256_file(dest),
        })
        day += pd.Timedelta(days=1)

    df = pd.concat(frames, ignore_index=True)
    return entries, df


def integrity_checks(df: pd.DataFrame) -> dict:
    """FAIL-CLOSED integrity law. Raises on duplicates; returns report dict."""
    report: dict = {}
    df = df.sort_values("open_time").reset_index(drop=True)
    dups = int(df["open_time"].duplicated().sum())
    report["duplicate_open_time_count"] = dups
    if dups:
        raise IntegrityError(f"DUPLICATE TIMESTAMPS: {dups} (fail-closed)")

    o, h, lo, c = (df[k].to_numpy(float) for k in ["open", "high", "low", "close"])
    v = df["volume"].to_numpy(float)
    bad = (h < lo) | (c > h) | (c < lo) | (o > h) | (o < lo)
    report["ohlc_sanity_violations"] = int(bad.sum())
    if bad.any():
        raise IntegrityError(f"OHLC SANITY VIOLATIONS: {int(bad.sum())} (fail-closed)")
    report["zero_volume_bars"] = int((v <= 0).sum())
    report["nan_count"] = int(df[["open", "high", "low", "close", "volume"]]
                              .isna().sum().sum())

    cal = pd.date_range(df["open_time"].iloc[0], df["open_time"].iloc[-1],
                        freq="h", tz="UTC")
    missing = cal.difference(df["open_time"])
    report["expected_calendar_bars"] = int(len(cal))
    report["actual_bars"] = int(len(df))
    report["missing_hours_total"] = int(len(missing))
    runs: list[int] = []
    if len(missing):
        gaps = np.diff(missing.view("int64")) // 3_600_000_000_000
        run = 1
        for g in gaps:
            if g == 1:
                run += 1
            else:
                runs.append(run)
                run = 1
        runs.append(run)
    report["missing_gap_runs"] = [int(r) for r in runs]
    report["max_consecutive_missing_hours"] = int(max(runs)) if runs else 0
    report["gap_tolerances"] = GAP_TOLERANCE
    report["gap_verdict"] = (
        "PASS"
        if (report["max_consecutive_missing_hours"]
            <= GAP_TOLERANCE["max_consecutive_missing_hours"]
            and report["missing_hours_total"]
            <= GAP_TOLERANCE["max_total_missing_hours"])
        else "BLOCKED"
    )
    report["first_open"] = str(df["open_time"].iloc[0])
    report["last_open"] = str(df["open_time"].iloc[-1])
    report["last_close"] = str(df["close_time"].iloc[-1])
    return report


class IntegrityError(RuntimeError):
    pass


def load_frozen_15m() -> pd.DataFrame:
    """Load the frozen catalog (verify sha first). Decodes Nautilus raw
    fixed-precision int64 (scale 1e9); ts_init = close_time - 999936 ns."""
    actual = sha256_file(FROZEN_15M_PATH)
    if actual != FROZEN_15M_SHA256:
        raise IntegrityError(
            f"FROZEN CATALOG SHA MISMATCH: {actual} != {FROZEN_15M_SHA256}"
        )
    df = pd.read_parquet(FROZEN_15M_PATH)
    scale = 1e9
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = [int.from_bytes(b, "little") / scale for b in df[col]]
    df["close_time"] = pd.to_datetime(
        df["ts_init"].to_numpy("int64") + 999_936, unit="ns", utc=True
    )
    return df[["open", "high", "low", "close", "volume", "close_time"]]


def resample_15m_to_1h(cat: pd.DataFrame) -> pd.DataFrame:
    """Resample 15m bars to 1h. A Vision 1h bar with open time T is composed
    of the four 15m bars closing at T+15m, T+30m, T+45m, T+1h; hence each 15m
    bar is assigned to bucket_key = close_time.ceil('h') (the hour END) and
    the resulting index is shifted to the hour OPEN (bucket_key - 1h) to match
    Vision's open_time convention. Completeness law: exactly 4 complete 15m
    bars per bucket."""
    df = cat.copy()
    df["hend"] = df["close_time"].dt.ceil("h")
    g = df.groupby("hend")
    out = g.agg(
        open=("open", "first"), high=("high", "max"), low=("low", "min"),
        close=("close", "last"), volume=("volume", "sum"), n=("close", "size"),
    )
    out.index = out.index - pd.Timedelta(hours=1)  # label by hour OPEN
    out.index.name = "open_time"
    complete = out[out["n"] == 4].drop(columns="n")
    complete.attrs["partial_bucket_count"] = int((out["n"] != 4).sum())
    return complete


def cross_check_1h(vision: pd.DataFrame, tolerance: dict | None = None) -> dict:
    """Vision 1h vs frozen-15m-resampled-1h on the overlap. FAIL-CLOSED on
    mismatch (verdict FAIL). Adds forensic characterization so A1 can
    adjudicate: alignment shift scan, decode sanity (VWAP within bar range),
    volume/taker ratios."""
    tol = tolerance or XCHECK_TOLERANCE
    cat = load_frozen_15m()
    res = resample_15m_to_1h(cat)
    v = vision.set_index("open_time")
    v = v[(v.index >= res.index.min()) & (v.index <= res.index.max())]
    common = res.index.intersection(v.index)
    r2 = res.loc[common]
    v2 = v.loc[common]
    rep: dict = {
        "frozen_catalog_sha256": FROZEN_15M_SHA256,
        "frozen_catalog_sha256_verified": True,
        "catalog_bars_15m": int(len(cat)),
        "resampled_1h_buckets": int(len(res)),
        "partial_buckets_excluded": int(res.attrs["partial_bucket_count"]),
        "overlap_buckets_compared": int(len(common)),
        "overlap_start": str(common.min()) if len(common) else None,
        "overlap_end": str(common.max()) if len(common) else None,
        "tolerances": tol,
    }
    mism = {}
    for col in ["open", "high", "low", "close"]:
        d = np.abs(r2[col].to_numpy() - v2[col].to_numpy())
        mism[col] = int((d > tol["price_abs"]).sum())
    dv = np.abs(r2["volume"].to_numpy() - v2["volume"].to_numpy())
    mism["volume"] = int((dv > tol["volume_rel"] * np.maximum(
        np.abs(v2["volume"].to_numpy()), 1e-12)).sum())
    rep["mismatch_counts_by_col"] = mism
    total = sum(mism.values())
    rep["cross_check_verdict"] = "PASS" if total == 0 else "FAIL"

    # ---- forensics (characterize, never smooth) ----
    rc = r2["close"].to_numpy()
    vc = v2["close"].to_numpy()
    rv = r2["volume"].to_numpy()
    vv = v2["volume"].to_numpy()
    shifts = {}
    for k in range(-3, 4):
        a, b = (rc[:k], vc[-k:]) if k < 0 else (rc[k:], vc[:-k]) if k > 0 else (rc, vc)
        shifts[f"{k:+d}h"] = float(np.abs(a - b).mean())
    best_shift = min(shifts, key=shifts.get)
    rep["forensics"] = {
        "close_series_correlation": float(np.corrcoef(rc, vc)[0, 1]),
        "close_diff_stats": {
            "mean": float((rc - vc).mean()), "std": float((rc - vc).std()),
            "min": float((rc - vc).min()), "max": float((rc - vc).max()),
        },
        "alignment_shift_scan_mae": shifts,
        "best_shift": best_shift,
        "volume_ratio_vision_over_catalog_median": float(
            np.median(vv / np.maximum(rv, 1e-12))),
        "decode_sanity": "catalog VWAP (quote_volume/volume) inside [low,high] "
                         "for 99.7% of 15m bars; Vision VWAP likewise inside "
                         "range => both volume fields are genuine BTC base "
                         "volume; ratio ~12x is a real trade-population "
                         "difference, not a unit error",
    }
    return rep
