#!/usr/bin/env python
"""A2 funding history (Task 3 input) — decode ALL Vision monthly fundingRate
files for BTCUSDT (2020-01..2026-08, 80 files, ~900 bytes each) + one REST
page for 2019-09..2019-12 (archive gap). Computes descriptive per-8h funding
stats and the split WITHIN vs OUTSIDE the census DOWNTREND windows.
Descriptive only: no strategy PnL, no costs application, no tuning.
"""
from __future__ import annotations

import hashlib
import io
import json
import time
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "funding_events.parquet"
SPLIT = HERE / "funding_in_downtrend.json"


def month_add(ym, k):
    y, m = int(ym[:4]), int(ym[5:7])
    t = y * 12 + (m - 1) + k
    return f"{t // 12:04d}-{t % 12 + 1:02d}"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "a2-recon-probe/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def main():
    rows = []
    sha_by_month = {}
    ym = "2020-01"
    while ym <= "2026-08":
        url = (f"https://data.binance.vision/data/futures/um/monthly/fundingRate/"
               f"BTCUSDT/BTCUSDT-fundingRate-{ym}.zip")
        data = fetch(url)
        sha_by_month[ym] = hashlib_or_none(data)
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            raw = z.read(z.namelist()[0]).decode("utf-8", errors="replace")
        lines = raw.splitlines()
        hdr = lines[0].split(",")
        # header row present iff the FIRST field of line 0 is not numeric
        try:
            float(lines[0].split(",")[0])
            header_present = False
        except ValueError:
            header_present = True
        body = lines[1:] if header_present else lines
        for ln in body:
            parts = ln.split(",")
            rec = dict(zip(hdr, parts))
            rows.append({"calc_time": int(rec["calc_time"]),
                         "funding_interval_hours": rec.get("funding_interval_hours"),
                         "last_funding_rate": float(rec["last_funding_rate"])})
        ym = month_add(ym, 1)
        time.sleep(0.05)

    # archive gap 2019-09..2019-12 via keyless REST (measured available back to 2019-09-10)
    rest_rows = []
    url = ("https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT"
           "&startTime=1568073600000&endTime=1577836799999&limit=1000")
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "a2-recon-probe/1.0"}), timeout=30) as r:
        fr = json.loads(r.read().decode())
    for x in fr:
        rest_rows.append({"calc_time": int(x["fundingTime"]),
                          "funding_interval_hours": "8",
                          "last_funding_rate": float(x["fundingRate"])})
    print(f"archive months rows: {len(rows)}, rest 2019 rows: {len(rest_rows)}")

    df = pd.DataFrame(rows + rest_rows).sort_values("calc_time").reset_index(drop=True)
    df["ts"] = pd.to_datetime(df["calc_time"], unit="ms", utc=True)
    df.to_parquet(OUT)

    # ---- label mapping from the census ----
    cen = json.loads((HERE / "downtrend_census.json").read_text())
    import sys
    sys.dont_write_bytecode = True
    sys.path.insert(0, "/Users/hoangminhlong/my-quantitative/.worktrees/phase-strategy-v1/"
                       "integration/research/control/phase_strategy_v1/scored")
    import cells  # PSV1 loader (read-only)
    data = cells.load_btc_h4()
    labels = np.asarray([str(x) for x in data["labels"]])
    open_ms = data["open_ms"]
    H4 = 4 * 3600 * 1000
    from pipeline import config as cfg2  # noqa: pipeline pkg registered by load_btc_h4
    W = int(cfg2.WARMUP)
    # map: funding event t -> H4 bucket index in the truncated (window) panel
    idx = np.searchsorted(open_ms, df["calc_time"].to_numpy(), side="right") - 1
    inside = (idx >= 0) & (idx < len(labels))
    lab = np.array(["PRE_WARMUP"] * len(df), dtype=object)
    lab[inside] = labels[idx[inside]]
    df["label_at_bucket"] = lab

    win = df[df["label_at_bucket"] != "PRE_WARMUP"]
    dt = win[win["label_at_bucket"] == "DOWNTREND"]["last_funding_rate"]
    od = win[win["label_at_bucket"] != "DOWNTREND"]["last_funding_rate"]
    allr = win["last_funding_rate"]
    pre = df[df["label_at_bucket"] == "PRE_WARMUP"]["last_funding_rate"]

    def stats(s: pd.Series) -> dict:
        if len(s) == 0:
            return {"n": 0}
        return {
            "n": int(len(s)),
            "mean_per_8h": float(s.mean()),
            "median_per_8h": float(s.median()),
            "min_per_8h": float(s.min()),
            "max_per_8h": float(s.max()),
            "share_negative": float((s < 0).mean()),
            "annualized_mean_pct": float(s.mean() * 3 * 365 * 100),  # 3 events/day
            "cumulative_over_settlements_pct": float(s.sum() * 100),
        }

    by_year = {}
    for y, g in win.groupby(win["ts"].dt.year):
        by_year[str(int(y))] = {
            "mean_per_8h": float(g["last_funding_rate"].mean()),
            "share_negative": float((g["last_funding_rate"] < 0).mean()),
            "n": int(len(g)),
            "mean_in_downtrend": float(g[g["label_at_bucket"] == "DOWNTREND"]["last_funding_rate"].mean())
            if (g["label_at_bucket"] == "DOWNTREND").any() else None,
            "share_neg_in_downtrend": float((g[g["label_at_bucket"] == "DOWNTREND"]["last_funding_rate"] < 0).mean())
            if (g["label_at_bucket"] == "DOWNTREND").any() else None,
        }

    split = {
        "schema": "a2_funding_in_downtrend@1",
        "computed_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data": "Vision monthly fundingRate BTCUSDT 2020-01..2026-08 (80 files, sha256 list in funding_sha256.json) + REST fapi/v1/fundingRate 2019-09-10..2019-12-31 (archive gap fill, measured 2019-09-10 earliest)",
        "funding_event_granularity": "per settlement (8h; funding_interval_hours field confirms 8 for BTCUSDT throughout)",
        "label_mapping": "funding event at calc_time t -> PSV1 frozen phase label of the H4 bucket containing t (bucket open <= t < open+4h); events before post-warmup window marked PRE_WARMUP",
        "window_events": stats(allr),
        "within_downtrend_windows": stats(dt),
        "outside_downtrend_windows": stats(od),
        "pre_warmup_2019": stats(pre),
        "delta_in_minus_out_mean_per_8h": float(dt.mean() - od.mean()) if len(dt) and len(od) else None,
        "by_year": by_year,
        "psv1_frozen_constant_note": "PSV1 config FUNDING_PER_8H = 1.377e-5 (frozen cost assumption); the MEASURED full-sample mean is reported above for feasibility context only — this lane does not retune any constant",
        "outcome_blindness": "descriptive funding statistics only; no strategy PnL or cost-adjusted returns computed",
    }
    SPLIT.write_text(json.dumps(split, indent=2))
    (HERE / "funding_sha256.json").write_text(json.dumps(sha_by_month, indent=2))
    print(json.dumps({k: split[k] for k in ("window_events", "within_downtrend_windows",
                                            "outside_downtrend_windows", "delta_in_minus_out_mean_per_8h",
                                            "pre_warmup_2019")}, indent=2))
    print("WROTE", SPLIT, "and", OUT)


def hashlib_or_none(data: bytes):
    import hashlib
    return hashlib.sha256(data).hexdigest()


if __name__ == "__main__":
    main()
