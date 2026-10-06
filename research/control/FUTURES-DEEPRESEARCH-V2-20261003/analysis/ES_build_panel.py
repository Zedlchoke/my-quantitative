#!/usr/bin/env python
"""ES deep-research v2 — panel builder (lane DEEP-ES, task FUTURES-DEEPRESEARCH-V2-20261003).

DESCRIPTIVE ONLY: no PnL, no strategy returns, no parameter selection, no
conditional mean-return tables. Thresholds use strict past/trailing windows.

Builds from the vendor ohlcv-1m per-contract parquet (read-only):
  ~/.my-quantitative-data/futures-databento-av1trim/parquet/
      AV1R-O1M-ES-DELTA/*.parquet  (2010-06-06 -> 2023-10-01, delta backfill)
      AV1T-O1M-ES/*.parquet        (2023-10-01 -> 2026-10-01)
plus definitions parquet (AV1T-definition-ALL10, 2023-10+) for exact expiries.

Outputs (all under analysis/ES_cache/):
  es_1m_outright.parquet  all outright quarterly-contract 1m bars (int nanos),
                          keyed instrument_id (unique per contract, immune to
                          decade-repeated symbols e.g. ESH0=2010 vs ESH0=2020)
  es_contracts.json       per-contract metadata: symbol, first/last session,
                          observed last-trade session, delivery month, expiry
                          (definitions where available, else naive 3rd Friday),
                          data-quality counters
  es_stats OI/statistics daily table extracted from statistics parquet
                          (stat_type 9 = open interest, 6 = cleared volume;
                          2023-10+ only)

Conventions (exchange tz = America/Chicago, DST-correct via tz database):
  session_date d = the Chicago calendar day containing 08:30-16:00; minutes at
  Chicago time >= 17:00 belong to the NEXT session date. RTH = [08:30,16:00)
  Chicago (IBKR "liquid hours" / v1 convention). NY-cash hours = [08:30,15:00).
  Overnight = [17:00,08:30). Maintenance = [16:00,17:00).

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python ES_build_panel.py
"""
import glob
import json
import os
import re
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "ES_cache")
os.makedirs(CACHE, exist_ok=True)

VENDOR = os.path.expanduser(
    "~/my-quantitative-data/futures-databento-av1trim/parquet")
OHLCV_DIRS = [
    os.path.join(VENDOR, "AV1R-O1M-ES-DELTA"),
    os.path.join(VENDOR, "AV1T-O1M-ES"),
]
DEF_DIR = os.path.join(VENDOR, "AV1T-definition-ALL10")
STAT_DIR = os.path.join(VENDOR, "AV1T-statistics-ALL10")

OUTRIGHT_RE = re.compile(r"^ES[HMUZ][0-9]$")
MONTH_CODE = {"H": 3, "M": 6, "U": 9, "Z": 12}
NS = 1_000_000_000


def chicago(ts_ns: pd.Series) -> pd.Series:
    return pd.DatetimeIndex(pd.to_datetime(ts_ns, unit="ns", utc=True)) \
        .tz_convert("America/Chicago")


def session_dates_from_chicago(chi):
    """Chicago-local DatetimeIndex -> DatetimeIndex of session dates
    (minutes at/after 17:00 Chicago belong to the NEXT session date)."""
    midnight = chi.normalize()
    roll = pd.to_timedelta((chi.hour >= 17).astype("int64"), unit="D")
    return midnight + roll


def third_friday(year: int, month: int) -> date:
    d = date(year, month, 1)
    # weekday(): Mon=0..Fri=4; first Friday
    first_fri = d + timedelta(days=(4 - d.weekday()) % 7)
    return first_fri + timedelta(days=14)


# ---------------------------------------------------------------- load ohlcv
frames = []
files = []
for dd in OHLCV_DIRS:
    files += sorted(glob.glob(os.path.join(dd, "*.parquet")))
print(f"loading {len(files)} ohlcv chunk files")
for fp in files:
    t = pq.read_table(fp)
    df = t.to_pandas()
    df = df[df["raw_symbol"].str.match(OUTRIGHT_RE)]
    frames.append(df[["instrument_id", "raw_symbol", "ts_event",
                      "open", "high", "low", "close", "volume"]])
m = pd.concat(frames, ignore_index=True)
del frames
print("outright quarterly 1m rows:", len(m), "contracts:", m["instrument_id"].nunique())

# de-duplicate on (instrument_id, ts_event): vendor may overlap chunk edges
dup = m.duplicated(subset=["instrument_id", "ts_event"], keep="first")
n_dup = int(dup.sum())
if n_dup:
    m = m[~dup]
print("duplicate (instrument_id, ts_event) rows dropped:", n_dup)

# sanity: price scale + negative prices (none expected for ES)
neg = int(((m[["open", "high", "low", "close"]] < 0).any(axis=1)).sum())
ohlc_bad = int(((m["high"] < m[["open", "low", "close"]].max(axis=1)) |
                (m["low"] > m[["open", "high", "close"]].min(axis=1))).sum())
print("negative-price bars:", neg, "| OHLC-inconsistent bars:", ohlc_bad)

m.to_parquet(os.path.join(CACHE, "es_1m_outright.parquet"), index=False)

# ------------------------------------------------------- contract metadata
DATA_END = None  # filled after first pass; contracts still active at data end
contracts = {}
for iid, g in m.groupby("instrument_id"):
    sym = g["raw_symbol"].iloc[0]
    chi = chicago(g["ts_event"])
    sess_dates = session_dates_from_chicago(chi)
    last_sess = sess_dates.max()
    first_sess = sess_dates.min()
    contracts[int(iid)] = {
        "instrument_id": int(iid),
        "symbol": sym,
        "_last_sess": last_sess.date(),
        "first_session": first_sess.date().isoformat(),
        "last_session": last_sess.date().isoformat(),
        "n_bars": int(len(g)),
        "volume_total": int(g["volume"].sum()),
    }

# delivery year: contract EXPIRED inside the data window -> year of its last
# session (ES quarterlies trade until the 3rd Friday of the delivery month
# itself; verified above). Contract still listed at data end -> definitions
# expiry if present, else the symbol-decade candidate that lies in the future.
DATA_END = max(c["_last_sess"] for c in contracts.values())
for c in contracts.values():
    mm = MONTH_CODE[c["symbol"][2]]
    if c["_last_sess"] < (DATA_END - timedelta(days=7)):
        yy = c["_last_sess"].year          # expired: last trade == delivery month
        c["still_listed"] = False
    else:
        c["still_listed"] = True
        digit = int(c["symbol"][3])
        cands = [2010 + digit, 2020 + digit, 2030 + digit]
        future = [y for y in cands if (y, mm) >= (DATA_END.year, DATA_END.month)]
        yy = min(future) if future else max(cands)
    c["delivery"] = f"{yy:04d}-{mm:02d}"
    c["naive_third_friday"] = third_friday(yy, mm).isoformat()

# definitions expiries (2023-10+): authoritative (dedupe repeated A-actions)
def_files = sorted(glob.glob(os.path.join(DEF_DIR, "*.parquet")))
def_rows = []
for fp in def_files:
    t = pq.read_table(fp).to_pandas()
    t = t[t["raw_symbol"].str.match(OUTRIGHT_RE)]
    def_rows.append(t)
dd = pd.concat(def_rows, ignore_index=True) if def_rows else pd.DataFrame()
n_def = 0
if len(dd):
    dd = dd[dd["action"] == "A"]
    for iid, g in dd.groupby("instrument_id"):
        iid = int(iid)
        if iid not in contracts:
            continue
        r = g.iloc[-1]
        exp = pd.to_datetime(r["expiration"], unit="ns", utc=True) \
            .tz_convert("America/Chicago")
        contracts[iid]["definition_expiration"] = exp.isoformat()
        if pd.notna(r.get("min_price_increment")):
            contracts[iid]["min_price_increment_raw"] = float(
                r["min_price_increment"])
        n_def += 1
print("contracts with definition expiration:", n_def, "of", len(contracts))

# definitions expiry is authoritative for delivery assignment (fixes barely-
# trading deferred contracts whose own last-print date precedes data end)
for c in contracts.values():
    de = c.get("definition_expiration")
    if de:
        dt = pd.Timestamp(de)
        c["delivery"] = f"{dt.year:04d}-{dt.month:02d}"
        c["naive_third_friday"] = third_friday(dt.year, dt.month).isoformat()
        c["still_listed"] = (c["_last_sess"] >= (DATA_END - timedelta(days=7))
                             or dt.date() > DATA_END)

# last observed TRADE (volume>0 bar) vs last session with any bar
for iid, g in m.groupby("instrument_id"):
    gv = g[g["volume"] > 0]
    if len(gv) == 0:
        contracts[int(iid)]["last_volume_session"] = None
        continue
    chi = chicago(gv["ts_event"])
    sess = session_dates_from_chicago(chi)
    contracts[int(iid)]["last_volume_session"] = sess.max().date().isoformat()

with open(os.path.join(CACHE, "es_contracts.json"), "w") as f:
    json.dump({"generated_utc": datetime.utcnow().isoformat() + "+00:00",
               "n_contracts": len(contracts),
               "n_duplicate_rows_dropped": n_dup,
               "n_negative_price_bars": neg,
               "n_ohlc_inconsistent_bars": ohlc_bad,
               "contracts": sorted(
                   ({k: v for k, v in c.items() if k != "_last_sess"}
                    for c in contracts.values()),
                   key=lambda c: c["delivery"])}, f, indent=1)
print("contracts written:", len(contracts))

# ------------------------------------------------- statistics -> daily OI
stat_files = sorted(glob.glob(os.path.join(STAT_DIR, "*.parquet")))
rows = []
for fp in stat_files:
    t = pq.read_table(fp).to_pandas()
    t = t[t["raw_symbol"].str.match(OUTRIGHT_RE)]
    t = t[t["stat_type"].isin((6, 9))]           # cleared volume, open interest
    rows.append(t)
st = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
if len(st):
    st["ref_date"] = pd.to_datetime(st["ts_ref"], unit="ns", utc=True) \
        .dt.tz_convert("America/Chicago").dt.date
    st["pub_ts"] = pd.to_datetime(st["ts_event"], unit="ns", utc=True)
    st = st[st["update_action"] == 1]
    st = st.sort_values("pub_ts").groupby(
        ["raw_symbol", "ref_date", "stat_type"], as_index=False).last()
    piv = st.pivot_table(index=["raw_symbol", "ref_date"], columns="stat_type",
                         values="quantity", aggfunc="last").reset_index()
    piv.columns = ["symbol", "ref_date", "cleared_volume", "open_interest"]
    piv.to_parquet(os.path.join(CACHE, "es_statistics_daily.parquet"),
                   index=False)
    print("statistics daily table rows:", len(piv),
          "range:", piv["ref_date"].min(), piv["ref_date"].max())

print("BUILD OK")
