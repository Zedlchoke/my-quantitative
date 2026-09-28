"""DT100 data loaders: Binance Vision zips, Dukascopy M1 BID/ASK, premium zips.

Read-only against source worktrees (append-only evidence of other cycles);
staging manifest hashes every consumed source file.
"""
from __future__ import annotations

import hashlib
import io
import json
import lzma
import os
import struct
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
                raw = fh.read()
        df = pd.read_csv(io.BytesIO(raw), header=None, low_memory=False)
        if df.empty:
            continue
        first = str(df.iloc[0, 0])
        if not first.isdigit():          # newer zips carry a header row
            df = pd.read_csv(io.BytesIO(raw), header=0, low_memory=False)
            df = df.iloc[:, :min(df.shape[1], len(_BIN_COLS))]
        df.columns = _BIN_COLS[:df.shape[1]]
        frames.append(df)
    out = pd.concat(frames, ignore_index=True, sort=False)
    out["open_time"] = pd.to_numeric(out["open_time"]).astype("int64")
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


def _load_duka_side(side_dir: str, scale: float) -> pd.DataFrame:
    """Dukascopy day M1 candle .bi5 files -> [ts,o,h,l,c,vol].

    Layout VERIFIED empirically by EURUSD-OPEN-SEARCH-V1 probe 2026-09-23
    (scripts/duka_lib.py, reused verbatim semantics): LZMA container, 24-byte
    big-endian records >5if = (sec_offset_in_day, open, close, low, high, vol),
    prices in integer points scaled by `scale` (1e5 for 5-digit pairs, 1e3 JPY).
    """
    files = sorted(Path(side_dir).glob("*.bi5"))
    if not files:
        raise FileNotFoundError(f"no .bi5 day files in {side_dir}")
    recs = []
    for fp in files:
        day = fp.stem
        plain = lzma.decompress(fp.read_bytes())
        if len(plain) % 24:
            raise ValueError(f"bi5 candle payload not multiple of 24: {fp}")
        for i in range(len(plain) // 24):
            sec, o, c, l, h, vol = struct.unpack_from(">5if", plain, 24 * i)
            recs.append((f"{day}T{sec // 3600:02d}:{(sec // 60) % 60:02d}:00",
                         o / scale, h / scale, l / scale, c / scale, float(vol)))
    side = pd.DataFrame(recs, columns=["ts_str", "o", "h", "l", "c", "vol"])
    side["ts"] = pd.to_datetime(side["ts_str"], utc=True)
    return side[["ts", "o", "h", "l", "c", "vol"]] \
        .sort_values("ts").drop_duplicates("ts").reset_index(drop=True)


def load_fx_pair(bid_dir: str, ask_dir: str, scale: float) -> pd.DataFrame:
    """BID+ASK M1 day files -> [ts,o,h,l,c,v,tb,spread_bps].

    o/h/l/c = mid of the two sides' candles; spread measured per bar from the
    two CLOSEs (the quantity the cost bill charges per fill).
    """
    key = bid_dir
    if key in _CACHE:
        return _CACHE[key]
    bid = _load_duka_side(bid_dir, scale).rename(
        columns={"o": "bo", "h": "bh", "l": "bl", "c": "bc", "vol": "v"})
    ask = _load_duka_side(ask_dir, scale).rename(
        columns={"o": "ao", "h": "ah", "l": "al", "c": "ac"})
    m = bid.merge(ask, on="ts", how="inner")
    m = m[(m["bc"] > 0) & (m["ac"] >= m["bc"])].reset_index(drop=True)
    out = pd.DataFrame({
        "ts": m["ts"],
        "o": (m["bo"] + m["ao"]) / 2, "h": (m["bh"] + m["ah"]) / 2,
        "l": (m["bl"] + m["al"]) / 2, "c": (m["bc"] + m["ac"]) / 2,
        "v": m["v"], "tb": np.nan,
        "spread_bps": (m["ac"] - m["bc"]) / ((m["ac"] + m["bc"]) / 2) * 1e4,
    })
    _CACHE[key] = out
    return out


def load_quarterly_continuous(dirname: str, roll_days: int = 30) -> pd.DataFrame:
    """Continuous quarterly-futures 1m series: at each minute, the nearest
    quarterly contract with >= roll_days to expiry (then roll to the next).
    Symbols are BTCUSDT_YYMMDD named by last-Friday expiry. Minutes where no
    contract satisfies the rule are dropped (honest gaps, never interpolated).
    """
    import re
    files = sorted(Path(dirname).glob("*.zip"))
    if not files:
        raise FileNotFoundError(f"no quarterly zips in {dirname}")
    by_sym: dict[str, pd.DataFrame] = {}
    for zp in files:
        m = re.match(r"(BTCUSDT_\d{6})-1m-", zp.name)
        if not m:
            continue
        sym = m.group(1)
        with zipfile.ZipFile(zp) as z:
            with z.open(z.namelist()[0]) as fh:
                df = pd.read_csv(io.BytesIO(fh.read()), header=None,
                                 names=_BIN_COLS, low_memory=False)
        if len(df) and not str(df.iloc[0, 0]).isdigit():
            df = df.iloc[1:]
        df = df[["open_time", "open", "high", "low", "close", "volume", "taker_buy_base"]]
        df.columns = ["open_time", "o", "h", "l", "c", "v", "tb"]
        for col in ("open_time", "o", "h", "l", "c", "v", "tb"):
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.dropna(subset=["open_time", "o", "c"])
        by_sym.setdefault(sym, []).append(df)
    frames = []
    for sym, lst in by_sym.items():
        d = pd.concat(lst, ignore_index=True).drop_duplicates("open_time")
        d["ts"] = pd.to_datetime(pd.to_numeric(d["open_time"]), unit="ms", utc=True)
        d["expiry"] = pd.Timestamp(f"20{sym[-6:-4]}-{sym[-4:-2]}-{sym[-2:]}", tz="UTC")
        frames.append(d[["ts", "o", "h", "l", "c", "v", "tb", "expiry"]])
    allq = pd.concat(frames, ignore_index=True).sort_values("ts").reset_index(drop=True)
    allq["dte"] = (allq["expiry"] - allq["ts"]).dt.total_seconds() / 86400
    # nearest expiry among contracts with dte >= roll_days (per minute)
    ok = allq[allq["dte"] >= roll_days]
    ok = ok.sort_values(["ts", "dte"])
    cont = ok.groupby("ts", as_index=False).first()
    return cont[["ts", "o", "h", "l", "c", "v", "tb"]]


def aggregate(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Aggregate 1m -> higher timeframe (e.g. '1h'). First open, last close."""
    g = df.set_index("ts").resample(rule)
    out = pd.DataFrame({
        "o": g["o"].first(), "h": g["h"].max(), "l": g["l"].min(),
        "c": g["c"].last(), "v": g["v"].sum(), "tb": g["tb"].sum(),
    }).dropna(subset=["o", "c"]).reset_index()
    return out
