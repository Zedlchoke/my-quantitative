"""6A deep-research v2 shared library — lane DEEP-6A, task FUTURES-DEEPRESEARCH-V2-20261003.

Loads the Databento av1trim 6A ohlcv-1m panel (2020-01-01..2026-10-01, the union of
AV1B-O1M-6A-BACKFILL2 / AV1R-O1M-6A-BACKFILL / AV1T-O1M-6A), keeps OUTRIGHT bars
(raw_symbol without '-'; calendar-spread instruments carry negative prices and are
NEVER mixed into price-behavior stats), builds the per-contract registry with the
CME FX delivery frame (3rd Wednesday of delivery month), and provides DST-correct
session/hub-local clocks (exchange America/Chicago; hubs Australia/Sydney,
Asia/Tokyo, Asia/Shanghai, Europe/London).

Laws honored (dispatch DISPATCH_MANIFEST.json):
  * No PnL evaluation, no signal selection; descriptive only. No conditional
    mean-return event tables.
  * No vendor-stitched continuous series: held-contract chains are built here
    from per-contract bars with explicit, declared, PIT-legal selection rules.
  * Every threshold used inside analyses is strict-past/rolling.
"""
from __future__ import annotations

import datetime as dt
import glob
import json
import os
import re

import numpy as np
import pandas as pd

DATA_ROOT = "/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim"
NONPRICE = "/Users/hoangminhlong/.my-quantitative-data/futures-nonprice-10syms"
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "6A_cache")

CHI = "America/Chicago"
SYD = "Australia/Sydney"
SHA = "Asia/Shanghai"
TYO = "Asia/Tokyo"
LON = "Europe/London"

NS = 1_000_000_000
PRICE_SCALE = 1_000_000_000          # Databento fixed point: 703300000 -> 0.7033 USD/AUD
TICK = 50_000                        # 1 tick in fixed point = 5e-05 USD/AUD = $5.00
MULT = 100_000.0                     # AUD 100,000 per contract

MONTH_CODE = {  # 6A lists all 12 serial months
    "F": 1, "G": 2, "H": 3, "J": 4, "K": 5, "M": 6,
    "N": 7, "Q": 8, "U": 9, "V": 10, "X": 11, "Z": 12,
}
CODE_MONTH = {v: k for k, v in MONTH_CODE.items()}
QUARTERLY = "HMUZ"

# Session template (measured on this panel: bars 2020-01-02..2026-10-01; exactly
# ONE bar ever lands in the 16:00-17:00 CT maintenance window; Sunday sessions
# start 17:00 CT). Trade date D runs 17:00 CT on D-1 through 16:00 CT on D.
SESSION_FULL_MIN = 23 * 60 - 60      # 1320 tradable minutes/day (60-min break)

# CT-clock partition segments (exchange clock; DST-correct via tz_convert).
# 'ev'/'on' belong to the session date D (17:00 D-1 .. 07:00 D).
CT_SEGMENTS = [
    ("ev_apac_open", 17 * 60, 24 * 60),   # D-1 17:00-24:00 CT (Sydney/Tokyo morning of D)
    ("on_asia", 0 * 60, 6 * 60),          # D 00:00-06:00 CT (Asia afternoon/evening)
    ("on_sydney_close_london_open", 6 * 60, 8 * 60),  # D 06:00-08:00 CT
    ("us_data_block", 7 * 60, 8 * 60 + 30),           # D 07:00-08:30 CT (US releases 07:30 CT)
    ("rth_open30", 8 * 60 + 30, 9 * 60),
    ("rth_morning", 9 * 60, 11 * 60 + 30),
    ("rth_lunch", 11 * 60 + 30, 13 * 60 + 30),
    ("rth_afternoon", 13 * 60 + 30, 15 * 60),
    ("settle_tail", 15 * 60, 16 * 60),
]

OUTRIGHT_RE = re.compile(r"^6A([FGHJKMNQUVXZ])(\d)$")


def source_files() -> list[str]:
    files = []
    for line in ["AV1B-O1M-6A-BACKFILL2", "AV1R-O1M-6A-BACKFILL", "AV1T-O1M-6A"]:
        files += sorted(glob.glob(f"{DATA_ROOT}/parquet/{line}/*.parquet"))
    if not files:
        raise FileNotFoundError("no 6A parquet files under DATA_ROOT/parquet/")
    return files


def load_raw_6a() -> pd.DataFrame:
    df = pd.concat([pd.read_parquet(f) for f in source_files()], ignore_index=True)
    df["dt"] = pd.to_datetime(df["ts_event"], unit="ns", utc=True)
    return df.sort_values(["raw_symbol", "dt"]).reset_index(drop=True)


# ----------------------------------------------------------------------------
# Registry: outright symbol clusters -> contract identity (year resolution)
# ----------------------------------------------------------------------------

def third_wednesday(year: int, month: int) -> dt.date:
    d = dt.date(year, month, 1)
    offset = (2 - d.weekday()) % 7      # Wednesday == 2
    first_wed = d + dt.timedelta(days=offset)
    return first_wed + dt.timedelta(days=14)


def build_registry(outr: pd.DataFrame, definitions: pd.DataFrame | None = None) -> pd.DataFrame:
    """One row per outright CONTRACT (grouped by instrument_id — vendor GLBX ids
    are global and stable across files, unlike decade-ambiguous raw_symbols).

    Identity resolution, in order:
      1. vendor definition (2023-10+ window): maturity_year/maturity_month by
         instrument_id (authoritative);
      2. containment vs the CME FX delivery frame (3rd Wednesday anchor; legal
         last trade ~09:16 CT 2nd business days before it; listing window up
         to 30 months) on the instrument's MAIN (max-total-volume) cluster.
    Clusters outside the resolved frame with negligible volume (pre-activation
    vendor prints, e.g. instrument 7084 '6AM5' printed 2020-01..05 before its
    2020-06-15 activation) are demoted to recorded strays, never silently
    merged. Definitions cross-check is reported (matches + mismatches).
    """
    deflut = {}
    if definitions is not None:
        defs = (definitions[definitions["raw_symbol"].str.fullmatch(r"6A[FGHJKMNQUVXZ]\d")]
                [["instrument_id", "maturity_year", "maturity_month"]]
                .drop_duplicates())
        for r in defs.itertuples():
            deflut.setdefault(int(r.instrument_id),
                              (int(r.maturity_year), int(r.maturity_month)))

    rows = []
    for iid, sub in outr.groupby("instrument_id", sort=False):
        syms = sub["raw_symbol"].unique()
        if len(syms) != 1:
            raise ValueError(f"instrument {iid} maps to multiple raw symbols {syms}")
        sym = syms[0]
        m = OUTRIGHT_RE.fullmatch(sym)
        if m is None:
            continue
        code, digit = m.group(1), int(m.group(2))
        ts = sub["dt"].sort_values().reset_index(drop=True)
        breaks = ts.diff() > pd.Timedelta(days=45)
        sub = sub.assign(_cluster=breaks.cumsum().values)
        clusters = []
        for cid, grp in sub.groupby("_cluster"):
            clusters.append({"cid": int(cid), "grp": grp,
                             "t0": grp["dt"].min(), "t1": grp["dt"].max(),
                             "vol": float(grp["volume"].sum())})
        main = max(clusters, key=lambda c: c["vol"])
        # resolve year
        year = None
        if iid in deflut:
            year, month = deflut[iid]
            if month != MONTH_CODE[code]:
                raise ValueError(f"instrument {iid}: def month {month} != symbol {code}")
        else:
            ok = []
            for y in range(2009, 2030):
                if y % 10 != digit:
                    continue
                tw = pd.Timestamp(third_wednesday(y, MONTH_CODE[code]), tz="UTC")
                lo = tw - pd.DateOffset(months=30)
                hi = tw + pd.Timedelta(days=1)
                if lo <= main["t0"] and main["t1"] <= hi:
                    ok.append(y)
            if len(ok) == 1:
                year = ok[0]
            elif len(ok) == 0 and main["vol"] < 1e4:
                year = None          # negligible unresolved -> whole id stray
            else:
                raise ValueError(
                    f"instrument {iid} {sym} main cluster {main['t0']}..{main['t1']} "
                    f"-> candidate years {ok}")
        stray_clusters = []
        if year is not None:
            tw = pd.Timestamp(third_wednesday(year, MONTH_CODE[code]), tz="UTC")
            lo, hi = tw - pd.DateOffset(months=30), tw + pd.Timedelta(days=1)
            for c in clusters:
                if c is main:
                    continue
                inside = (lo <= c["t0"]) and (c["t1"] <= hi)
                negligible = c["vol"] <= max(1000.0, 0.01 * main["vol"])
                if inside:
                    pass                # same contract with a data gap — keep
                elif negligible:
                    stray_clusters.append(c)   # e.g. pre-activation vendor prints
                else:
                    raise ValueError(
                        f"instrument {iid} {sym}: non-negligible out-of-frame "
                        f"cluster {c['t0']}..{c['t1']} vol {c['vol']}")
        stray = year is None
        rows.append({
            "symbol": sym, "instrument_id": int(iid),
            "contract": (f"{sym}_{year}" if year else f"STRAY_{sym}_{iid}"),
            "month": MONTH_CODE[code], "year": year,
            "is_quarterly": code in QUARTERLY,
            "delivery_month_start": (pd.Timestamp(year=year, month=MONTH_CODE[code], day=1)
                                     if year else pd.NaT),
            "third_wed": (third_wednesday(year, MONTH_CODE[code])
                          if year else None),
            "first_bar": main["t0"], "last_bar": main["t1"],
            "n_bars": int(len(sub)), "total_volume": float(sub["volume"].sum()),
            "identity_source": ("definition" if iid in deflut else "delivery_frame"),
            "stray": stray,
            "n_stray_clusters": len(stray_clusters),
            "stray_clusters": [{"span": [str(c["t0"]), str(c["t1"])],
                                "volume": c["vol"], "bars": int(len(c["grp"]))}
                               for c in stray_clusters],
        })
    reg = pd.DataFrame(rows).sort_values("delivery_month_start",
                                         na_position="last").reset_index(drop=True)
    # cross-check: every definition-mapped id's containment choice
    if definitions is not None:
        mism = []
        for r in reg.itertuples():
            if r.instrument_id in deflut and r.year is not None:
                my, mm = deflut[r.instrument_id]
                if (my, mm) != (int(r.year), int(r.month)):
                    mism.append({"instrument_id": r.instrument_id,
                                 "contract": r.contract,
                                 "def": [my, mm], "registry": [int(r.year), int(r.month)]})
        reg.attrs["def_mismatches"] = mism
    return reg


# ----------------------------------------------------------------------------
# Annotation: session date, exchange clock, hub-local clocks
# ----------------------------------------------------------------------------

def annotate(outr: pd.DataFrame) -> pd.DataFrame:
    local = outr["dt"].dt.tz_convert(CHI)
    hhmm = (local.dt.hour * 60 + local.dt.minute).astype("int32")
    # trade date D: local times >= 17:00 belong to the NEXT calendar day
    # (wall-clock arithmetic: DST-correct via date + int days)
    ndays = local.dt.normalize().values.astype("datetime64[D]")
    ndays = ndays + np.where(local.dt.hour >= 17, 1, 0).astype("int64")
    outr = outr.assign(
        ct_minute=hhmm,
        session_date=pd.Series(pd.DatetimeIndex(ndays).date, index=outr.index),
        in_break=(hhmm >= 16 * 60) & (hhmm < 17 * 60),
        weekend_anomaly=((local.dt.dayofweek == 4) & (hhmm >= 17 * 60))
                        | (local.dt.dayofweek == 5),
    )
    seg = pd.Series("unassigned", index=outr.index, dtype="object")
    for name, a, b in CT_SEGMENTS:
        seg[(hhmm >= a) & (hhmm < b)] = name
    # note: us_data_block overlaps on_sydney_close_london_open by design; last
    # assignment wins for the *column*, but per-window aggregates are computed
    # from hub-local clocks in the analyses, so keep segments as pure partition:
    outr["segment"] = seg
    outr["in_rth"] = ((hhmm >= 8 * 60 + 30) & (hhmm < 15 * 60)).astype(bool)
    return outr


def hub_local(df: pd.DataFrame, tz: str) -> pd.Series:
    """Bar local wall-clock hour:minute (minutes since midnight) in a hub tz."""
    loc = df["dt"].dt.tz_convert(tz)
    return (loc.dt.hour * 60 + loc.dt.minute).astype("int32")


# ----------------------------------------------------------------------------
# PIT held-contract chains (no vendor stitching)
# ----------------------------------------------------------------------------

_QKEY = re.compile(r"^6A[HMUZ]\d_\d{4}$")
_SKEY = re.compile(r"^6A[FGHJKMNQUVXZ]\d_\d{4}$")


def real_contracts(sess: pd.DataFrame) -> pd.DataFrame:
    return sess[sess["contract"].str.match(_SKEY)].copy()


def next_listed(contract: str) -> str | None:
    """Next listed serial month after this contract (FX lists all 12 months)."""
    sym, yr = contract.split("_")
    y, m = int(yr), MONTH_CODE[sym[2]]
    m2, y2 = (m + 1, y) if m < 12 else (1, y + 1)
    return f"6A{CODE_MONTH[m2]}{y2 % 10}_{y2}"


def next_quarterly(contract: str) -> str | None:
    sym, yr = contract.split("_")
    y, m = int(yr), MONTH_CODE[sym[2]]
    while True:
        m, y = (m + 1, y) if m < 12 else (1, y + 1)
        if CODE_MONTH[m] in QUARTERLY:
            return f"6A{CODE_MONTH[m]}{y % 10}_{y}"


def calendar_chain(sess: pd.DataFrame, quarterly_only: bool = True) -> pd.DataFrame:
    """v1 declared rule adapted: hold until the last session BEFORE day-1 of the
    held contract's delivery month; roll at that close to the next listed
    contract (literal) or next HMUZ quarterly (quarterly adaptation).
    Returns session-level frame with held contract per session_date."""
    s = real_contracts(sess)
    contracts = sorted(s["contract"].unique(),
                       key=lambda c: pd.Timestamp(c.split("_")[1] + "-" +
                                                  f"{MONTH_CODE[c[2]]:02d}" + "-01"))
    avail = set(contracts)
    lut = {c: pd.Timestamp(c.split("_")[1] + "-" + f"{MONTH_CODE[c[2]]:02d}" + "-01")
           for c in contracts}
    dates = sorted(s["session_date"].unique())
    dates = pd.to_datetime(pd.Series(dates, dtype="object")).dt.date
    held = []
    cur = contracts[0]
    for d in dates:
        # if d is day-1 of cur's delivery month or later -> roll
        while cur in lut and d >= lut[cur].date():
            nxt = next_quarterly(cur) if quarterly_only else next_listed(cur)
            if nxt is None or nxt not in avail:
                cur = None
                break
            cur = nxt
        held.append(cur)
    out = pd.DataFrame({"session_date": list(dates), "held": held})
    return out.dropna(subset=["held"]).reset_index(drop=True)


# ----------------------------------------------------------------------------
# Non-price loaders
# ----------------------------------------------------------------------------

def load_rba_decisions() -> pd.DataFrame:
    """RBA cash-rate decision table from the archived rba.gov.au gate HTML
    (nonprice corpus, fetched by the acquisition lane). Columns: effective
    date, change (pp), cash rate target (%). Announcement convention:
    decision announced 14:30 Sydney on the Board day; target effective the
    following day -> announcement = effective_date - 1 business day
    (disclosed convention; special meetings checked in A4)."""
    html = open(f"{NONPRICE}/rba/cash_rate_gate.html", encoding="utf-8",
                errors="replace").read()
    rows = re.findall(
        r"<th[^>]*>\s*(\d{1,2} [A-Za-z]+ \d{4})\s*</th>\s*"
        r"<td[^>]*>\s*([+\-]?\d+\.\d+)\s*</td>\s*"
        r"<td[^>]*>\s*(\d+\.\d+)\s*</td>",
        html)
    rec = []
    for d, ch, lvl in rows:
        try:
            ts = dt.datetime.strptime(d, "%d %b %Y")
        except ValueError:
            ts = dt.datetime.strptime(d, "%d %B %Y")
        rec.append({"effective_date": pd.Timestamp(ts),
                    "change_pp": float(ch), "cash_rate_pct": float(lvl)})
    df = pd.DataFrame(rec).drop_duplicates("effective_date").sort_values("effective_date")
    # announcement = previous AU business day at 14:30 Sydney
    ann = []
    for d in df["effective_date"]:
        a = d - pd.offsets.BDay(1)
        ann.append(pd.Timestamp(a.date()))
    df["announcement_date"] = ann
    df["announcement_time_syd"] = "14:30"
    return df.reset_index(drop=True)


def load_fomc() -> pd.DataFrame:
    """FOMC statement events from the archived federalreserve.gov HTML
    (nonprice corpus). release_time_et only where the statement itself carries
    'For release at H:MM a.m./p.m. E[SD]T'."""
    files = sorted(glob.glob(f"{NONPRICE}/fed/statements/monetary*.html"))
    rows = []
    for f in files:
        base = os.path.basename(f)
        m = re.fullmatch(r"monetary(\d{8})a\.html", base)
        if not m:
            continue
        d = pd.Timestamp(m.group(1))
        txt = open(f, encoding="utf-8", errors="replace").read()
        mt = re.search(r"For release at\s*(\d{1,2}):(\d{2})\s*([ap])\.m\.\s*(E[SD]T)", txt)
        time_et = None
        if mt:
            hh = int(mt.group(1)) % 12
            if mt.group(3) == "p":
                hh += 12
            time_et = dt.time(hh, int(mt.group(2)))
        rows.append({"date": d, "time_et": time_et, "statement_file": base})
    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)


def load_cot_6a() -> pd.DataFrame:
    """CFTC legacy futures-only CoT for 6A (AUSTRALIAN DOLLAR - CME, mapping
    verified by the acquisition lane). observation_period = Tuesday as-of;
    released Friday 15:30 ET; as_published_no_revision."""
    df = pd.read_parquet(f"{NONPRICE}/normalized/cftc_legacy_tidy.parquet")
    a = df[df["series_id"] == "COT_LEGACY_6A"].copy()
    a["obs_date"] = pd.to_datetime(a["observation_period"])
    a["net_noncomm"] = a["noncomm_long"] - a["noncomm_short"]
    a["net_comm"] = a["comm_long"] - a["comm_short"]
    return a.sort_values("obs_date").reset_index(drop=True)


def load_statistics_6a() -> pd.DataFrame:
    """GLBX statistics for 6A outrights (2023-10+). stat_type 3 settlement,
    6 cleared volume, 9 open interest (OI 2023+ only)."""
    files = sorted(glob.glob(f"{DATA_ROOT}/parquet/AV1T-statistics-ALL10/*.parquet"))
    dfs = []
    for f in files:
        d = pd.read_parquet(f, columns=["instrument_id", "raw_symbol", "ts_event",
                                        "ts_ref", "stat_type", "price", "quantity"])
        d = d[d["raw_symbol"].str.fullmatch(r"6A[FGHJKMNQUVXZ]\d")]
        dfs.append(d)
    df = pd.concat(dfs, ignore_index=True)
    df["dt"] = pd.to_datetime(df["ts_event"], unit="ns", utc=True)
    df["ref_date"] = pd.to_datetime(df["ts_ref"], unit="ns", utc=True).dt.date
    return df


def load_definitions_6a() -> pd.DataFrame:
    files = sorted(glob.glob(f"{DATA_ROOT}/parquet/AV1T-definition-ALL10/*.parquet"))
    dfs = []
    for f in files:
        d = pd.read_parquet(f, columns=["instrument_id", "raw_symbol", "ts_event",
                                        "activation", "expiration",
                                        "maturity_year", "maturity_month"])
        d = d[d["raw_symbol"].str.fullmatch(r"6A[FGHJKMNQUVXZ]\d")]
        dfs.append(d)
    df = pd.concat(dfs, ignore_index=True)
    df["dt"] = pd.to_datetime(df["ts_event"], unit="ns", utc=True)
    return df


# ----------------------------------------------------------------------------
# IO helpers
# ----------------------------------------------------------------------------

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
    with open(path, "w") as fh:
        json.dump(_san(obj), fh, indent=1, allow_nan=False)


def px(x):
    """fixed point -> USD/AUD float"""
    return float(x) / PRICE_SCALE


if __name__ == "__main__":
    print("library module — run 6A_build_cache.py first")
