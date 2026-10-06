"""6B deep-research v2 shared library — lane DEEP-6B, task FUTURES-DEEPRESEARCH-V2-20261003.

Loads the Databento av1trim 6B ohlcv-1m outright panel (2020-01-01..2026-09-30,
= FX-BACKFILL2 2020-22 + AV1R-BACKFILL 2022-26.04 + AV1T 2026.04-10), the GLBX
statistics (2023-10+), definitions (2023-10+), CFTC legacy CoT for POUND
STERLING (series COT_LEGACY_6B, as-published), BoE Bank Rate decisions, FRED
latest policy-rate series, FOMC statement archive, and BoE gilt nominal
daily-curve XLSX (parsed via raw XML; DECLARED_LAG caveat applies).

Laws honored:
  * No PnL evaluation, no signal selection; descriptive only. No conditional
    mean-return tables (those would be PnL-linked selection = NOT_RUN).
  * No vendor-stitched continuous series: held-contract series are built here
    from per-contract bars with explicit, declared, PIT-legal selection rules.
  * Session/segment logic is DST-correct (America/Chicago + Europe/London +
    Asia/Tokyo via zoneinfo); city-clock bands are computed by tz_convert.
  * Thresholds are strict-past/rolling; ex-post labels descriptive only.
"""
from __future__ import annotations

import datetime as dt
import glob
import io
import json
import os
import re
import zipfile
from xml.etree import ElementTree

import numpy as np
import pandas as pd

# NOTE: dispatch names ~/.my-quantitative-data/futures-databento-av1trim/ but the
# delivered dataset physically lives at the sibling non-dot path (both verified
# 2026-10-02); nonprice lives at the dot path. Both recorded in the dossier.
DATA_ROOT = "/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim"
NONPRICE = os.path.expanduser(
    "/Users/hoangminhlong/.my-quantitative-data/futures-nonprice-10syms")
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "6B_cache")

CHI = "America/Chicago"      # exchange tz
LON = "Europe/London"        # BoE MPC release clock (12:00 convention, verified
                             # empirically below as volume-spike minute)
TOK = "Asia/Tokyo"           # Asia session clock
NS = 1_000_000_000
PX_SCALE = 1e9               # Databento fixed-9 prices -> 1.32 == 1320000000

MONTH_CODE = {"H": 3, "M": 6, "U": 9, "Z": 12}
CODE_MONTH = {3: "H", 6: "M", 9: "U", 12: "Z"}

# Session boundaries in exchange-local (CT) clock. Trade date D runs from the
# 17:00 CT open on D-1 to the 16:00 CT close on D; maintenance break
# 16:00-17:00 CT daily (measured; constant across 2020-2026 — verified by
# 6B_build_cache minute-of-day histogram).
SESSION_OPEN_MIN = 17 * 60   # CT, on D-1
SESSION_CLOSE_MIN = 16 * 60  # CT, on D

# City-clock segments (DST-correct via tz_convert):
#   asia_core      09:00-15:00 Tokyo   (Tokyo banking day core)
#   asia_early     00:00-09:00 Tokyo   (late US -> Tokyo open)
#   lon_pre_boe    08:00-12:00 London  (London morning; ONS 07:00 just before)
#   boe_release    12:00-12:30 London  (MPC 12:00 convention window)
#   lon_us_overlap 12:00-16:30 London  (London afternoon + US data window)
#   us_rth         08:30-15:00 Chicago (US cash-synchronous window)
#   us_close       15:00-17:00 Chicago (close approach + maintenance at 16:00)
CITY_SEGMENTS = [
    ("asia_early", TOK, 0, 9 * 60),
    ("asia_core", TOK, 9 * 60, 15 * 60),
    ("lon_pre_boe", LON, 8 * 60, 12 * 60),
    ("boe_release", LON, 12 * 60, 12 * 60 + 30),
    ("lon_us_overlap", LON, 12 * 60, 16 * 60 + 30),
    ("us_rth", CHI, 8 * 60 + 30, 15 * 60),
    ("us_close", CHI, 15 * 60, 17 * 60),
]


# ----------------------------------------------------------------------------
# Contract registry
# ----------------------------------------------------------------------------

def third_wednesday(year: int, month: int) -> dt.date:
    d = dt.date(year, month, 1)
    offset = (2 - d.weekday()) % 7  # Wednesday == 2
    first_wed = d + dt.timedelta(days=offset)
    return first_wed + dt.timedelta(days=14)


def approx_ltd(year: int, month: int) -> dt.date:
    """Approximate last-trade date: 2 Mon-Fri business days before the third
    Wednesday, at 09:16 CT (v1 §1). Monday-holiday drift up to -3 calendar days
    (MLK/Presidents Day cases measured in v1); registry windows tolerate slop."""
    d = third_wednesday(year, month)
    n = 0
    while n < 2:
        d -= dt.timedelta(days=1)
        if d.weekday() < 5:
            n += 1
    return d


def build_contract_registry(df: pd.DataFrame) -> pd.DataFrame:
    """One row per (symbol cluster) contract: symbol, expiry, first/last bar.

    One-digit-year CME symbols are decade-ambiguous (6BH0 = Mar 2010 or Mar
    2020); clusters are split on >45-day gaps and matched to the expiry year
    whose [approx_ltd - 1100d, approx_ltd + 12d] window contains the cluster.
    Non-6B symbols and unmatched clusters become QA strays (excluded from
    analysis, recorded in the quality ledger).
    """
    rows = []
    for sym, idx in df.groupby("raw_symbol", sort=False).groups.items():
        m = re.fullmatch(r"6B([HMUZ])(\d)", sym)
        sub = df.loc[idx]
        ts = sub["dt"].sort_values().reset_index(drop=True)
        cluster_id = (ts.diff() > pd.Timedelta(days=45)).cumsum()
        sub = sub.assign(_cluster=cluster_id.values)
        for cid, grp in sub.groupby("_cluster"):
            t0, t1 = grp["dt"].min(), grp["dt"].max()
            stray = True
            stray_reason = None
            expiry = None
            year = None
            if m is None:
                stray_reason = ("serial_or_foreign_symbol"
                                if re.fullmatch(r"6B[F G J K N Q V X]\d", sym)
                                else "non_6B_symbol")
            else:
                code, digit = m.group(1), int(m.group(2))
                cands = [approx_ltd(y, MONTH_CODE[code])
                         for y in range(2019, 2029) if y % 10 == digit]
                ok = [c for c in cands
                      if (pd.Timestamp(c) - pd.Timedelta(days=1100)).tz_localize("UTC") <= t0
                      and t1 <= (pd.Timestamp(c) + pd.Timedelta(days=12)).tz_localize("UTC")]
                if len(ok) == 1:
                    expiry = ok[0].isoformat()
                    year = ok[0].year
                    stray = False
                else:
                    stray_reason = "quarterly_no_expiry_match"
            rows.append({
                "symbol": sym, "cluster": int(cid),
                "expiry": expiry, "year": year,
                "month": MONTH_CODE[m.group(1)] if m else None,
                "quarterly": bool(m),
                "first_bar": t0, "last_bar": t1, "n_bars": len(grp),
                "volume": int(grp["volume"].sum()),
                "instrument_ids": sorted(grp["instrument_id"].unique().tolist()),
                "stray": stray, "stray_reason": stray_reason,
            })
    reg = pd.DataFrame(rows).sort_values(
        ["stray", "expiry"], na_position="last").reset_index(drop=True)

    def _key(r):
        if r["stray"] or not r["quarterly"]:
            return f"STRAY_{r['symbol']}_{r['cluster']}"
        return f"{r['symbol']}_{int(r['year'])}"

    reg["contract"] = reg.apply(_key, axis=1)
    return reg


# ----------------------------------------------------------------------------
# Panel loading + annotation
# ----------------------------------------------------------------------------

def _panel_files():
    return (sorted(glob.glob(f"{DATA_ROOT}/parquet/AV1B-O1M-6B-BACKFILL2/*.parquet"))
            + sorted(glob.glob(f"{DATA_ROOT}/parquet/AV1R-O1M-6B-BACKFILL/*.parquet"))
            + sorted(glob.glob(f"{DATA_ROOT}/parquet/AV1T-O1M-6B/*.parquet")))


def load_outright_1m() -> pd.DataFrame:
    """Full 6B outright ohlcv-1m panel (cached). Spread instruments (symbol
    contains '-') are excluded here and counted separately by the QA script."""
    cache = os.path.join(CACHE, "6b_outright_1m.parquet")
    if os.path.exists(cache):
        return pd.read_parquet(cache)
    dfs = []
    for f in _panel_files():
        d = pd.read_parquet(f)
        dfs.append(d[~d["raw_symbol"].str.contains("-")])
    df = pd.concat(dfs, ignore_index=True).sort_values("ts_event").reset_index(drop=True)
    df["dt"] = pd.to_datetime(df["ts_event"], unit="ns", utc=True)
    os.makedirs(CACHE, exist_ok=True)
    df.to_parquet(cache, index=False)
    return df


def annotate_panel(df: pd.DataFrame, reg: pd.DataFrame) -> pd.DataFrame:
    """Add session date, minute-of-day (CT), city-clock segment, contract key."""
    local = df["dt"].dt.tz_convert(CHI)
    hhmm = local.dt.hour * 60 + local.dt.minute
    sess_date = local.dt.normalize()
    nxt = local.dt.hour >= 17
    # wall-clock +1 calendar day (DST-correct: Day offset, not 24h timedelta)
    sess_date.loc[nxt] = sess_date.loc[nxt] + pd.offsets.Day(1)
    df["session_date"] = sess_date.dt.tz_localize(None).dt.date
    df["minute_ct"] = hhmm
    df["in_break"] = (hhmm >= 16 * 60) & (hhmm < 17 * 60)
    dow = local.dt.dayofweek
    df["weekend_anomaly"] = ((dow == 4) & (hhmm >= 17 * 60)) | (dow == 5)

    # city-clock segments (DST-correct): a minute can belong to one city band;
    # order of assignment = GBP-relevance priority used everywhere below.
    seg = pd.Series("other", index=df.index, dtype="object")
    for name, tzname, a, b in CITY_SEGMENTS:
        cloc = df["dt"].dt.tz_convert(tzname)
        chm = cloc.dt.hour * 60 + cloc.dt.minute
        seg[(chm >= a) & (chm < b)] = name
    df["segment"] = seg

    # contract key
    df = df.sort_values(["raw_symbol", "dt"]).reset_index(drop=True)
    brk = df.groupby("raw_symbol")["dt"].diff() > pd.Timedelta(days=45)
    df["_cluster"] = brk.groupby(df["raw_symbol"]).cumsum().fillna(0).astype(int)
    key = df["raw_symbol"] + "|" + df["_cluster"].astype(str)
    regmap = reg[["symbol", "cluster", "contract"]]
    regkey = regmap["symbol"] + "|" + regmap["cluster"].astype(str)
    lut = pd.Series(regmap["contract"].values, index=regkey.values)
    df["contract"] = key.map(lut)
    if df["contract"].isna().any():
        raise ValueError("unmapped contract rows")
    df.loc[df["contract"].str.startswith("STRAY"), "contract"] = np.nan
    return df


def build_session_table(df: pd.DataFrame) -> pd.DataFrame:
    """Per (session_date, contract): OHLC from 1m bars, volume, bar counts.

    Session open = first bar's open of the session (17:00 CT region); close =
    last bar's close (< 16:00 CT); high/low over all bars. Real-volume only by
    construction (Databento ohlcv prints no settlement bars; zero-volume
    minute bars exist and are kept — flagged in QA).
    """
    d = df[df["contract"].notna()]
    g = d.groupby(["session_date", "contract"], sort=True)
    out = g.agg(
        open=("open", "first"), high=("high", "max"), low=("low", "min"),
        close=("close", "last"), volume=("volume", "sum"),
        n_bars=("volume", "size"), n_v0=("volume", lambda s: int((s == 0).sum())),
        first_dt=("dt", "min"), last_dt=("dt", "max"),
    ).reset_index()
    for c in ("open", "high", "low", "close"):
        out[c] = out[c] / PX_SCALE
    return out


# ----------------------------------------------------------------------------
# PIT held-contract selection (no vendor stitching, ever)
# ----------------------------------------------------------------------------

_QRE = re.compile(r"^6B[HMUZ]\d_\d{4}$")


def next_quarter(contract: str) -> str:
    sym, yr = contract.split("_")
    m, y = MONTH_CODE[sym[2]], int(yr)
    nm, ny = (m + 3, y) if m < 12 else (3, y + 1)
    return f"6B{CODE_MONTH[nm]}{ny % 10}_{ny}"


def quarterly_contracts(sess: pd.DataFrame) -> list:
    return sorted([c for c in sess["contract"].unique() if _QRE.match(c)])


def front_by_calendar(sess: pd.DataFrame, reg: pd.DataFrame) -> pd.DataFrame:
    """v1 declared rule: hold until the last session BEFORE day-1 of the held
    contract's delivery month; roll to next HMUZ at that close (PIT-legal)."""
    lut = reg[~reg["stray"]].set_index("contract")["expiry"].to_dict()
    out = []
    contracts = quarterly_contracts(sess)
    contracts = [c for c in contracts if c in lut]
    contracts.sort(key=lambda c: lut[c])
    for i, c in enumerate(contracts[:-1]):
        exp = pd.Timestamp(lut[c])
        win = sess[(sess["contract"] == c)
                   & (pd.to_datetime(sess["session_date"]) < exp.replace(day=1))]
        if i > 0:
            prev_exp = pd.Timestamp(lut[contracts[i - 1]])
            win = win[pd.to_datetime(win["session_date"]) >= prev_exp.replace(day=1)]
        if len(win):
            out.append(win[["session_date", "contract"]].rename(
                columns={"contract": "held"}))
    held = pd.concat(out).sort_values("session_date")
    return held.groupby("session_date")["held"].last().reset_index()


def front_by_volume_crossover(sess: pd.DataFrame, k: int = 5) -> pd.DataFrame:
    """PIT volume-triggered rule: switch old->next quarterly at the first
    session-close where the NEXT quarterly's trailing-k-session mean volume
    exceeds the held contract's (decision at close of t; next held from t+1)."""
    d = sess[sess["contract"].str.match(_QRE, na=False)]
    wide = d.pivot_table(index="session_date", columns="contract",
                         values="volume", aggfunc="sum").sort_index()
    roll = wide.rolling(k, min_periods=1).mean()
    state, held_contracts = None, []
    for date in wide.index:
        row = roll.loc[date].dropna()
        row = row[row > 0]
        if state is None:
            state = row.idxmax()
        else:
            nxt = next_quarter(state)
            if nxt in row.index:
                cur_v = row.get(state, np.nan)
                if pd.isna(cur_v) or row[nxt] > cur_v:
                    state = nxt
        held_contracts.append(state)
    return pd.DataFrame({"session_date": wide.index, "held": held_contracts})


def held_series(sess: pd.DataFrame, held: pd.DataFrame) -> pd.DataFrame:
    """Daily OHLCV of the held contract (stitched at declared roll closes; no
    back-adjustment; raw roll gaps recorded separately)."""
    m = sess.merge(held, on="session_date")
    m = m[m["contract"] == m["held"]].copy()
    m["ret"] = m["close"].pct_change()
    m.loc[m["held"] != m["held"].shift(), "ret"] = np.nan  # roll boundary
    return m.reset_index(drop=True)


# ----------------------------------------------------------------------------
# Non-price loaders
# ----------------------------------------------------------------------------

def load_boe_bank_rate() -> pd.DataFrame:
    """Official Bank Rate change dates 2000-2025-12-18 (official_history_latest
    vintage; provenance sha in parquet). These are MPC announcement dates that
    CHANGED the rate; scheduled hold dates come from the MPC calendar."""
    df = pd.read_parquet(f"{NONPRICE}/normalized/boe_bank_rate_tidy.parquet")
    df["obs"] = pd.to_datetime(df["observation_date"])
    return df.sort_values("obs").reset_index(drop=True)


def load_mpc_calendar() -> pd.DataFrame:
    """BoE MPC announcement dates 2020-01-30..2026-09-17 (+2026-11/12), assembled
    from bankofengland.co.uk 'MPC dates for YYYY' news pages + upcoming-mpc-dates
    + emergency 2020 meetings, fetched 2026-10-02 (lane web session); rate-change
    subset cross-checked == load_boe_bank_rate(). 12:00 London convention is
    verified EMPIRICALLY by 6B_a4_events.py volume-spike minute."""
    sched = {
        2020: ["2020-01-30", "2020-03-11", "2020-03-19", "2020-03-26", "2020-05-07",
               "2020-06-18", "2020-08-06", "2020-09-17", "2020-11-05", "2020-12-17"],
        2021: ["2021-02-04", "2021-03-18", "2021-05-06", "2021-06-24", "2021-08-05",
               "2021-09-23", "2021-11-04", "2021-12-16"],
        2022: ["2022-02-03", "2022-03-17", "2022-05-05", "2022-06-16", "2022-08-04",
               "2022-09-22", "2022-11-03", "2022-12-15"],
        2023: ["2023-02-02", "2023-03-23", "2023-05-11", "2023-06-22", "2023-08-03",
               "2023-09-21", "2023-11-02", "2023-12-14"],
        2024: ["2024-02-01", "2024-03-21", "2024-05-09", "2024-06-20", "2024-08-01",
               "2024-09-19", "2024-11-07", "2024-12-19"],
        2025: ["2025-02-06", "2025-03-20", "2025-05-08", "2025-06-19", "2025-08-07",
               "2025-09-18", "2025-11-06", "2025-12-18"],
        2026: ["2026-02-05", "2026-03-19", "2026-04-30", "2026-06-18", "2026-07-30",
               "2026-09-17", "2026-11-05", "2026-12-17"],
    }
    # flags: 2020-03-11 moved meeting (Budget day), 2020-03-19 emergency,
    # 2020-03-26 originally scheduled March decision (brought forward; kept for
    # completeness, flagged), rate-change rows marked from the official table.
    changes = set(load_boe_bank_rate()["obs"].dt.strftime("%Y-%m-%d"))
    rows = []
    for y, ds in sched.items():
        for s in ds:
            rows.append({"date": pd.Timestamp(s), "changed_rate": s in changes})
    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)


def load_fomc() -> pd.DataFrame:
    """FOMC statement events from archived federalreserve.gov HTML (incl.
    intermeeting 2020 moves). release_time_et set only where the statement
    itself carries 'For release at H:MM a.m./p.m. E[SD]T'."""
    files = sorted(glob.glob(f"{NONPRICE}/fed/statements/monetary*.html"))
    rows = []
    for f in files:
        base = os.path.basename(f)
        m = re.fullmatch(r"monetary(\d{8})a\.html", base)
        if not m:
            continue
        txt = open(f, encoding="utf-8", errors="replace").read()
        mt = re.search(
            r"For release at\s*(\d{1,2}):(\d{2})\s*([ap])\.m\.\s*(E[SD]T)", txt)
        time_et = None
        if mt:
            hh = int(mt.group(1)) % 12
            if mt.group(3) == "p":
                hh += 12
            time_et = dt.time(hh, int(mt.group(2)))
        rows.append({"date": pd.Timestamp(m.group(1)), "time_et": time_et,
                     "statement_file": base})
    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)


def load_cot_6b() -> pd.DataFrame:
    """CFTC legacy futures-only CoT, CME POUND STERLING mapped to 6B
    (mapping verified in FUTURES-BEHAVIOR-10SYMS-PREP-20261002
    nonprice_acquisition). obs Tuesday, released Friday 15:30 ET."""
    df = pd.read_parquet(f"{NONPRICE}/normalized/cftc_legacy_tidy.parquet")
    g = df[df["series_id"] == "COT_LEGACY_6B"].copy()
    g["obs"] = pd.to_datetime(g["observation_period"])
    g["net_noncomm"] = g["noncomm_long"] - g["noncomm_short"]
    g["net_comm"] = g["comm_long"] - g["comm_short"]
    return g.sort_values("obs").reset_index(drop=True)


def load_fred_latest(series: str) -> pd.DataFrame:
    df = pd.read_parquet(f"{NONPRICE}/normalized/fred_latest_tidy.parquet")
    s = df[df["series_id"] == series].copy()
    s["obs"] = pd.to_datetime(s["observation_period"])
    return s.sort_values("obs").reset_index(drop=True)


def load_statistics_6b() -> pd.DataFrame:
    """GLBX statistics for 6B outrights (2023-10+): stat_type 3 settlement,
    6 cleared volume, 9 open interest (forward-looking fields unused)."""
    files = sorted(glob.glob(
        f"{DATA_ROOT}/parquet/AV1T-statistics-ALL10/*.parquet"))
    dfs = []
    for f in files:
        d = pd.read_parquet(f)
        d = d[d["raw_symbol"].str.startswith("6B")
              & ~d["raw_symbol"].str.contains("-")]
        dfs.append(d)
    df = pd.concat(dfs, ignore_index=True)
    df["dt"] = pd.to_datetime(df["ts_event"], unit="ns", utc=True)
    df["ref_date"] = pd.to_datetime(df["ts_ref"], unit="ns", utc=True).dt.date
    return df


def load_definitions_6b() -> pd.DataFrame:
    files = sorted(glob.glob(
        f"{DATA_ROOT}/parquet/AV1T-definition-ALL10/*.parquet"))
    dfs = []
    for f in files:
        d = pd.read_parquet(f)
        d = d[d["raw_symbol"].str.fullmatch(r"6B[HMUZ]\d")]
        dfs.append(d)
    df = pd.concat(dfs, ignore_index=True)
    df["dt"] = pd.to_datetime(df["ts_event"], unit="ns", utc=True)
    return df


# ----------------------------------------------------------------------------
# Gilt nominal daily curve (BoE GLC xlsx, DECLARED_LAG caveat)
# ----------------------------------------------------------------------------

def _xlsx_sheet_rows(zf: zipfile.ZipFile, name: str):
    """Minimal xlsx reader: first worksheet, rows of cell values (str)."""
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    try:
        wb = ElementTree.fromstring(zf.read("xl/workbook.xml"))
        rels = ElementTree.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    except KeyError:
        return None
    rid_map = {}
    for rel in rels:
        rid_map[rel.get("Id")] = rel.get("Target")
    sheets = wb.findall(".//m:sheet", ns)
    for sh in sheets:
        rid = sh.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
        target = rid_map.get(rid)
        if target is None:
            continue
        path = "xl/" + target.lstrip("/") if not target.startswith("xl/") else target
        try:
            ws = ElementTree.fromstring(zf.read(path))
        except KeyError:
            continue
        sst = []
        if "xl/sharedStrings.xml" in zf.namelist():
            ss = ElementTree.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in ss.findall("m:si", ns):
                sst.append("".join(t.text or "" for t in si.findall(".//m:t", ns)))
        for row in ws.findall(".//m:row", ns):
            vals = []
            for c in row.findall("m:c", ns):
                v = c.find("m:v", ns)
                if v is None:
                    vals.append(None)
                    continue
                if c.get("t") == "s":
                    vals.append(sst[int(v.text)])
                else:
                    vals.append(v.text)
            yield sh.get("name"), vals


def load_gilt_curve() -> pd.DataFrame:
    """BoE nominal government liability curve, daily, sheet '4. spot curve'.
    Parsed from glcnominalddata.zip 'GLC Nominal daily data_2016 to 2024.xlsx'
    (file updated 2025-01-21 -> coverage ends 2024). Dates are Excel serials;
    tenors in years (0.5..40); yields in percent. DECLARED_LAG: BoE publishes
    curve data with a declared lag; treat as PIT-known only >=1 business day
    after the observation date."""
    out_cache = os.path.join(CACHE, "gilt_curve.parquet")
    if os.path.exists(out_cache):
        return pd.read_parquet(out_cache)
    outer = zipfile.ZipFile(f"{NONPRICE}/boe/glcnominalddata.zip")
    target = [n for n in outer.namelist() if "2016 to 2024" in n][0]
    inner = zipfile.ZipFile(io.BytesIO(outer.read(target)))
    rows = []
    tenors = None
    for shname, vals in _xlsx_sheet_rows(inner, target):
        if shname != "4. spot curve":
            continue
        if vals and str(vals[0]).strip().lower().startswith("years:"):
            tenors = []
            for v in vals[1:]:
                try:
                    tenors.append(float(v))
                except (TypeError, ValueError):
                    tenors.append(None)
            continue
        if not tenors or not vals or vals[0] is None:
            continue
        try:
            serial = float(vals[0])
            d = (dt.datetime(1899, 12, 30) + dt.timedelta(days=serial)).date()
        except (TypeError, ValueError):
            continue
        for t, v in zip(tenors, vals[1:]):
            if t is None or v is None:
                continue
            try:
                rows.append({"date": d, "tenor": t, "yield": float(v)})
            except ValueError:
                continue
    out = pd.DataFrame(rows)
    if not len(out):
        raise RuntimeError("gilt curve parse produced 0 rows")
    os.makedirs(CACHE, exist_ok=True)
    out.to_parquet(out_cache, index=False)
    return out


# ----------------------------------------------------------------------------
# JSON helpers
# ----------------------------------------------------------------------------

def _san(o):
    if isinstance(o, dict):
        return {str(k): _san(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_san(v) for v in o]
    if isinstance(o, (float, np.floating)):
        return float(o) if np.isfinite(o) else None
    if isinstance(o, np.integer):
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


if __name__ == "__main__":
    print("library module — run 6B_build_cache.py first")
