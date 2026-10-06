"""fx_ja shared IO helpers — lane FX-JA-READINESS, FUTURES-SIX-READINESS-20261004.

Read-only over:
  /Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/parquet/
  (raw vendor parquets — NOT the deep-v2 caches, except where explicitly cited).

Laws honored: no git; no PnL/returns (descriptive price/volume/roll mechanics
only); chunked/predicate-filtered parquet reads; missing evidence = NOT_RUN.

Algorithm-provenance note: session attribution + k=5 volume-crossover rule are
re-implemented here (and in 6a_roll_measure.py) from the baseline lane source
  research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/6J_deep_lib.py
  research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/NQ_deep_lib.py
(front_by_volume_crossover / third_wednesday / session_date logic), so every
number produced by this lane is independently re-derived.
"""
from __future__ import annotations

import datetime as dt
import glob
import hashlib
import json
import os
import re

import numpy as np
import pandas as pd

DATA_ROOT = "/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/parquet"
NONPRICE = "/Users/hoangminhlong/.my-quantitative-data/futures-nonprice-10syms"
HERE = os.path.dirname(os.path.abspath(__file__))

CHI = "America/Chicago"
NS = 1_000_000_000
PX_SCALE = 1e-9  # Databento GLBX int-nano price encoding (cited: 6J_deep_lib.py)

MONTH_CODE = {"F": 1, "G": 2, "H": 3, "J": 4, "K": 5, "M": 6,
              "N": 7, "Q": 8, "U": 9, "V": 10, "X": 11, "Z": 12}
CODE_MONTH = {v: k for k, v in MONTH_CODE.items()}
QUARTERS = "HMUZ"

OUTRIGHT_RE = {
    "6J": re.compile(r"^6J([FGHJKMNQUVXZ])(\d)$"),
    "6A": re.compile(r"^6A([FGHJKMNQUVXZ])(\d)$"),
}


def third_wednesday(year: int, month: int) -> dt.date:
    """CME FX delivery: 3rd Wednesday of contract month (copied semantics from
    6J_deep_lib.third_wednesday)."""
    d = dt.date(year, month, 1)
    offset = (2 - d.weekday()) % 7  # Wednesday == 2
    return d + dt.timedelta(days=offset) + dt.timedelta(days=14)


def next_quarter(contract: str) -> str:
    """Next HMUZ quarterly of the chain (6J_deep_lib.next_quarter semantics)."""
    sym, yr = contract.split("_")
    m = MONTH_CODE[sym[2]]
    y = int(yr)
    nxt_m, nxt_y = (m + 3, y) if m < 12 else (3, y + 1)
    return f"{sym[:2]}{CODE_MONTH[nxt_m]}{nxt_y % 10}_{nxt_y}"


def files_for(root: str) -> list[str]:
    return sorted(glob.glob(os.path.join(DATA_ROOT, root, "*.parquet")))


def load_slice(roots: list[str], t0: str, t1: str, sym_re: re.Pattern,
               extra_cols: list[str] | None = None) -> pd.DataFrame:
    """Predicate-filtered union of one or more parquet roots over a UTC window,
    keeping only raw_symbols matching sym_re. Prices stay int-nano ints."""
    cols = ["rtype", "instrument_id", "raw_symbol", "ts_event",
            "open", "high", "low", "close", "volume"]
    if extra_cols:
        cols += [c for c in extra_cols if c not in cols]
    t0n = pd.Timestamp(t0, tz="UTC").value
    t1n = pd.Timestamp(t1, tz="UTC").value
    out = []
    for root in roots:
        for f in files_for(root):
            try:
                d = pd.read_parquet(
                    f, columns=cols,
                    filters=[("ts_event", ">=", t0n), ("ts_event", "<=", t1n)])
            except Exception:
                # file may not cover the window at all
                continue
            if len(d) == 0:
                continue
            d = d[d["raw_symbol"].str.fullmatch(sym_re)]
            if len(d):
                out.append(d)
    if not out:
        return pd.DataFrame(columns=cols)
    df = pd.concat(out, ignore_index=True).sort_values("ts_event").reset_index(drop=True)
    df["dt"] = pd.to_datetime(df["ts_event"], unit="ns", utc=True)
    return df


def add_session(df: pd.DataFrame) -> pd.DataFrame:
    """Trade date = CT date of the 16:00 close (6J_deep_lib.annotate_panel
    semantics: naive CT normalize + integer-day roll at 17:00)."""
    local = df["dt"].dt.tz_convert(CHI)
    naive = local.dt.tz_localize(None)
    roll = (naive.dt.hour >= 17).astype("int64")
    df = df.copy()
    df["session_date"] = (naive.dt.normalize()
                          + pd.to_timedelta(roll, unit="D")).dt.date
    df["ct_minute"] = local.dt.hour * 60 + local.dt.minute
    return df


def session_volumes(df: pd.DataFrame, contract_of) -> pd.DataFrame:
    """Wide (session_date x contract) volume table from an annotated panel.
    contract_of: fn(raw_symbol series, instrument_id series) -> contract keys."""
    d = df.copy()
    d["contract"] = contract_of(d["raw_symbol"], d["instrument_id"])
    return d.pivot_table(index="session_date", columns="contract",
                         values="volume", aggfunc="sum").sort_index()


def k5_chain(wide: pd.DataFrame, k: int = 5) -> pd.DataFrame:
    """Baseline k=5 volume-crossover held rule, re-implemented verbatim from
    6J_deep_lib.front_by_volume_crossover / NQ_deep_lib (same algorithm family):
    hold quarterly c until next_quarter(c) has trailing-k-session mean volume
    > c's (stale means persist through missing sessions; NaN current volume on
    a ceased contract forces a switch via the pd.isna(cur_v) branch — this is
    the baseline CODE behavior, disclosed as erratum m-5 in 6J_DEEP_v2.md §1)."""
    qcols = [c for c in wide.columns
             if re.fullmatch(r"6[A-Z][HMUZ]\d_\d{4}", str(c))]
    w = wide[qcols]
    roll = w.rolling(k, min_periods=1).mean()
    state = None
    held = []
    for d in roll.index:
        row = roll.loc[d].dropna()
        row = row[row > 0]
        if state is None:
            state = row.idxmax()
        else:
            nxt = next_quarter(state)
            if nxt in row.index:
                cur_v = row.get(state, np.nan)
                if pd.isna(cur_v) or row[nxt] > cur_v:
                    state = nxt
        held.append(state)
    return pd.DataFrame({"session_date": roll.index, "held": held})


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _san(o):
    if isinstance(o, dict):
        return {str(k): _san(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_san(v) for v in o]
    if isinstance(o, (float, np.floating)):
        return float(o) if np.isfinite(o) else None
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (pd.Timestamp, dt.date, dt.datetime)):
        return str(o)
    if isinstance(o, np.ndarray):
        return _san(o.tolist())
    return o


def jdump(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(_san(obj), fh, indent=1, allow_nan=False)
    print("wrote", path)
