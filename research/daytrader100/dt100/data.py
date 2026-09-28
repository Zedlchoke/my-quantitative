"""DT100 data loaders: Binance Vision zips, Dukascopy M1 BID/ASK, premium zips.

Read-only against source worktrees (append-only evidence of other cycles);
staging manifest hashes every consumed source file.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from . import config

_CACHE: dict[str, pd.DataFrame] = {}


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def manifest_entry(paths: list[str]) -> dict:
    return {
        "files": len(paths),
        "sha256_all": [_sha256(p) for p in paths] if len(paths) <= 400 else None,
        "sha256_sample": [_sha256(p) for p in paths[:5]] + [_sha256(p) for p in paths[-5:]],
        "names_first": [os.path.basename(p) for p in paths[:3]],
        "names_last": [os.path.basename(p) for p in paths[-3:]],
    }


_BIN_COLS = ["open_time", "open", "high", "low", "close", "volume", "close_time",
             "quote_volume", "count", "taker_buy_base", "taker_buy_quote", "ignore"]


def load_binance_zipdir(dirname: str, resolution: str = "1m") -> pd.DataFrame:
    """Monthly Binance Vision zips -> UTC 1m/1h frame [ts,o,h,l,c,v,tb]."""
    key = dirname
    if key in _CACHE:
        return _CACHE[key]
    files = sorted(Path(dirname).glob("*.zip"))
    if not files:
        raise FileNotFoundError(f"no zips in {dirname}")
    frames = []
    for zp in files:
        with zipfile.ZipFile(zp) as z:
            name = z.namelist()[0]
            with z.open(name) as fh:
                df = pd.read_csv(io.BytesIO(fh.read()), header=None, names=_BIN_COLS)
        frames.append(df)
    out = pd.concat(frames, ignore_index=True)
    out = out.sort_values("open_time").drop_duplicates("open_time").reset_index(drop=True)
    out["ts"] = pd.to_datetime(out["open_time"], unit="ms", utc=True)
    keep = ["ts", "open", "high", "low", "close", "volume", "taker_buy_base"]
    out = out[keep].rename(columns={
        "open": "o", "high": "h", "low": "l", "close": "c",
        "volume": "v", "taker_buy_base": "tb"})
    for col in ("o", "h", "l", "c", "v", "tb"):
        out[col] = out[col].astype(float)
    _CACHE[key] = out
    return out


def load_premium_zipdir(dirname: str) -> pd.DataFrame:
    """premiumIndexKlines zips (same csv layout; open==close==premium index)."""
    df = load_binance_zipdir(dirname)
    return df


def _load_duka_side(side_dir: str) -> pd.DataFrame:
    files = sorted(Path(side_dir).glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"no csv in {side_dir}")
    frames = []
    for fp in files:
        df = pd.read_csv(fp)
        tcol = [c for c in df.columns if "time" in c.lower() or "gmt" in c.lower()][0]
        ccol = [c for c in df.columns if c.lower() == "close"][0]
        frames.append(pd.DataFrame({"ts_str": df[tcol], "px": df[ccol].astype(float)}))
    side = pd.concat(frames, ignore_index=True)
    side["ts"] = pd.to_datetime(side["ts_str"], utc=True, format="mixed", dayfirst=True)
    return side[["ts", "px"]].sort_values("ts").drop_duplicates("ts").reset_index(drop=True)


def load_fx_pair(bid_dir: str, ask_dir: str) -> pd.DataFrame:
    """Dukascopy M1 BID+ASK day CSVs -> [ts,o,h,l,c,v,tb,spread_bps].

    o/h/l/c built from MID of bid/ask closes per minute (conservative: OHLC from
    closes; intraday families here are close/open-driven, and fills use the
    measured per-bar half-spread which is the quantity that matters for cost).
    """
    key = bid_dir
    if key in _CACHE:
        return _CACHE[key]
    bid = _load_duka_side(bid_dir).rename(columns={"px": "bid"})
    ask = _load_duka_side(ask_dir).rename(columns={"px": "ask"})
    m = bid.merge(ask, on="ts", how="inner")
    m = m[(m["bid"] > 0) & (m["ask"] >= m["bid"])].reset_index(drop=True)
    m["c"] = (m["bid"] + m["ask"]) / 2.0
    m["o"] = m["c"].shift(1).fillna(m["c"])
    m["h"] = m[["o", "c"]].max(axis=1)
    m["l"] = m[["o", "c"]].min(axis=1)
    m["v"] = 0.0
    m["tb"] = np.nan
    m["spread_bps"] = ((m["ask"] - m["bid"]) / m["c"]) * 1e4
    out = m[["ts", "o", "h", "l", "c", "v", "tb", "spread_bps"]]
    _CACHE[key] = out
    return out


def aggregate(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Aggregate 1m -> higher timeframe (e.g. '1h'). First open, last close."""
    g = df.set_index("ts").resample(rule)
    out = pd.DataFrame({
        "o": g["o"].first(), "h": g["h"].max(), "l": g["l"].min(),
        "c": g["c"].last(), "v": g["v"].sum(), "tb": g["tb"].sum(),
    }).dropna(subset=["o", "c"]).reset_index()
    return out
